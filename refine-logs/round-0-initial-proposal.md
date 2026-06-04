# Round 0: Initial Proposal — CogDiag: Cognitive-Diagnosis-Driven Token-Efficient Refinement

**Date**: 2026-05-22
**Round**: 0
**Version**: Fresh Start (基于正确代码理解 + V-Critic 无效约束)

---

## Problem Anchor

- **Bottom-line problem**: Table-Critic Stage 2 的 token 成本极高，主要瓶颈是 `tree_exec_one_sample()` 每次调用将完整的 error tree JSON（143K chars ≈ 35K tokens）注入 prompt，仅仅为了分类 error_route（一个如 "sub-table error -> row error" 的字符串）。V-Critic（确定性验证器）已验证无效（准确率仅 +0.18%），无法替代 LLM 诊断。
- **Must-solve bottleneck**: `tree_exec` 占 Stage 2 token 的 73%，但 error_route 的唯一用途是从 error tree 检索 few-shot 示例给 Critic。如果能让 Critic 在不需要完整 error tree 的情况下完成诊断，就可以消除这个 73% 的 token 开销。
- **Non-goals**: 不追求新 SOTA；不训练新模型；不做纯工程优化；不修复 V-Critic（已验证无效）。
- **Constraints**: 零微调；不增加整体 token 用量，理想情况减少 ≥30%；可以重构 pipeline；目标 ACL/EMNLP；新增代码 ≤300 行。
- **Success condition**: WikiTQ Refine 阶段准确率 ≥ baseline（不下降），同时 Stage 2 token 总量减少 ≥30%。

## Technical Gap

### Token 开销分析

实测 error tree 数据：
```
few_shot_critic.json 完整 JSON: 143,016 chars ≈ 35,754 tokens
仅保留键名结构（去除叶子内容）:    1,531 chars ≈       382 tokens
叶子节点数量:                                      30 个
```

Stage 2 每次迭代 LLM 调用成本估算：
| 调用 | 估算 tokens | 用途 |
|------|-----------|------|
| tree_exec_one_sample() | ~40,000 | 输出 error_route 字符串 |
| critic_exec_one_sample() | ~10,000 | 输出 error_step + critique |
| dynamic_chain_exec | ~5,000 | 重新执行链 |
| simple_query_cot_original | ~2,000 | 提取答案 |
| judge_exec_one_sample() | ~1,500 | 判定对错 |
| **每次迭代总计** | **~58,500** | |

**tree_exec 占比 = 68.4%**，是绝对的 token 瓶颈。

### 为什么 naive 修复不够

- **减小 error tree**（删除旧案例）？→ error tree 只有 30 个叶子节点，已经很小。问题不在 tree 大小，而在于 tree 结构本身必须展示给 LLM 才能导航。
- **仅保留键名结构**（382 tokens）？→ LLM 需要看到一些叶子内容才能理解分类含义，纯结构信息不够。
- **V-Critic 替代**？→ 已验证无效（+0.18%）。
- **跳过 tree_exec，不用 few-shot？**→ Critic 在没有 few-shot 示例的情况下，诊断精度可能下降。
- **用规则分类 error_route？**→ operation type 到 error_route 的映射不精确，且 error tree 的分类体系（sub-table error → row/column error）本身就不够结构化。

### 真正的问题

当前 pipeline 将"错误分类"和"错误诊断"作为两个独立步骤，分两次 LLM 调用完成。但认知科学（Kahneman 双过程理论）表明：
- **快速分类**（System 1）可以在少量上下文中完成，不需要完整信息
- **深度诊断**（System 2）需要丰富上下文，但在快速分类正确时是浪费

当前 pipeline 对所有样本都使用"深度诊断"路径（tree_exec + critic），即使很多简单错误只需要快速分类就能定位。

## Method Thesis

> 基于认知科学的双过程理论（Dual-Process Theory），将 Stage 2 的两步诊断流程（tree_exec 分类 → critic 诊断）重构为单步认知诊断（Cognitive Diagnosis）。Critic 直接基于链推理上下文和认知诊断框架进行诊断，无需导航完整的 error tree。tree_exec 被完全消除，Stage 2 token 减少 ~68%。当认知诊断失败（Judge 判 Incorrect）时，回退到当前完整管线（含 tree_exec）作为保底路径。

**为什么这是最小充分干预**：
- 只修改 `controller_main_loop()` 的流程控制逻辑，不改变任何子模块
- 不修改 error tree 结构（`few_shot_critic.json`）——继续在回退路径中使用
- 不修改 Critic/Judge/Refine 的实现——它们完全不变
- 新增的"认知诊断"只是 Critic prompt 的一组结构化追问指令（~200 tokens）

