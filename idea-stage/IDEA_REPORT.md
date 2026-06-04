# Research Idea Report: Question-Aware Executable Table Curation

**Direction**: 基于 Table-Critic (ACL 2025)，训练小模型预测 question-conditioned 的可执行表格结构变换操作序列，替代/增强现有规则预处理
**Generated**: 2026-05-26
**Ideas evaluated**: 6 generated → 4 survived filtering → 0 piloted (需先完成 Step 0) → 3 recommended
**Status**: 待 Step 0 (Hints-to-Stage1) 验证

---

## Executive Summary

Table-Critic 的 Refine 阶段（Stage 2）对 WikiTQ 仅带来 +2.97% 提升（81.98%→84.95%），成本高昂（3~6 次 LLM 调用/样本 × 2 轮迭代）。现有 Stage 0/0.5 的规则预处理（Flatten + TableAnalyzer）生成 hints 但仅在 Refine 消费。本报告提出 3 个互补的研究想法，核心假设是：**如果能以低成本（小模型 + DSL 执行器）将表格预处理到"推理就绪"状态，可以减少对昂贵 Refine 的依赖**。

**关键前提**：所有想法都依赖 Step 0 (Hints-to-Stage1 pilot) 的结果。如果现有 hints 注入 Stage 1 不能提升 ≥1%，整个方向需要重新评估。

---

## Literature Landscape

### 核心竞品

| 论文 | 会议 | 核心方法 | 与我们的关系 |
|------|------|----------|-------------|
| **AutoPrep** (Pan et al.) | VLDB 2025 | 多 LLM agent 做问题感知数据准备 (Planner→Executor→Answerer) | **最大竞品** — 同样做 question-aware prep，但用昂贵多 LLM，我们用小模型 DSL |
| **NormTab** (Nahid & Rafiei) | EMNLP 2024 Findings | LLM 直接做 web 表格归一化 | 证明归一化有用；我们用小模型替代 LLM |
| **Chain-of-Table** (Wang et al.) | ICLR 2024 | 6 种表格操作链式推理 | **直接基础** — DSL 设计借鉴其操作集，但用于推理前而非推理中 |
| **TART** (Lu, Pan et al.) | NAACL 2025 Findings | Table Formatter + Tool Maker + Explanation Generator | 相邻工作，关注线性化表示而非结构变换 |

### 关键结构缺口

1. **效率缺口**: AutoPrep 证明 question-aware prep 有效，但依赖多 LLM agent → 高成本。无人探索用小模型替代。
2. **操作序列预测缺口**: Chain-of-Table 的操作用于推理中，无人将其适配为推理前预处理操作。
3. **下游 reward 对齐缺口**: 现有预处理方法（NormTab, AutoPrep）的标签来自 LLM 自生成或通用标准，无人用下游 QA 准确率作为训练信号。
4. **管线集成缺口**: 现有预处理方法是独立系统，无人将其集成到多阶段推理管线（Thought→Refine）中作为成本-效果权衡。

---

## Ranked Ideas

### 🏆 Idea 1: OpCurator — 面向表格推理的可执行操作序列预测器 [RECOMMENDED — Step 0 验证后推进]

**一句话总结**: 训练 SLM (3B class + LoRA) 预测 question-conditioned 的表格结构变换操作序列，由确定性 Python 引擎执行，使 Stage 1 直接达到接近 full pipeline 的准确率。

**核心假设**:
> 表格推理中的大量错误源于"表格结构不适合推理"而非"推理能力不足"。如果一个小模型能根据问题预测出正确的结构变换操作（表头拆分、值归一化、类型标注、列选择等），并由确定性引擎执行，那么 Stage 1 就能一次做对，减少对昂贵 Refine 的依赖。

**方法设计**:

```
Phase 0: 标签构造（最大挑战）
  对每个 (table, question, correct_answer) 三元组:
  ├── 用 GPT-5.4 生成候选操作序列
  ├── 确定性执行器执行每个序列
  ├── 在 Stage 1 上测试每个变换后的表格
  └── 选择下游准确率最高的序列作为 gold label

Phase 1: 模型训练
  ├── 输入: [table_schema, table_preview, question]
  ├── 输出: 操作序列 JSON: [
  │     {"op": "split_header", "args": {"col": 0, "delimiter": "/"}},
  │     {"op": "normalize_values", "args": {"col": 2, "type": "numeric"}},
  │     {"op": "annotate_type", "args": {"col": 3, "type": "date"}}
  │   ]
  └── 训练: LoRA fine-tune on 操作序列 (seq2seq)

Phase 2: 推理时执行
  SLM 预测操作序列 → Python 引擎确定性执行 → 变换后表格 → Stage 1
```

