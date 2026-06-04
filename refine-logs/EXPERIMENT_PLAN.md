# Experiment Plan

**Problem**: Table-Critic Refine 阶段对所有样本无差别处理，正确样本浪费 API 调用
**Method Thesis**: 自适应路由（AdaRefine）根据问题复杂度决定 SKIP/LITE/FULL 修正策略，降低 40%+ API 成本
**Date**: 2026-05-21

## Claim Map
| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|-----------------|-----------------------------|---------------|
| C1 | AdaRefine 在不损失准确率前提下降低 40%+ API 成本 | WikiTQ 准确率下降 <0.5%，API 调用减少 ≥40% | B1, B2, B3 |
| C2 | 路由信号的消融证明各组件贡献 | 去除某个信号后效果显著变差 | B4 |
| C3 | 跨数据集泛化 | TabFact 上同样有效 | B5 |

## Paper Storyline
- Main paper must prove: C1 (成本降低) + C2 (信号消融)
- Appendix can support: C3 (TabFact 泛化)、失败案例分析
- Experiments intentionally cut: V-Critic 作为独立贡献（已证伪）

## Experiment Blocks

### Block 1: Judge-Skip Sanity Check（最小可行性验证）
- **Claim tested**: C1 (部分)
- **Why this block exists**: 用最简单的路由信号（Judge 预检）验证 SKIP 策略是否可行
- **Dataset/split**: WikiTQ, 从现有 4344 samples 中取 100 samples
- **Compared systems**: Baseline (standard Refine) vs Judge-Skip (Judge says correct → SKIP)
- **Metrics**: Accuracy, API calls, Total tokens
- **Setup details**: 使用 `results/flattened/thought/wikitq/gpt-5.4` 的 Thought 结果
- **Success criterion**: 准确率下降 <1%，API 调用减少 ≥20%
- **Failure interpretation**: 如果准确率下降 >1%，说明 Judge 预检不可靠，需要更保守的策略
- **Priority**: MUST-RUN

### Block 2: Multi-Signal Router（完整 AdaRefine）
- **Claim tested**: C1 (完整)
- **Why this block exists**: 加入全部路由信号，验证完整 AdaRefine 的效果
- **Dataset/split**: WikiTQ 100 samples (先小样本)
- **Compared systems**: Baseline vs Judge-Skip-only vs Full AdaRefine
- **Metrics**: Accuracy, API calls, Total tokens, 各路由分支比例 (SKIP/LITE/FULL)
- **Setup details**:
  - SKIP: Judge says correct
  - LITE: chain_length ≤ 2 且无 group_by/sort_by → 仅 re-query
  - FULL: 其他所有情况
- **Success criterion**: 准确率下降 <0.5%，API 调用减少 ≥40%
- **Failure interpretation**: 如果提升不如 B1，说明额外信号引入了噪声
- **Priority**: MUST-RUN

### Block 3: Full Dataset A/B Test
- **Claim tested**: C1 (最终证据)
- **Dataset/split**: WikiTQ full 4344 samples
- **Compared systems**: Baseline (existing 84.05%) vs Full AdaRefine
- **Metrics**: Accuracy, Total tokens, API calls, per-sample 路由分布
- **Setup details**: 使用 `results/flattened/thought/wikitq/gpt-5.4`
- **Success criterion**: 准确率 ≥ 83.5%（允许 ≤0.5% 下降），API 调用减少 ≥35%
- **Failure interpretation**: 如果 API 减少但准确率下降 >1%，需要调保守阈值
- **Priority**: MUST-RUN (depends on B1, B2 success)

### Block 4: Signal Ablation（消融实验）
- **Claim tested**: C2
- **Why this block exists**: 证明每个路由信号都有独立贡献
- **Dataset/split**: WikiTQ 100 samples
- **Compared systems**:
  - Full AdaRefine (all signals)
  - No Judge (只用 chain + table features)
  - No chain_length (只用 Judge + table features)
  - No table_features (只用 Judge + chain)
- **Metrics**: Accuracy, API calls
- **Success criterion**: 去掉任意信号后效果显著变差
- **Priority**: MUST-RUN

