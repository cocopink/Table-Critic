# FINAL_PROPOSAL.md

**Date**: 2026-05-21
**Version**: Round 2 Final — Information-Enhanced Error Diagnosis

---

## Problem Anchor

**Bottom-line problem**: Table-Critic 的 Refine 阶段对错误样本的修正效率极低（WikiTQ Thought→Refine 仅 +2%），根本原因是 Critic 缺乏足够的诊断信息——当前 Critic 只能看到推理链的最终子表（一个静态快照），看不到每个操作步骤如何逐步变换表格。这就像一个程序调试器只给你看最终输出，不给你看中间变量——定位 bug 几乎不可能。

**Must-solve bottleneck**: Critic 的诊断输入只包含最终子表，缺少操作前后的中间表格对比（table diff），导致错误定位不准确；Critic 的诊断输出是自由文本，没有结构化分类，Refiner 无法针对性地选择修正策略。

**Non-goals**: 不追求新 SOTA；不引入需训练的组件；不改变 Thought 阶段。

**Constraints**: 零微调；必须基于 Table-Critic 现有代码；WikiTQ + TabFact 双数据集验证；目标 ACL/EMNLP。

**Success condition**: WikiTQ Refine 阶段准确率提升 ≥2%（从 baseline +2% 到 +4%），且消融实验证明中间表格注入是主要贡献来源。

---

## Technical Gap

当前 `get_cot_for_critic()` 构建的 Critic 上下文包含：原始表格 + 问题 + 推理步骤链 + **最终子表**（`table_log[-1]`）。Critic 看不到中间表格状态变化，无法精确诊断"哪步操作改变了什么"。

类比：这就像调试一个函数链 `f(g(h(x)))`，你只看到 `x` 和 `f(g(h(x)))` 的值，看不到 `h(x)` 和 `g(h(x))` 的中间结果。要精确定位哪个函数出错，你需要 diff：`h(x)` vs `g(h(x))` vs `f(g(h(x)))`。

**为什么 naive 修复不够**：
- 更大的 Critic prompt？→ 信息本身不够，不是 prompt 的问题
- 更多 few-shot？→ 已有 Error Tree 检索，但检索的案例没有中间状态
- 多次迭代？→ max_iterations=2 已是瓶颈
- 训练 PSV 模型？→ 违反零微调约束（StepCo 路线）

---

## Method Thesis

> 在 Table-Critic 的 Critic 诊断中引入**操作级表格 Diff**（Operation-Level Table Diff）——通过两阶段诊断流程，让 Critic 从只看"最终快照"升级为看"逐步变化"，显著增强错误定位精度。阶段 1 用现有流程粗定位错误步骤，阶段 2 注入该步骤前后的中间表格状态（table diff）+ V-Critic 验证报告，让 Critic 在动态变化信息下做精细诊断。基于精细诊断的 error_route 路由到专用 Refiner 模板。

**Why the "table diff" framing is the right narrative**:
- 两阶段是手段，table diff 才是 insight
- 类比程序调试的 diff 视图：调试器不猜 bug 在哪行，而是 diff 前后状态
- 这是 Critic 的根本性信息增强——从"静态快照诊断"到"动态 diff 诊断"

---

## Contribution Focus

- **Dominant contribution**: 操作级 Table Diff —— 通过注入中间表格状态，让 Critic 从静态快照诊断升级为动态 diff 诊断。这为多智能体批评框架中的错误定位提供了新的信息维度。

- **Optional supporting contribution**: 基于诊断信号的智能修正路由 —— 将 Critic 的结构化诊断（error_route）映射到类型专用 Refiner 模板，实现"分类→分派→修正"的精准修正流水线。

- **Explicit non-contributions**: 不声称两阶段架构是创新（coarse-to-fine 是成熟范式）；不声称 V-Critic 是贡献（已证伪）；不声称路由策略是主贡献（是辅助）。

---

## Proposed Method

### Complexity Budget

- **Frozen backbone**: Table-Critic 全部现有代码（Critic/Controller/Refiner/Error Tree/TableAnalyzer/V-Critic）
- **New components**:
  1. `stage2_instruction`（Critic 阶段 2 的诊断指令）：~15 行
  2. `critic_stage2_exec()`（阶段 2 调用逻辑）：~30 行
  3. `get_cot_for_critic_stage2()`（含 table diff + V-Critic）：~25 行
  4. Controller 两阶段诊断流程 + 路由：~25 行
  5. Type-specific Refiner 模板（可选增强）：~250 行
- **Total new code**: ~345 行

### System Overview

```
错误样本（Thought 预测 [Incorrect]）
    │
    ▼
┌─ Stage 1: 粗定位（现有 Critic 流程）──────────────┐
│  输入：原始表格 + 推理链 + 最终子表               │
│  输出：error_step                              │
│  cost: 1 LLM call（与现有完全相同）              │
└──────────────────────────────────────────────────┘
    │ error_step
    ▼
┌─ Stage 2: Table Diff 诊断（核心新组件）──────────┐
│  输入：原始表格 + 推理链                        │
│       + table_log[error_step]（步骤前子表）       │
│       + table_log[error_step + 1]（步骤后子表）   │
│       + V-Critic 验证报告（如有 FAIL）             │
│       + Error Tree 检索的匹配案例                 │
│  输出：(error_step, error_route, correction_hint)  │
│  insight: Critic 看到 "操作前" vs "操作后" 的 diff │
│  cost: 1 additional LLM call（仅错误样本）         │
└──────────────────────────────────────────────────┘
    │ error_route
    ▼
┌─ Type-Aware Router ─────────────────────────────┐
│  error_route → Refiner 策略                       │
│  含 select_row/select_column → ENTITY-REFINE     │
│  含 group_by/add_column/sort → NUMERICAL-REFINE │
│  含 final_query 相关 → QUERY-REFINE              │
│  其他 → STANDARD-REFINE                         │
└──────────────────────────────────────────────────┘
    │
    ▼
Refiner → Judge
```