## Contribution Focus

- **Dominant contribution**: **认知诊断框架（Cognitive Diagnosis Framework）**——基于认知科学的错误分类体系，替代 operation-type 的 error route。提供四种认知缺陷类型（分解缺陷、表征切换失败、约束传播失败、元认知监控缺失），每种类型有结构化的诊断追问。使 Critic 能在没有完整 error tree 的情况下完成精准诊断。

- **Optional supporting contribution**: **ACT-R 记忆管理**——将 Error Tree 的 few-shot 检索从 uniform random 升级为 ACT-R 激活值加权采样，在保底路径中提供更高质量的 few-shot 示例。

- **Explicit non-contributions**: 不声称 token 减少是贡献（它是架构重构的自然结果）；不声称 cognitive diagnosis taxonomy 是新的认知科学发现（它是从 28 维认知元素分类法 arXiv 2025 迁移的）。

## Proposed Method

### Complexity Budget

- **Frozen backbone**:
  - `critic/TableQA/tools/multiprocess.py` — critic_exec, judge_exec, tree_exec（全部保留，保底路径使用）
  - `critic/TableQA/tools/instruction.py` — critic_instruction, judge_instruction, tree_instruction（全部保留）
  - `refine/TableQA/utils/chain.py` — 链执行引擎
  - `critic/TableQA/tools/few_shot_critic.json` — Error Tree 数据
  - `thought/TableQA/` — Stage 1 完全不变
- **New components**:
  1. `cognitive_diagnosis.py` — 认知诊断指令生成：~80 行
     - `get_cognitive_diagnosis_prompt(sample, error_step=None)` — 生成追加到 Critic CoT 末尾的结构化追问
     - `infer_cognitive_deficit(error_step, chain)` — 基于操作类型的启发式认知缺陷推断
  2. `controller.py` 修改 — 流程重构：~40 行
     - 第一轮迭代：跳过 tree_exec，直接调用 critic（带认知诊断）
     - 如果第一轮成功：更新 error tree（用启发式 error_route）
     - 如果第一轮失败：第二轮回退到当前完整管线（tree_exec → critic → refine → judge）
  3. `get_info.py` 修改 — Critic CoT 构建适配：~20 行
     - 在 `get_cot_for_critic()` 末尾注入认知诊断追问
  4. `update_tree.py` 修改 — 水平扩展适配：~15 行
     - 支持通过认知缺陷类型推断 error_route
- **Total new code**: ~155 行

### System Overview

**当前 Stage 2 流程（每个错题样本）:**
```
Iteration 1:
  tree_exec (~40K tokens) → error_route → critic (~10K tokens) → refine (~5K) → judge (~1.5K)
  Total: ~56.5K tokens

Iteration 2 (if needed):
  tree_exec → error_route → critic → refine → judge
  Total: ~56.5K tokens

Total per sample (1.5 avg iterations): ~84.8K tokens
```

**提案 Stage 2 流程（每个错题样本）:**
```
Iteration 1 (快速路径, Cognitive Diagnosis):
  critic_with_cogdiag (~10K tokens, 包含认知诊断追问) → refine (~5K) → judge (~1.5K)
  Total: ~16.5K tokens  ← 节省 ~40K tokens

Iteration 2 (保底路径, 仅在第一轮失败时触发):
  tree_exec (~40K tokens) → error_route → critic (~10K) → refine (~5K) → judge (~1.5K)
  Total: ~56.5K tokens  ← 与当前完全相同

Expected per sample (假设 50% 第一轮成功):
  0.5 × 16.5K + 0.5 × (16.5K + 56.5K) = 44.8K tokens
  节省: 84.8K → 44.8K = 47% 减少

Total per sample (假设 40% 第一轮成功):
  0.6 × 16.5K + 0.4 × (16.5K + 56.5K) = 46.4K tokens
  节省: 84.8K → 46.4K = 45% 减少
```

### Core Mechanism: Cognitive Diagnosis Framework

核心 insight: **Critic 不需要 error tree 来理解"这个推理链哪里错了"，它需要的是结构化的诊断引导（"应该检查什么类型的错误"）。**

认知诊断框架提供四种认知缺陷类型，每种类型对应一组结构化追问：