**DSL 定义** (6 种操作):
| 操作 | 功能 | 参数 | 示例 |
|------|------|------|------|
| `split_header` | 复合表头拆分 | col, delimiter | `"Population/Million"` → `"Population"` |
| `normalize_values` | 值格式标准化 | col, type | `"$1,234"` → `"1234"` |
| `parse_numeric` | 数值解析与对齐 | col | `"1.2K"` → `"1200"` |
| `standardize_date` | 日期格式统一 | col, format | `"Jan 5"` → `"2024-01-05"` |
| `annotate_type` | 列类型标注 | col, type | 标注 "percentage", "currency" |
| `select_columns` | 列选择/重排 | cols | 仅保留问题相关列 |

**最小可行实验**:
1. **Step 0 (已有计划)**: Hints-to-Stage1 pilot — 注入现有 table_analysis hints 到 Stage 1，验证 ≥1% 提升
2. **Step 1**: Oracle ceiling — 对 200 个 WikiTQ bad cases 标注可被预处理修复的错误比例
3. **Step 2 (如果 Step 0/1 通过)**: 训练操作序列预测器，100 样本 pilot
4. **Step 3 (如果 Step 2 通过)**: 全量验证 + cost 分析

**预期结果**:
- WikiTQ Stage 1: 81.98% → 83~84% (接近 full pipeline 84.95%)
- TabFact Stage 1: 93.63% → 94.5~95%
- 成本: SLM 推理 ~0.01$/样本 vs Refine ~0.30$/样本 (30x 便宜)
- 如果 hints 也注入 Refine: full pipeline 可能 >85%

**新颖性**: 7/10
- 最接近工作: AutoPrep (VLDB 2025) — 但 AutoPrep 用多 LLM agent，我们用单 SLM + 确定性执行
- 另一个相关: Chain-of-Table (ICLR 2024) — 但 CoT 的操作是推理本身，我们的是推理前预处理
- **核心差异**: 首个将操作序列预测用于表格推理前预处理的工作，用下游 reward 构造标签

**可行性**: 6/10 (受限于标签构造)
- SLM + LoRA 训练: 2-3 天 (技术成熟)
- DSL 执行器: 1-2 天 (简单 Python)
- 标签构造: **最大瓶颈** (需要 GPT + 下游验证循环)
- 实验运行: 2-3 天

**风险**: MEDIUM-HIGH
- 标签构造可能效果不好（无 ground truth）
- Oracle ceiling 可能 < +2%（预处理无法修复大部分错误）
- 与 AutoPrep 新颖性重叠风险

**贡献类型**: 新方法 + 效率优化 + 实证发现

**审稿人可能的反对意见**:
> "这只是 AutoPrep 的便宜版本，novelty 不足。"

**回应**:
1. 我们首次引入**下游 reward 对齐**的标签构造 — 不是 GPT 蒸馏，而是以 Stage 1 准确率为目标优化操作序列
2. 我们提供**确定性执行保证** — AutoPrep 的 executor 是 LLM 驱动的（不可复现），我们是 Python 引擎（可解释、可消融）
3. 我们证明**小模型可以替代多 LLM** — 这在 AI 效率研究的叙事中很有力
4. 管线集成视角 — 我们不是独立系统，而是多阶段推理管线的预处理增强

**为什么应该做这个**:
1. 如果成功，提供了一种**低成本替代/增强 Refine** 的方案
2. 操作 DSL 设计 + 确定性执行器是**可复用的基础设施**
3. 下游 reward 对齐的标签构造方法有**独立贡献价值**
4. 笨蛋已有的 TableAnalyzer 和 hints 机制提供了**天然起点**

---

### 🥈 Idea 2: HintBoost — 基于现有 TableAnalyzer 的 Stage 1 前置增强 [SAFEST OPTION]

**一句话总结**: 不训练新模型，而是将现有 table_analysis hints（零 LLM 成本的 TableAnalyzer 输出）前置注入 Stage 1 的 6 种操作中，以零训练成本验证"预处理增强 Stage 1"假设。

**核心假设**:
> 现有 TableAnalyzer 已能生成高质量的表格结构分析（表头树、列归一化建议、答案格式 hint），但这些信息仅在 Stage 2 Refine 消费。如果将其前置到 Stage 1，Stage 1 就能在推理时利用这些信息，减少对 Refine 的需求。

