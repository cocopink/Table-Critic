# Round 1 Review — CogDiag: Cognitive-Diagnosis-Driven Token-Efficient Refinement

**Date**: 2026-05-22
**Round**: 1 (Adversarial Self-Review)
**Reviewer**: Adversarial Senior Reviewer (NeurIPS/ICML/ACL perspective)

---

## Scores

| 维度 | 分数 | 理由 |
|------|------|------|
| Problem Fidelity | 9 | 问题锚定极其精准：tree_exec 占 Stage 2 token 的 73%，实测 143K chars ≈ 35.7K tokens 仅用于输出一个 error_route 字符串。这是数据驱动的发现，非常扎实。 |
| Method Specificity | 5 | 认知诊断框架的具体机制不够清晰：(1) 4 种认知缺陷类型如何与具体操作类型（select_row/sort_by 等）关联？(2) `infer_cognitive_deficit()` 的启发式规则是什么？(3) 第一轮迭代中 critic_exec_one_sample 如何处理没有 error_route 的情况——代码写 `executor.execute_cognitive_diagnosis(state)` 但这个方法不存在，也没有说明如何替换 critic 的 few-shot 输入。 |
| Contribution Quality | 4 | **核心问题：认知诊断框架本质上是 4 组静态 prompt 模板。** 4 种认知缺陷类型 × 每种 3 个追问问题，这就是 12 句预定义问题。审稿人会直接说："You replaced a 143K-char lookup table with 12 sentences. The cognitive science labels are window dressing." 双过程理论（System 1/2）的映射也极其表面——"快速路径"和"慢速回退"只是标准的 try-cheap-first-then-fallback 工程模式，不是认知科学 insight。 |
| Frontier Leverage | 5 | 没有使用任何 foundation-model-era 的新技术。认知诊断框架是纯手写的规则+prompt，ACT-R 的实现也退化为线性插值（`access_count * 0.7 + recency * 0.3`），而非真正的 ACT-R base-level activation 公式。 |
| Feasibility | 7 | 控制流修改（跳过 tree_exec）是可行的，fallback 机制设计合理。但 `critic_exec_one_sample` 当 error_route 缺失时实际走 `get_critic_few_shot("random")` → `return_error_shot` 回退到 `get_terminal_nodes` → 随机采样 5 个 few-shot。这意味着**即使跳过 tree_exec，critic 仍然会拿到 random few-shot**。提案中完全没有提到这一点。 |
| Validation Focus | 6 | 3 配置消融矩阵（A/B/C）清晰。但缺少一个关键实验：**Critic 在完全没有 few-shot 的情况下 vs 有 random few-shot 的情况下的诊断准确率对比**。这直接决定了认知诊断框架能否替代 few-shot。 |
| Venue Readiness | 4 | 最大担忧：**"消除 tree_exec"是效率优化，不是方法论创新。** 论文标题中的 "Cognitive-Diagnosis-Driven" 暗示有认知科学方法论，但实际贡献是 12 句预定义问题 + try-cheap-first 控制流。ACL/EMNLP 审稿人可能接受，但 NeurIPS/ICML 会直接 reject。 |

**OVERALL: 5.7/10 | Verdict: REVISE**

---

## Critical Concerns

### CRITICAL 1: 认知诊断框架是 prompt engineering，不是方法论创新

4 种认知缺陷类型（decomposition_failure, representation_switch_failure, constraint_propagation_failure, metacognitive_monitoring_gap）和它们的 12 个追问问题，本质上是：

```python
# 这就是提案的全部"创新"
COGNITIVE_DEFICITS = {
    "decomposition_failure": [3 个问题],
    "representation_switch_failure": [3 个问题],
    "constraint_propagation_failure": [3 个问题],
    "metacognitive_monitoring_gap": [3 个问题],
}
```

审稿人会问：
1. 这 4 种分类从何而来？与 Kahneman 双过程理论的具体对应关系是什么？（提案只说"从 28 维认知元素分类法迁移"，但 28→4 的映射逻辑未说明）
2. 为什么是这 4 种而不是 3 种或 5 种？消融实验能证明每种都有独立价值吗？
3. 这和 Chain-of-Thought prompting 的本质区别是什么？CoT 也会问"检查每一步推理是否正确"，认知诊断只是把这些追问结构化了