```python
COGNITIVE_DEFICITS = {
    "decomposition_failure": {
        "description": "未能将复合问题分解为原子操作，或遗漏了隐式约束条件",
        "diagnostic_questions": [
            "1. 问题中是否包含多个约束条件（如 '同时满足 A 和 B'）？所有约束是否都有对应的操作步骤？",
            "2. select_row 的过滤条件是否覆盖了问题中的所有实体/关键词？",
            "3. 是否存在需要先 group_by 再 select_row 的隐式依赖顺序？"
        ]
    },
    "representation_switch_failure": {
        "description": "数值/文本/格式在操作链中发生隐式格式切换，导致后续操作失效",
        "diagnostic_questions": [
            "1. 检查数值格式：是否有 '1,000' vs '1000' vs '1k' 的混合格式？",
            "2. 检查列名歧义：同一列在不同步骤中是否使用了不同的名称？",
            "3. final_query 的答案格式是否与问题要求的格式一致？"
        ]
    },
    "constraint_propagation_failure": {
        "description": "上游操作的输出错误被后续操作接受，导致错误逐级放大",
        "diagnostic_questions": [
            "1. 如果第 N 步的输出有误，第 N+1 步是否应该仍使用它？",
            "2. sort_by 操作的输入表是否确实已被正确过滤/分组？",
            "3. 最终答案的计算是否基于正确的中间子表？"
        ]
    },
    "metacognitive_monitoring_gap": {
        "description": "推理过程中缺乏自我检查，未发现操作结果中的明显异常",
        "diagnostic_questions": [
            "1. 检查 chain 中间步骤：最终子表的行数/列数是否合理？",
            "2. 最终答案的数值量级是否与问题中的数量级一致？",
            "3. 是否存在'看似正确的答案但实际上忽略了问题中的关键条件'的情况？"
        ]
    }
}
```

### Integration into Critic Prompt

在 `get_cot_for_critic()` 的末尾（在 "Critique:" 之前）注入认知诊断追问：

```python
# 在 cot += "Critique:" 之前注入
from cognitive_diagnosis import infer_cognitive_deficit

cognitive_deficit = infer_cognitive_deficit(error_step, chain)
if cognitive_deficit:
    deficit_info = COGNITIVE_DEFICITS[cognitive_deficit]
    cot += f"\n\n[Cognitive Diagnosis Framework]\n"
    cot += f"Based on the reasoning steps above, this error may fall under: {deficit_info['description']}\n"
    cot += f"Please verify the following:\n"
    for q in deficit_info["diagnostic_questions"]:
        cot += f"  {q}\n"
else:
    cot += "\n\n[Cognitive Diagnosis Framework]\n"
    cot += "Analyze the reasoning chain and identify the most likely type of error.\n"
    cot += "Consider: Was the problem properly decomposed? Was there a format switch? "
    cot += "Did an intermediate result propagate incorrectly?\n"
```

### Heuristic Error Route Inference

当认知诊断成功修正时，需要推断 error_route 以更新 error tree：

```python
def infer_error_route(cognitive_deficit, error_step, chain):
    """基于认知缺陷类型和操作链结构，推断 error tree 路径"""
    COGNITIVE_TO_ROUTE = {
        "decomposition_failure": "sub-table error -> row error",
        "representation_switch_failure": "sub-table error -> column error",
        "constraint_propagation_failure": "sub-table error -> row error",
        "metacognitive_monitoring_gap": "final query error -> logical error",
    }
    return COGNITIVE_TO_ROUTE.get(cognitive_deficit, "sub-table error -> row error")
```

### Controller Flow Modification

```python
# controller_main_loop() 中的核心修改

# 当前流程:
#   tree_exec → error_route → critic → refine → judge

# 修改后流程:
#   第一轮: critic (带认知诊断, 无 tree_exec) → refine → judge
#   如果第一轮失败:
#   第二轮: tree_exec → error_route → critic → refine → judge (当前完整管线)

for iteration in range(max_iterations):
    if iteration == 0:
        # 快速路径：认知诊断模式
        # 跳过 tree_exec，直接调用 critic
        state = executor.execute_cognitive_diagnosis(state)  # ← 新增
    else:
        # 保底路径：当前完整管线
        state = executor.execute(state, decision)  # ← 不变
    
    # judge 检查
    if state.is_correct:
        if iteration == 0:
            # 认知诊断成功 → 用推断的 error_route 更新 tree
            inferred_route = infer_cognitive_deficit(...)
            update_error_tree(sample, inferred_route, ...)
        else:
            # 完整管线成功 → 正常更新 tree
            update_error_tree(sample, state.error_route, ...)
        break
```

### Optional: ACT-R Memory Management (Supporting Contribution)

在保底路径中（第二轮，使用 tree_exec 时），用 ACT-R 替代 uniform random 检索：