**方法设计**:
```
Stage 0: Flatten (已有)
Stage 0.5: TableAnalyzer (已有, 零 LLM 成本)
  → 产出: sample["table_analysis"] = {
      column_normalizations: [...],
      format_normalizations: [...],
      answer_format_hint: "...",
      header_tree: {...}
    }

Stage 1: Thought (修改后)
  ├── select_row: 注入 column_normalizations → 更精准的行选择
  ├── sort_by: 注入 format_normalizations → 正确识别排序方向
  ├── final_query: 注入 answer_format_hint → 答案格式对齐
  └── 其他操作: 透传 table_analysis 供 LLM 参考
```

**与已有计划的关系**: 这正是 `EXPERIMENT_PLAN_HINTS.md` 中的 Step 0！已设计但未执行。

**最小可行实验**: 修改 8 个文件（QA 4 + FV 4），在 WikiTQ 100 样本上验证。
- 已有计划: `refine-logs/EXPERIMENT_PLAN_HINTS.md`
- 预计实现时间: 2-3h
- 预计实验时间: ~15 min (100 samples)

**预期结果**:
- WikiTQ 100: hints + Stage 1 > no hints + Stage 1
- 如果 delta ≥ 1%: 验证假设，为 Idea 1 提供基础
- 如果 delta < 1%: Idea 1 的前提不成立，需要转向

**新颖性**: 3/10 (如果是独立论文)
- 但作为 Idea 1 的**前置验证步骤**，价值很高
- 可作为论文中的 **Ablation / Preliminary Study**

**可行性**: 9/10
- 代码修改已在 EXPERIMENT_PLAN_HINTS.md 中详细规划
- 8 个文件修改，参考实现在 Stage 2 中已有
- pytest 可快速验证正确性

**风险**: LOW
- 最坏情况: hints 无效 → 2-3h 的工作浪费，但获得重要负结果

**贡献类型**: 实证发现 (作为论文的 ablation study)

**审稿人可能的反对意见**:
> "这只是把已有的 hints 从 Refine 移到 Stage 1，没有新东西。"

**回应**: 正确，这不是独立贡献，而是 Idea 1 的**必要前置**。只有当 hints 在 Stage 1 有效时，训练小模型生成更好 hints 才有意义。

**为什么应该做这个**:
1. **零训练成本** — 只需修改代码
2. **快速验证** — 2-3h 实现 + 15min 实验
3. **Gate 决策** — 如果无效，节省训练 SLM 的全部时间
4. **论文基础** — 作为 ablation study 展示 hints 的价值

---

### 🥉 Idea 3: OracleCuration — 预处理 Oracle Ceiling 分析 [DIAGNOSTIC]

**一句话总结**: 系统分析 WikiTQ/TabFact Stage 1 bad cases 中有多少错误可以（理论上）被完美表格预处理修复，确定该方向的天花板。

**核心假设**:
> 不是所有 Stage 1 错误都能被预处理修复。有些错误源于 LLM 推理能力不足（如复杂多步聚合），有些源于问题歧义。只有"结构预处理可修复"的错误才是我们的目标。

**方法设计**:
```
1. 收集 WikiTQ Stage 1 bad cases (约 800 个错误样本)
2. 对每个错误样本，分类错误根因:
   ├── Category A: 表头结构问题 (复合表头未拆分)
   ├── Category B: 值格式问题 (混合格式、不一致)
   ├── Category C: 数值/日期解析问题
   ├── Category D: 列选择问题 (冗余信息干扰)
   ├── Category E: 推理能力不足 (多步聚合、复杂逻辑)
   └── Category F: 问题歧义/无解
3. 对 Category A-D，人工/GPT 标注理想预处理操作
4. 执行理想预处理 → 重新运行 Stage 1
5. 统计: 理论上能修复的比例 = Oracle Ceiling
```

**最小可行实验**:
- 抽样 200 个 WikiTQ bad cases
- GPT-5.4 辅助分类 + 人工审核
- 对 A-D 类执行理想预处理并验证

**预期结果**:
- Oracle ceiling = 可修复错误数 / 总错误数
- 如果 ≥ 60%: 预处理方向非常有价值
- 如果 30-60%: 中等价值，需要结合其他方法
- 如果 < 30%: 预处理方向天花板太低

**新颖性**: 2/10 (诊断工作)
- 但为 Idea 1 提供了**定量的天花板估计**
- 可作为论文的 **Analysis Section**