**Fix**：如果认知诊断要成为真正的方法论贡献，需要：
- (a) 基于错误分布数据（WikiTQ 39.1% 数值 / 29.3% 实体 / 24.3% 排序）推导认知缺陷分类，而非从认知科学理论自上而下地套用
- (b) 设计一个**自动化的认知缺陷推断机制**（而非手写 `infer_cognitive_deficit()` 启发式），例如让 Critic 自己输出认知缺陷类型
- (c) 或者换一个更有深度的理论框架

### CRITICAL 2: Critic 在没有 few-shot 的情况下能正常工作吗？

提案假设 Critic 不需要 error tree 的 few-shot 示例就能完成诊断。但看代码：

```python
# critic_exec_one_sample 的 prompt 结构：
prompt = critic_instruction + few_shot + cot
```

`few_shot` 块提供了 **5 个具体的错误诊断示例**（来自 error tree），教会 Critic：
1. 输出格式（`Conclusion: [Incorrect] Step <NUM>`）
2. 常见错误模式的识别方式
3. 从 CoT 中提取诊断线索的方法

提案用认知诊断问题替换 few-shot。但认知诊断问题是**通用追问**（"检查数值格式是否一致"），而 few-shot 是**具体示例**（"这个 select_row 步骤忽略了 'rank' 关键词"）。**通用追问和具体示例的信息量完全不同。**

此外，实际代码中即使 `error_route="random"`，`return_error_shot()` 也会回退到 `get_terminal_nodes()` 随机采样 5 个 few-shot。所以**即使跳过 tree_exec，Critic 仍然能拿到 random few-shot**——提案完全忽略了这一点。

**Fix**：
1. 明确区分两个变量：(a) 是否跳过 tree_exec（省 token）(b) 是否提供 few-shot（影响诊断质量）
2. 在 pilot 实验中测试 4 种配置：
   - (i) tree_exec + route-specific few-shot（当前 baseline）
   - (ii) 跳过 tree_exec + random few-shot（最简单的节省 token 方案）
   - (iii) 跳过 tree_exec + 认知诊断（提案方案）
   - (iv) 跳过 tree_exec + random few-shot + 认知诊断
3. 如果 (ii) 已经足够好，那认知诊断的增量价值就需要证明

### CRITICAL 3: 双过程理论映射是表面工程

提案将 Kahneman 的 System 1/System 2 映射为"第一轮快速路径/第二轮保底路径"。但：

- Kahneman 的 System 1 是**快速、自动、直觉**的认知过程
- Kahneman 的 System 2 是**缓慢、刻意、分析**的认知过程
- 这里的"快速路径"和"慢速路径"的区别只是**有没有调用 tree_exec**——一个 LLM 调用的有无

真正的 System 1/System 2 区别在于认知过程本身（直觉 vs 推理），而不在于调用了几个 LLM。两轮都用了 LLM 进行推理，区别只在于输入上下文的多少。这不是双过程理论，这是**分级上下文策略**（tiered context strategy）。

**Fix**：如果要用双过程理论，需要更深入的对应：
- System 1: Critic 基于 pattern matching（从 few-shot 中匹配相似错误模式）进行快速诊断
- System 2: Critic 基于 causal reasoning（逐步分析推理链的因果关系）进行深度诊断
- 这两种认知模式由同一个 Critic 在不同条件下自动切换

或者干脆不用双过程理论，换一个更自然的框架。

---

## Important Concerns

### IMPORTANT 1: ACT-R 部分是半成品

```python
# 提案中的 ACT-R 实现
score = candidate.get("access_count", 0) * 0.7 + candidate.get("recency", 0.5) * 0.3
```

这不是 ACT-R。真正的 ACT-R base-level activation 是：

```
A(node) = ln(Σ(t_now - t_i)^(-d))
```

其中 d 是 decay 参数（通常 0.5），t_i 是第 i 次访问的时间。这是一个**幂律衰减**函数，体现了记忆遗忘曲线。

