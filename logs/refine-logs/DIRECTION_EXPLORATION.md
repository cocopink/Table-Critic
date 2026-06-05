# Research Direction Exploration

**Date**: 2026-05-21
**Status**: 探索中

## 已否决方向

| 方向 | 评分 | 否决原因 |
|------|------|---------|
| V-Critic | ~4/10 | 结构验证覆盖率极低（~6-7%），天花板 <1% |
| AdaRefine | ~5/10 | LITE 分支几乎不触发，本质上只是 Judge-Skip |
| Type-Aware Correction | 5.7/10 | 贡献质量 4 分，本质是 prompt engineering |

## 候选方向

### 方向 1: 难度感知选择性精炼（Difficulty-Aware Selective Refinement）

**核心洞察**: MAGICORE (EMNLP 2025) 证明统一精炼所有样本会损害性能（-3.8%~-5.2%），简单样本被"过度修正"反而引入错误。

**方案**:
- 难度评估器：Easy → SKIP, Medium → 1 轮精炼, Hard → 2 轮 + 操作重构
- 步骤级验证：Critic 对每个操作步骤打置信度，只对低置信度步骤触发重执行
- 精炼终止判据：置信度 > 阈值则提前终止

**优势**: 风险最低，与现有架构最契合
**劣势**: 可能不够新颖（MAGICORE 已在数学推理做了类似的事）
**预估评分**: 6.5-7/10

### 方向 2: 循环对抗式批评强化（Cyclic Adversarial Critique）

**核心洞察**: CAP-CoT (arXiv 2604.23270) 用循环对抗 prompt 让 LLM 生成"看似合理但刻意包含错误"的推理步骤，然后训练模型抵抗这些错误。**零训练，纯 prompting。**

**方案**:
- Phase 1: Critic 不仅诊断真实错误，还基于错误树生成"对抗性错误推理链"（adversarial chains）
- Phase 2: Refiner 尝试修正这些对抗性错误 → 形成更强的纠错能力
- Phase 3: 对抗性错误 + 真实错误混合训练 Refiner 的 prompt
- 利用 Table-Critic 的错误树（few_shot_critic.json）作为对抗样本源

**优势**: 零训练、纯 prompting、与错误树天然结合、概念新颖
**劣势**: 对抗性错误的质量和多样性难保证；可能需要多轮迭代才能看到效果
**预估评分**: 7-7.5/10

### 方向 3: Test-Time 对比规则蒸馏（Test-Time Contrastive Rule Distillation）

**核心洞察**: TF-TTCL (arXiv 2604.13552) 在零梯度条件下通过对比正负推理路径，提炼推理规则，GSM8K 相对错误率降低 41-54%。

**方案**:
- Explore: 多角色生成不同操作路径（Teacher 正确路径 + Tutor 故意犯错路径）
- Reflect: 对比正负路径差异，提炼"表格推理专用对比规则"（如"含'最大值'时应用 sort_by(desc)"）
- Steer: 将规则注入 Thought/Refine prompt，跨样本复用

**优势**: 新颖性最高（表格推理领域空白）、规则可解释、记忆演化
**劣势**: 工程量较大、规则质量依赖 LLM 对比能力
**预估评分**: 7-8/10

### 组合方案: 方向 1 + 方向 2

- 方向 1 解决"要不要精炼"的问题（资源分配 + 避免过度修正）
- 方向 2 解决"精炼时怎么变强"的问题（对抗性训练增强 Refiner）
- 两者正交，可独立消融

## 待验证问题

1. 难度评估器的准确率能否达到可用水平？
2. 对抗性错误链的质量和多样性如何保证？
3. Table-Critic 的错误树（few_shot_critic.json）包含的错误模式是否足够丰富？
4. MAGICORE 的"统一精炼有害"发现在表格推理上是否成立？