**可行性**: 8/10
- 需要人工标注或 GPT 辅助分类
- 可以并行执行

**风险**: LOW

**为什么应该做这个**:
1. **定量回答核心问题**: "预处理到底能修多少错误？"
2. **指导 Idea 1 的 DSL 设计**: 哪些操作最常被需要？
3. **论文分析素材**: 错误分类分布是很好的分析表格

---

## Eliminated Ideas

| # | Idea | 排除原因 |
|---|------|----------|
| 4 | **FreeFormCuration**: 训练 SLM 直接生成变换后的表格（非操作序列） | 自由 JSON 生成容易格式错、不可控、难解释、难消融；操作序列更好 |
| 5 | **PrepRefine**: 用预处理替代 Refine（而非补充） | 过于激进；预处理和 Refine 解决不同类型的问题，完全替代风险高 |
| 6 | **UniversalTablePrep**: 通用表格预处理（不限于 table reasoning） | 与 NormTab、AutoPrep 重叠太多，novelty 不足；应聚焦 table reasoning |

---

## Execution Plan: 分阶段验证路径

```
Phase 0: Gate 验证（必须先完成）
├── Step 0a: 实现 Hints-to-Stage1 代码修改 (Idea 2, 2-3h)
│   └── Gate: hints 注入 Stage 1 后 WikiTQ 100 样本准确率是否 > baseline + 1%?
│       ├── YES → 继续 Step 0b
│       └── NO  → 整个方向需要重新评估
│
├── Step 0b: Oracle Ceiling 分析 (Idea 3, 1-2 天)
│   └── Gate: 可修复错误比例是否 ≥ 40%?
│       ├── YES → 继续 Phase 1
│       └── NO  → 预处理方向天花板太低
│
Phase 1: 核心实现（Step 0 Gate 通过后）
├── 设计并实现操作 DSL (1-2 天)
├── 实现确定性执行器 (1 天)
├── 构造训练标签 (GPT + 下游 reward) (3-5 天)
├── LoRA fine-tune SLM (2-3 天)
└── 100 样本 pilot (1 天)

Phase 2: 全量验证
├── WikiTQ full (4344 samples)
├── TabFact full (2024 samples)
├── 多模型测试 (gpt-5.4, qwen3:32b)
└── Cost 分析 (API 调用数, tokens, 延迟)
```

---

## Decision Gates

| Gate | 条件 | 通过 → | 不通过 → |
|------|------|--------|---------|
| **G0: Hints 有效性** | WikiTQ 100 hints+S1 > no hints+S1 ≥ 1% | Oracle 分析 | 重新评估方向 |
| **G1: Oracle 天花板** | 可修复错误 ≥ 40% | 开始 DSL + 训练 | 转向 Refine 增强 |
| **G2: Pilot 信号** | SLM 预测器 100 样本准确率 > baseline | 全量训练 | 调整 DSL / 标签 |
| **G3: 全量验证** | WikiTQ S1+preprocessor ≥ 83.5% | 论文写作 | 改进或组合 Refine |

---

## Suggested Execution Order

```
Week 1 (Gate 验证):
  Day 1: 实现 Hints-to-Stage1 代码修改 (8 files)
  Day 2: 运行 WikiTQ 100 pilot + 分析结果
  Day 3: 如果 G0 通过 → 开始 Oracle Ceiling 分析
  Day 4-5: 完成 Oracle 分析 + 撰写分析报告

Week 2 (如果 Gate 通过):
  Day 1-2: 设计操作 DSL + 实现执行器
  Day 3-5: 构造训练标签 (GPT + 下游验证)
  Day 5: LoRA fine-tune pilot

Week 3 (全量验证):
  Day 1-2: WikiTQ full + TabFact full
  Day 3: Cost 分析 + 多模型测试
  Day 4-5: 消融实验 + 论文初稿
```

---

## Next Steps

- [ ] **Step 0a**: 实现 Hints-to-Stage1 代码修改 (8 files)
  - 参考: `refine-logs/EXPERIMENT_PLAN_HINTS.md`
  - 参考实现: `refine/TableQA/operations/select_row.py:9-17`, `sort_by.py:60-71`, `final_query.py:240-241`
- [ ] **Step 0a 实验**: WikiTQ 100 样本 pilot
- [ ] **Step 0b**: Oracle Ceiling 分析 (200 bad cases)
- [ ] **如果 G0 + G1 通过**: 开始 DSL 设计 + SLM 训练