提案中的公式是 `0.7 * count + 0.3 * recency`——这是一个线性插值。而且 `access_count` 和 `recency` 这两个字段在现有的 `few_shot_critic.json` 数据结构中**根本不存在**。这意味着要么要修改数据结构来追踪访问记录，要么这个功能无法实现。

**Fix**：要么正确实现 ACT-R（包括数据结构修改和时间追踪），要么直接删除。作为 "Optional supporting contribution"，它现在的状态是半成品。

### IMPORTANT 2: `infer_error_route()` 会污染 error tree

```python
COGNITIVE_TO_ROUTE = {
    "decomposition_failure": "sub-table error -> row error",
    "representation_switch_failure": "sub-table error -> column error",
    ...
}
```

**所有** decomposition_failure 都会被路由到 "sub-table error -> row error"。但分解失败可能发生在 select_column（列选择遗漏了约束条件对应的列）或 group_by（分组方式不正确）等不同操作上，error_route 应该不同。

这会导致 error tree 中积累大量错误分类的样本，**随着时间推移，tree 的 few-shot 质量会持续下降**。由于保底路径（第二轮）也依赖这个 tree 的 few-shot，这会**间接降低保底路径的效果**。

**Fix**：认知诊断成功时，不要更新 error tree。只在保底路径（tree_exec）成功时更新。这是最安全的策略。

### IMPORTANT 3: Token 节省估算依赖强假设

提案估算：
- 假设 50% 第一轮成功 → 节省 47%
- 假设 40% 第一轮成功 → 节省 45%

但计算有误。看提案的公式：
```
Expected per sample (假设 50% 第一轮成功):
  0.5 × 16.5K + 0.5 × (16.5K + 56.5K) = 44.8K tokens
```

等等——如果 50% 第一轮成功，那另外 50% 需要第一轮 + 第二轮。但当前 baseline 的平均迭代次数是 1.5，意味着有些样本本身就只需要 1 轮。正确的对比应该是：

```
Baseline (当前):
  每次迭代 ~58.5K tokens
  平均 1.5 次迭代 = 87.8K tokens

CogDiag (假设 50% 第一轮成功):
  成功的 50%: 1 轮快速路径 = 16.5K
  失败的 50%: 1 轮快速 + 1 轮保底 = 16.5K + 56.5K = 73K
  Expected = 0.5 × 16.5K + 0.5 × 73K = 44.75K
```

节省 87.8K → 44.75K = **49%**。这个估算其实比提案说的还好。

但关键假设是：**50% 第一轮成功率**。如果只有 20%，则：
```
Expected = 0.2 × 16.5K + 0.8 × 73K = 61.7K
节省: 87.8K → 61.7K = 30%
```

刚好踩到 30% 目标线。如果只有 10%，则节省 17.7%，不达标。

**需要 honest 地报告不同成功率下的节省百分比**。

---

## Minor Concerns

### MINOR 1: 提案中 `execute_cognitive_diagnosis()` 不存在

控制器代码中的 `executor.execute_cognitive_diagnosis(state)` 是新方法，没有说明其实现。实际需要修改 ActionExecutor 的 execute() 方法，新增一个 code path。这不是 40 行能完成的——需要修改 controller.py 的状态转移逻辑、decide() 方法的决策规则、以及 ActionExecutor 的 execute() 分支。

### MINOR 2: 提案忽略 DIAGNOSE_BP vs DIAGNOSE_FS 的区分

当前 pipeline 中，EXECUTE_TREE 后 LLM 会决定使用 DIAGNOSE_BP（blueprint-only）还是 DIAGNOSE_FS（full few-shot）。CogDiag 提案跳过了 EXECUTE_TREE，但没有说明 DIAGNOSE_BP/FS 的决策如何处理。

### MINOR 3: 代码量估算偏低

提案声称 ~155 行新代码。实际需要：
- `cognitive_diagnosis.py`: ~80 行（合理）
- `controller.py` 修改: 不只是 40 行——需要修改 decide()、execute()、_llm_decide_diagnose()、controller_main_loop()
- `get_info.py` 修改: ~20 行（合理）
- `update_tree.py` 修改: ~15 行（合理）
- 可能还需要修改 `instruction.py`（增加认知诊断的说明）