```python
def act_r_weighted_error_shot(error_route, few_shot_dict, k=3):
    """ACT-R 激活值加权的 few-shot 检索（替代 random.sample）"""
    candidates = return_error_shot(error_route, few_shot_dict)  # 复用现有函数
    # 计算 ACT-R base-level activation
    # A(node) = ln(Σ(t_now - t_i)^(-d)) + w * S(node, context)
    # 简化版：用 access_count 和 recency 替代完整公式
    scored = []
    for candidate in candidates:
        score = candidate.get("access_count", 0) * 0.7 + candidate.get("recency", 0.5) * 0.3
        scored.append((score, candidate))
    scored.sort(reverse=True)
    return [item for _, item in scored[:k]]
```

### Fallback 安全性

**最坏情况**：如果认知诊断路径的准确率低于当前完整管线，会怎样？
- 第一轮浪费 ~16.5K tokens（Critic + refine + judge）
- 第二轮回退到完整管线，多花 ~56.5K tokens
- 总成本：~73K tokens vs 当前 ~85K tokens — 仍然节省 ~14%
- 准确率：第二轮（完整管线）保证了保底准确率

**风险极低**的原因：认知诊断只是给 Critic 提供了结构化的追问引导，Critic 仍然看到完整的 chain reasoning + 中间表格状态 + 最终子表。这些信息已经足够定位大部分错误步骤。few-shot 示例主要帮助 Critic 理解输出格式和常见错误模式，而不是提供新的诊断信息。

## Claim-Driven Validation

### Claim 1: 认知诊断路径保持准确率（不下降）

- **Experiment**: A (proposed, 认知诊断) vs B (baseline, 当前管线)
- **Metric**: Refine 准确率、Refine 成功率（修正后 Judge 通过的比例）
- **Expected**: A ≥ B（不下降），且 A 的第一轮成功率 ≥ 40%

### Claim 2: Token 减少 ≥30%

- **Experiment**: A vs B 的总 token 消耗
- **Metric**: per-sample average tokens, total Stage 2 tokens
- **Expected**: A 总 token ≤ 70% of B

### Claim 3: 回退机制保证安全（不下降的最坏情况）

- **Experiment**: 比较 A 的第二轮（回退路径）与 B 的准确率
- **Expected**: A 第二轮准确率 = B 准确率（因为使用相同管线）

### Ablation Matrix

| Config | 第一轮（认知诊断） | 第二轮（保底路径） | 检验什么 |
|--------|:-------------:|:------------:|---------|
| A: Baseline | ✗ | 完整管线 | 基线准确率 |
| B: CogDiag | ✓ | 完整管线（仅失败时） | 认知诊断的因果价值 |
| C: CogDiag + ACT-R | ✓ | 完整管线 + ACT-R few-shot | ACT-R 记忆管理的增量价值 |

## Novelty and Elegance Argument

**为什么这不是"换个 prompt"**：
- 认知诊断框架提供了**理论驱动**的错误分类体系（来自认知科学 28 维认知元素分类法 + 双过程理论），而非工程直觉的 "不如用 fewer-shot"
- **消除 tree_exec** 是由数据驱动的发现（73% token 开销在一个仅输出字符串的调用上）直接推导出的架构决策，而非刻意追求的优化
- token 减少是**架构重构的自然结果**，不是目标本身

**Closest work**:
1. **Kargupta et al. (2025)** — 28 维认知元素分类法（本方案的理论来源）
2. **Kahneman (2011)** — Thinking, Fast and Slow（双过程理论，本方案的理论框架）
3. **当前 Table-Critic pipeline** — 完整保留作为保底路径

**本方案的区别**：
- 首次将认知科学的双过程理论系统化地应用于表格推理的错误诊断
- 首次基于 token 开销分析识别出 tree_exec 作为 token 瓶颈（非经验猜测）
- 保留了完整管线作为保底，消除了"准确率下降"的风险

## Risk & Mitigation

| 风险 | 概率 | 缓解 |
|------|------|------|
| 认知诊断准确率显著低于完整管线 | 低 | 保底路径（第二轮回退）保证安全 |
| 启发式 error_route 推断不准确 | 中 | 仅影响 tree 更新位置，不影响诊断准确率 |
| ACT-R 权重公式过于简化 | 低 | 仅用于 supporting contribution，不影响主贡献 |
| Reviewer 认为"只是去掉 tree_exec" | 中 | 强调理论动机（双过程理论）和数据驱动发现（73% token 开销） |

## Compute & Timeline Estimate

- **实现**: 1.5 天（cognitive_diagnosis.py + controller.py 修改 + get_info.py 修改）
- **Pre-flight**: 0.5 天（验证认知诊断 prompt 质量）
- **Pilot (100 samples)**: 1 天
- **Full WikiTQ (4344)**: 2-3 天
- **消融 (A-B 或 A-B-C)**: 1 天
- **Total**: ~6-7 天