### Core Mechanism: Operation-Level Table Diff

`get_table_log()` 已经在代码库中计算了每个操作后的中间表格状态。Stage 2 提取指定 error_step 前后的两个 table_log 条目，让 Critic 看到操作的具体效果：

```
[Table before Step 3 (select_row)]:
col   : rank | cyclist         | team
row 1 : 1    | alejandro valverde | esp
row 2 : 2    | alexandr kolobnev | rus
row 3 : 3    | davide rebellin  | ita
...
row 10: 10   | david moncoutié  | fra

[Table after Step 3 (select_row)]:
col   : rank | cyclist         | team
row 1 : 1    | alejandro valverde | esp
row 5 : 5    | franco pellizotti | ita
...

[Change]: Selected rows {1, 5} → removed rows {2, 3, 4, 6, 7, 8, 9, 10}
```

Critic 现在不仅能看到"最终子表"，还能看到"这一步到底改了什么"。这类似于 git diff —— 不是描述"有错误"，而是展示"改动前 vs 改动后"。

### Error Route Routing（辅助贡献）

阶段 2 的 Critic 从现有错误树中选择最匹配的 error_route 作为诊断结果。路由映射：

| error_route 模式 | Refiner 策略 | 关键 prompt 差异 |
|-----------------|------------|-----------------|
| `select_row/select_column` 相关 | ENTITY-REFINE | 利用 TableAnalyzer column_normalizations hint |
| `group_by/add_column/sort_column` 相关 | NUMERICAL-REFINE | 强调逐步计算验证 |
| `final_query` 相关 | QUERY-REFINE | 强调答案格式约束 |
| 无法匹配 | STANDARD-REFINE | 现有 baseline |

### V-Critic as Auxiliary Signal

V-Critic 不作为独立贡献，但在阶段 2 中提供**结构验证证据**：
- 如果 `verify_chain()` 在 error_step 发现 FAIL → 注入验证报告
- Critic 可以利用结构验证失败信息更准确地判断错误子类型
- 例如：`_verify_sort_column` FAIL（排序方向矛盾）→ 强信号指向 SORTING 类错误

### Token Cost Analysis

| 组件 | 触发率 | 额外 tokens/样本 | 全量额外 tokens |
|------|--------|-----------------|-----------------|
| Stage 1 Critic | 100%（现有） | 0 | 0 |
| Stage 2 Critic | ~20%（错误样本） | ~1500 | 4344 × 0.20 × 1500 ≈ **1.3M** |
| Refiner prompt | ~20%（错误样本）| ~200 | 4344 × 0.20 × 200 ≈ **0.17M** |
| **总计** | | | **~1.5M** |

对比 baseline Refine 全量 ~26M tokens，增加 ~5.8%。完全可接受。

---

## Claim-Driven Validation

### Claim 1: Table Diff 增强诊断质量（主贡献）

- **Experiment**: C vs A（table diff 注入 vs 无 table diff）
- **Metric**: Critic error_step 准确率、Refine 准确率
- **Expected**: C 的 Critic 准确率显著提升，C 的 Refine 准确率 > A

### Claim 2: 结构化路由优于 enriched prompt

- **Experiment**: D vs B（structured routing vs enriched critique text）
- **Metric**: Refine 准确率
- **Expected**: D > B，证明结构化路由比简单附加信息更有效

### Claim 3: 类型专用模板进一步提升（辅助）

- **Experiment**: E vs D（type-specific prompts vs unified prompt with routing）
- **Metric**: Refine 准确率
- **Expected**: E ≥ D（如果差距不大，这部分退化为可选增强）

### Claim 4: 跨数据集泛化

- **Experiment**: TabFact full dataset
- **Metric**: Accuracy

### Ablation Matrix

| Config | Table Diff | Structured Routing | Type-Specific | 验证什么 |
|--------|:---------:|:------------------:|:------------:|---------|
| A: Baseline | ✗ | ✗ | ✗ | 基线 |
| B: Enriched | ✗ | ✗ | ✗ | 附加信息本身 |
| C: Diff Only | ✓ | ✗ | ✗ | 信息增量 |
| D: Diff + Routing | ✓ | ✓ | ✗ | 结构化 vs enriched |
| E: Full | ✓ | ✓ | ✓ | 完整方案 |

---

## Pre-flight Validation

1. **格式遵循率**: 手动检查 50 个 Stage 2 Critic 输出 ≥90% 格式正确
2. **分类一致性**: 人工标注 100 个错误样本，对比 Critic error_route 诊断，Kappa ≥ 0.6
3. **成本验证**: 5 样本测量 Stage 2 token 增量 ≤ 2000 tokens

## Risk & Mitigation

| 风险 | 缓解 |
|------|------|
| Critic 阶段 2 分类不准 | Fallback 到 STANDARD-REFINE；消融中量化 fallback 率 |
| Table diff 增加太多 token | 只注入 1 步前后表格（~1500 tokens）；可以跳过 |
| Refiner 模板改进有限 | 消融 E vs D 量化；退化为可选增强 |
| 两阶段故事被质疑为不新颖 | 叙事锚定在"table diff"而非"两阶段" |
| +2% 天花板不够 | TabFact 提供额外证据；即使 +1.5% 也有价值 |

## Timeline

- **实现**: 2-3 天
- **Pre-flight validation**: 1 天
- **Pilot (100 samples)**: 1 天
- **Full WikiTQ (4344)**: 3-5 天
- **消融**: 2 天
- **TabFact**: 2 天
- **总计**: ~2 周
