# Round 1 Refinement

**Date**: 2026-05-21
**Round**: 1

## Problem Anchor（不变）

**Bottom-line problem**: Table-Critic 的 Refine 阶段对错误样本的修正效率极低（WikiTQ Thought→Refine 仅 +2%），根本原因是 Critic 的诊断信息不充分——(1) Critic 看不到中间表格状态变化，只能基于最终子表推理；(2) Critic 的输出是自由文本，Refiner 需要自行推断修正策略。

**Must-solve bottleneck**: Critic 缺乏足够的诊断信息（中间表格状态）和结构化的诊断输出（错误类型），导致 Refiner 无法针对性地修正不同类型的错误。

## Anchor Check

- **Original bottleneck**: Critic 诊断信息不充分 + Refiner 修正策略不区分错误类型
- **Revised method still addresses it**: 是，但重新分配了贡献权重——信息增强（中间表格注入）是主贡献，错误分类是辅助
- **Reviewer suggestions rejected as drift**: 无（评审没有要求改变问题定义）

## Simplicity Check

- **Dominant contribution after revision**: 信息增强的多智能体错误诊断（中间表格状态注入 Critic + 两阶段诊断）
- **Components removed or merged**: 错误类型四分类简化为与现有 error_route 对齐；类型专用 Refiner 保留但定位为辅助贡献
- **Reviewer suggestions rejected as unnecessary complexity**: 拒绝"对所有步骤注入中间状态"（成本太高），改为两阶段诊断（粗定位 + 精细诊断）

## Changes Made

### 1. 重新定位主贡献 [CRITICAL-1, CRITICAL-2]

**Reviewer said**: "结构化输出 + 路由"在 2026 年已不新颖；中间表格注入有价值但被低估。

**Action**: 将提案的主贡献从"错误类型路由"调整为"信息增强的错误诊断框架"。

**Reasoning**: 中间表格状态注入是唯一真正增加了新信息给 Critic 的改动（当前 Critic 只看到最终子表）。错误类型路由只是利用已有信息的不同分发方式。重新包装后：
- **主贡献**: 通过两阶段诊断（粗定位→精细诊断）和中间表格状态注入，显著增强 Critic 的诊断能力
- **辅助贡献**: 基于错误类型路由到专用 Refiner 模板

### 2. 解决循环依赖 [CRITICAL-3]

**Reviewer said**: suspected_step 来源不明，存在循环依赖。

**Action**: 设计**两阶段诊断流程**：

- **阶段 1（粗定位）**: 现有 Critic 流程不变，Critic 基于最终子表和推理链确定错误步骤（error_step）。输出格式不变：`Conclusion: [Incorrect] Step <NUM>`。
- **阶段 2（精细诊断）**: 用 error_step 从 `get_table_log()` 中提取该步骤前后的中间表格状态，加上 V-Critic 的验证报告（如有），再次调用 Critic 做精细诊断。此时 Critic 输出结构化三元组：`(error_step, error_sub_type, correction_hint)`。

**成本分析**: 阶段 2 只对错误样本触发（~20% 的样本），且只注入 1 个步骤的前后表格（~1000-2000 tokens）。全量 WikiTQ 额外 token：4344 × 20% × 1500 ≈ 1.3M tokens。

**Impact on core method**: 这是整个方案最关键的设计——通过两次 Critic 调用实现"先定位，再分类"，避免了信息泄露和循环依赖。

### 3. 错误分类与错误树对齐 [IMPORTANT-1]

**Reviewer said**: 四分类太粗，且与现有错误树不对齐。

**Action**: 不再使用 ENTITY/NUMERICAL/SORTING/OTHER 四分类，而是**复用现有错误树的 error_route 体系**作为第二阶段诊断的分类框架。

**Reasoning**: 现有 `few_shot_critic.json` 已经有细粒度的错误分类（如 `select_row_errors/condition_error`、`group_by_errors/wrong_aggregation` 等）。阶段 2 的 Critic 在看到中间表格状态后，从错误树中选择最匹配的 error_route 作为诊断结果。这既利用了已有知识（错误树中的 Blueprint），又避免了另起炉灶的分类体系。

**error_route → Refiner 策略映射**：
```
error_route 包含 "select_row/select_column" → ENTITY-REFINE（利用 TableAnalyzer hint）
error_route 包含 "group_by/add_column/sort_column" → NUMERICAL-REFINE（验证计算过程）
error_route 为其他或无法匹配 → STANDARD-REFINE（现有 baseline）
```

### 4. 增加关键消融 [CRITICAL-1]

**Reviewer said**: 缺少"结构化路由 vs enriched prompt"的消融对比。

**Action**: 实验设计中增加三个关键消融配置：

| 配置 | 说明 | 验证什么 |
|------|------|---------|
| A: Baseline | 现有 Table-Critic（自由文本 critique，统一 Refiner） | 基线 |
| B: Enriched Critique | Critic 在自由文本中提到错误类型（但不做路由） | 附加信息本身是否有用 |
| C: Intermediate Tables Only | 注入中间表格但不做错误分类和路由 | 信息增量本身是否有用 |
| D: Full（Two-Stage） | 两阶段诊断 + 中间表格 + error_route 路由 | 完整方案 |
| E: D + Type-Specific Prompts | D + 不同 error_route 用不同 Refiner 模板 | 路由本身是否有用 |