估算 ~200 行更现实。

---

## Simplification Opportunities

1. **先测 "跳过 tree_exec + random few-shot"**：这可能已经足够好。不需要认知诊断框架，只需要把 tree_exec 的 error_route 替换为 "random"，让 critic 拿随机 few-shot。如果这个就能省 73% token 且准确率不降，那认知诊断就是多余的。

2. **删除 ACT-R**：作为 supporting contribution 它不成熟，且分散了论文焦点。如果主贡献不够强，不应该用 supporting contribution 来凑数。

3. **不要更新 error tree 的认知诊断结果**：在快速路径成功时不更新 tree，只在保底路径成功时更新。这消除了 `infer_error_route()` 的需要，也避免了 tree 污染。

---

## Modernization Opportunities

1. **让 Critic 自己推断认知缺陷类型**：不是手写 4 种类型 + 12 个问题，而是在 critic_instruction 中增加一个输出字段要求 Critic 输出它认为的错误类型。然后基于 Critic 的输出动态检索相关的诊断问题。这把 Critic 从被动接收者变为主动参与者，更符合 foundation-model-era 的思路。

2. **用 LLM 做一级路由而非手写规则**：`infer_cognitive_deficit()` 可以是一个轻量级的 LLM 调用（~500 tokens），让模型根据 chain 结构和操作类型自动推断最可能的错误类别。这比手写 if-else 更鲁棒，且 token 成本极低。

---

## Drift Warning

**NONE** — 提案仍然锚定在 "消除 tree_exec 的 token 开销" 这个核心问题上。方向正确。

---

## Verdict

**REVISE** — 方向正确（消除 tree_exec 省 token 是有价值的），但当前的认知诊断框架不够深。核心问题：

1. 4 种认知缺陷 × 12 个问题 = prompt engineering，不是方法论创新
2. Critic 在没有 few-shot 的情况下能否工作是一个未验证的关键假设
3. 双过程理论的映射过于表面

**建议方向**：

- **路线 A（最简）**：不引入认知诊断，直接测试 "跳过 tree_exec + random few-shot"。如果效果好，论文可以聚焦在 "token 开销分析 + 分级上下文策略"，不需要认知科学包装。

- **路线 B（中等）**：让 Critic 自己输出错误分类（而非 tree_exec），用 Critic 的分类结果替代 error_route 检索 few-shot。这消除了 tree_exec 但保留了 few-shot 机制。贡献是 "self-classified error routing" 而非 "cognitive diagnosis"。

- **路线 C（有深度）**：重新设计认知诊断为一个**轻量级 LLM 路由器**（~500 tokens），基于 chain 结构自动推断错误类型并检索相应诊断策略。与 tree_exec 的区别：路由器只看 chain 的元信息（操作类型序列、中间表大小变化），不看完整 error tree。这是一个信息高效的路由机制。

---

<details>
<summary>Review Context</summary>

Reviewer profile: Senior ML researcher with expertise in table reasoning, multi-agent systems, and efficient inference. Familiar with Table-Critic (ACL 2025), Chain-of-Table (NeurIPS 2023), AlphaGeometry (Nature 2024), and cognitive science literature.

Key assumptions verified against code:
- `tree_exec_one_sample()` loads FULL `few_shot_critic.json` (143K chars) via `get_cot_for_tree()` — confirmed in `get_info.py:229-298`
- `critic_exec_one_sample()` prompt = critic_instruction + few_shot + cot — confirmed in `multiprocess.py:65-157`
- `return_error_shot("random", ...)` falls back to `get_terminal_nodes()` + random.sample — confirmed in `get_info.py:86-111`
- Controller flow: EXECUTE_TREE → DIAGNOSE_BP/FS → REFINE_CHAIN/QUERY → Judge — confirmed in `controller.py:1331-1391`
- DIAGNOSE_BP/FS decision made by LLM after EXECUTE_TREE — confirmed in `controller.py:1361-1371`

</details>