### Block 5: TabFact Generalization
- **Claim tested**: C3
- **Why this block exists**: 证明方法不局限于 WikiTQ
- **Dataset/split**: TabFact full 2024 samples
- **Compared systems**: Baseline vs AdaRefine
- **Metrics**: Accuracy, API calls
- **Success criterion**: 准确率不下降，API 调用减少
- **Priority**: NICE-TO-HAVE

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Estimated Time | Risk |
|-----------|------|------|---------------|----------------|------|
| M0 | 实现 AdaRefine 路由器 | 代码实现 | 路由器代码完成 | 1-2 天 | 低 |
| M1 | B1: Judge-Skip sanity | 100 samples WikiTQ | 准确率下降 <1% | ~20 min | 中 |
| M2 | B2: Multi-signal | 100 samples WikiTQ | API 减少 ≥40% | ~20 min | 中 |
| M3 | B3: Full dataset | 4344 samples WikiTQ | 准确率 ≥83.5% | ~12h | 高 |
| M4 | B4: Signal ablation | 100 samples WikiTQ | 去掉信号后变差 | ~1h | 低 |
| M5 | B5: TabFact | 2024 samples | 准确率不下降 | ~8h | 中 |

### Decision Gates
- **M1→M2**: Judge-Skip 必须通过（准确率下降 <1%，API 减少 ≥20%）
- **M2→M3**: Multi-signal 必须通过（准确率下降 <0.5%，API 减少 ≥40%）
- **M3→M4**: Full dataset 无严重问题后才做消融
- **M1/M2 失败**: 重新设计路由策略，或考虑降级为仅 Judge-Skip 论文

## Risks and Mitigations
- **Judge 预检误判**: Judge 也用 LLM，本身有 ~2-3% 的误判率 → Judge 预检仅作为信号之一，不作为唯一判据
- **路由误分类导致精度损失**: 保守策略，LITE 通道仅处理极简单问题 → false positive 成本远低于 false negative
- **效率贡献不够新颖**: 强调"首个 multi-agent table reasoning 自适应路由"的独特定位 + 与 Flatten/TableAnalyzer 的集成
- **Token 记录不完整**: 已有 SOTA baseline 无 token 记录 → 用 100 样本 pilot 对比，full dataset 用 V-Critic 实验的 token 记录估算

## Final Checklist
- [x] Main paper tables are covered (B1-B4)
- [x] Novelty is isolated (B4 消融)
- [x] Simplicity is defended (B1 Judge-only 是最简版本)
- [x] Frontier contribution is justified or explicitly not claimed (无 frontier model)
- [x] Nice-to-have runs are separated (B5 TabFact)

## Implementation Notes

### 路由器实现位置
- 新建 `refine/TableQA/utils/router.py` — 路由器逻辑
- 修改 `refine/TableQA/main_tree_based.py` — 集成路由决策
- 修改 `refine/TableQA/utils/controller.py` — 支持 SKIP/LITE/FULL 模式

### 路由信号实现（零 LLM 成本）
```python
def estimate_complexity(sample, thought_result):
    score = 0

    # Signal 1: Judge 预检（需要 1 次 LLM 调用）
    if thought_result.get("judge") == "[Correct]":
        return "SKIP"  # 最强信号，直接跳过

    # Signal 2: Chain 复杂度
    chain = thought_result.get("chain", [])
    ops = [op["operation_name"] for op in chain]
    if len(ops) <= 2 and "group_column" not in ops and "sort_column" not in ops:
        score += 2  # 简单链 → 倾向 LITE

    # Signal 3: 表格特征
    table = thought_result.get("table_text", [])
    if len(table) > 0 and len(table) <= 5:  # rows ≤ 4
        headers = table[0]
        if len(headers) <= 4:
            score += 1  # 小表格 → 倾向 LITE

    # Signal 4: V-Critic 验证结果（如果有）
    # verify_chain() 的结果可以降级为路由信号
    # 如果有 FAIL → score -= 2 (倾向于 FULL)

    if score >= 2:
        return "LITE"
    return "FULL"
```

### LITE 模式实现
LITE = 只跑 simple_query（1 次 LLM 调用），不跑 Critic + Refiner + Judge：
```python
if route == "LITE":
    result = simple_query_cot_original(sample, table_info, llm, llm_options)
    sample["pred_answer"] = result
    # 跳过 Critic/Controller/Judge
```