**关键对比**: C vs A 证明"信息增量"的价值；D vs B 证明"结构化路由 > enriched prompt"的价值；E vs D 证明"类型专用模板 > 统一模板"的价值。

### 5. Token 成本重新估算 [MINOR-1]

**Reviewer said**: 中间表格注入成本被低估。

**Action**: 精确估算：
- 阶段 1 Critic: 现有流程，无额外成本
- 阶段 2 Critic: 仅错误样本触发（~20%），注入 1 步前后表格（~1500 tokens/样本）
- 全量额外: 4344 × 0.20 × 1500 = 1.3M input tokens
- 对比 baseline Refine: ~26M tokens（全量），增加 ~5%
- 这个成本增加是可接受的，且只影响错误样本

### 6. Fallback 数学 [IMPORTANT-2]

**Reviewer said**: 25% fallback 率下需要有效样本提升 ~2.7%。

**Action**: 明确分析：
- Critic error_step 准确率：当前已有（Refine 阶段本身就在用）
- 格式遵循率（阶段 2）：预期 >90%（只是扩展输出格式）
- error_route 匹配率：利用现有错误树 + LLM 判断，预期 >80%
- 假设 15% fallback 到 STANDARD-REFINE，85% 使用路由
- 85% 样本需要平均提升 ~2.4% 才能达到整体 +2%
- 这仍然是有挑战的——但即使只达到 +1.5%，结合 API 成本节省，也是有价值的贡献

---

## Revised Proposal

### Method Thesis（修订版）

> 在 Table-Critic 的 Critic 诊断流程中引入**两阶段信息增强诊断**（Two-Stage Information-Enhanced Diagnosis）：第一阶段粗定位确定错误步骤，第二阶段注入该步骤的中间表格状态和 V-Critic 验证报告，让 Critic 在更丰富的信息下做精细诊断。基于精细诊断的 error_route 路由到专用 Refiner 模板。整个流程零微调、增量式集成到现有 Table-Critic 框架中。

### 系统架构（修订版）

```
错误样本
    │
    ▼
┌─ Stage 1: 粗定位（现有 Critic 流程）──────────────┐
│  输入：原始表格 + 推理链 + 最终子表               │
│  输出：error_step                              │
│  cost: 1 LLM call（与现有相同）                  │
└──────────────────────────────────────────────────┘
    │ error_step
    ▼
┌─ Stage 2: 精细诊断（新增）───────────────────────┐
│  输入：原始表格 + 推理链                        │
│       + error_step 前后的中间表格状态            │
│       + V-Critic 验证报告（如有 FAIL）             │
│       + Error Tree 检索的相似案例                 │
│  输出：(error_step, error_route, correction_hint)  │
│  cost: 1 additional LLM call（仅错误样本）         │
└──────────────────────────────────────────────────┘
    │ error_route
    ▼
┌─ Type-Aware Router ─────────────────────────────┐
│  error_route → Refiner 策略映射                  │
│  含 select_row/select_column → ENTITY-REFINE     │
│  含 group_by/add_column/sort → NUMERICAL-REFINE │
│  其他或无法匹配 → STANDARD-REFINE                │
└──────────────────────────────────────────────────┘
    │
    ▼
Type-Specific Refiner → Judge
```

### 核心改动清单（修订版）

| 文件 | 修改 | 行数 |
|------|------|------|
| `critic/TableQA/tools/instruction.py` | 新增 `stage2_instruction`（精细诊断指令） | +15 |
| `critic/TableQA/tools/multiprocess.py` | 新增 `critic_stage2_exec()`（阶段 2 调用） | +30 |
| `critic/TableQA/tools/get_info.py` | 新增 `get_cot_for_critic_stage2()`（含中间表格 + V-Critic） | +25 |
| `refine/TableQA/utils/controller.py` | 两阶段诊断流程 + error_route 路由 | +25 |
| `refine/TableQA/utils/refiner_templates.py` | **新文件**：ENTITY/NUMERICAL Refiner 模板 | +250 |
| **总修改** | | **~345 行** |

### Claim-Driven Validation（修订版）

### Claim 1: 中间表格状态注入增强 Critic 诊断质量
- **Experiment**: C vs A（intermediate tables vs baseline）
- **Metric**: Critic 诊断准确率（error_step 正确率、error_route 一致性）
- **Evidence**: C 的 Critic 在 error_step 和 error_route 上准确率显著高于 A

### Claim 2: 两阶段结构化诊断优于自由文本增强
- **Experiment**: D vs B（structured two-stage vs enriched critique text）
- **Metric**: Refine 准确率
- **Evidence**: D > B，证明结构化路由比简单附加信息更有效

### Claim 3: 类型专用 Refiner 模板进一步提升修正效果
- **Experiment**: E vs D（type-specific prompts vs unified prompt with routing）
- **Metric**: Refine 准确率
- **Evidence**: E > D

### Claim 4: 跨数据集泛化
- **Experiment**: TabFact full dataset
- **Metric**: Accuracy

### Pre-flight Validation（修订版）

在跑实验之前，必须完成：
1. **格式遵循率**: 手动检查 50 个阶段 2 Critic 输出，验证结构化格式 ≥90%
2. **分类一致性**: 人工标注 100 个错误样本的 error_type，对比阶段 2 Critic 分类结果，Kappa ≥0.6
3. **成本验证**: 在 5 个样本上测量阶段 2 的 token 增量，确认 ≤2000 tokens/样本
