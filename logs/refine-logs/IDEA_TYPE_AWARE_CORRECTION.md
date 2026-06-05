# Idea Proposal: Type-Aware Self-Correction for Multi-Agent Table Reasoning

**Date**: 2026-05-21
**Status**: DRAFT — 需要进一步验证

## Problem Anchor

Table-Critic (ACL 2025) 的 Refine 阶段对所有错误样本使用统一的 Critic 诊断策略（"盲诊"），Critic 收到的反馈只有粗粒度的 outcome-level 信号（[Correct]/[Incorrect]），需要"盲猜"错误步骤。这导致：
- Thought→Refine 在 WikiTQ 上仅 +2%（82%→84%），修正效率极低
- V-Critic（确定性结构验证）覆盖面极低（~6-7%），因为 93% 的错误是语义级的
- 不同类型的错误（实体识别、数值计算、排序比较）需要完全不同的修正方法，但当前系统不加区分

## Core Insight

**ACL Findings 2024 的关键发现**："LLMs Cannot Find Reasoning Errors, But Can Correct Them Given the Error Location"。

Table-Critic 的错误分析（874 个 WikiTQ 错误）揭示了一个清晰的错误类型分布：
- 数值计算错误：39.1%（计数/求和/算术）
- 实体识别错误：29.3%（选错行或列）
- 排序比较错误：24.3%（排序方向混淆）
- 其他：6.7%

这些错误类型的修正策略截然不同，但当前系统用同一种 Critic prompt 处理所有错误。

## Method Thesis

> 在 Table-Critic 的 Refine 阶段引入**错误类型感知的分层修正框架**（Type-Aware Correction Framework），通过零 LLM 成本的结构信号对错误进行初步分类，然后为每类错误路由到专用的修正策略，弥合"检测错误"和"修复错误"之间的鸿沟。

## 三个层次的贡献

### 层次 1：错误类型分类器（Error Type Classifier）

零 LLM 成本的启发式分类，基于链结构特征：

```python
def classify_error(sample, chain, judge_result):
    ops = [op["operation_name"] for op in chain]

    # 数值计算类：含 add_column 或 group_column 聚合
    if "add_column" in ops or ("group_column" in ops and "count" in question.lower()):
        return "NUMERICAL"

    # 排序比较类：含 sort_column + max/min/first/last 等关键词
    if "sort_column" in ops and any(kw in question for kw in ["most", "least", "first", "last", "highest", "lowest"]):
        return "SORTING"

    # 实体识别类：含 select_row/select_column 但无复杂操作
    if "select_row" in ops or "select_column" in ops:
        return "ENTITY"

    return "OTHER"
```

### 层次 2：类型专用修正策略（Type-Specific Correctors）

为每类错误设计专用的 Refiner prompt：

| 错误类型 | 修正策略 | 关键 prompt 差异 |
|----------|---------|-----------------|
| NUMERICAL | 重新执行聚合计算，强调数值精度 | "Focus on correct counting/aggregation. Verify your arithmetic." |
| ENTITY | 列名模糊匹配 + 实体重选，利用 TableAnalyzer hint | "Re-examine which column/row matches the question entity. Use column normalization hints." |
| SORTING | 验证排序方向（ASC/DESC），重新排序 | "Determine the correct sort direction from the question. Check ascending vs descending." |
| OTHER | 标准 Critic + Refiner 流程 | 现有 baseline |

### 层次 3：自适应路由（Adaptive Router）

结合错误类型分类和复杂度估计，决定修正策略：
- **SKIP**：Judge says correct → 跳过（复用现有逻辑）
- **TYPE-LITE**：简单错误 + 明确类型 → 专用修正器（1 次 LLM 调用）
- **TYPE-FULL**：复杂错误 → 专用修正器 + Critic 验证
- **FULL**：无法分类 → 标准 Controller 流程

## 竞品分析

| 工作 | 领域 | 错误分类 | 专用修正 | 多智能体 |
|------|------|---------|---------|---------|
| StepCo (ACL 2025) | 数学推理 | ✅ 有分类 | ✅ prompt 差异化 | ❌ 单 LLM |
| CORRECT (ICLR 2026) | 通用 MAS | ✅ error schema | ❌ 只定位不修正 | ✅ 多智能体 |
| ReVISE (ICML 2025) | 通用 QA | ❌ 无分类 | ❌ 通用自纠错 | ❌ 单 LLM |
| V-Critic (ours) | 表格推理 | ❌ 无分类 | ❌ 统一 Critic | ✅ 多智能体 |
| **本方案** | **表格推理** | **✅ 类型分类器** | **✅ 专用修正器** | **✅ 多智能体博弈** |

**本方案是首个在表格推理领域实现"错误类型分类→专用修正器分派"的工作，且是唯一同时具备三个能力（分类+专用修正+多智能体协作）的系统。**

## 零微调约束下的实现

所有组件均为零 LLM 成本或 1 次 LLM 调用：
- 错误类型分类器：纯启发式规则，基于 chain 操作类型和问题关键词
- 专用修正器：不同类型的 Refiner prompt 模板
- 路由器：分类结果 + 链复杂度 + 表格特征
- 结构验证：复用 V-Critic 代码作为辅助信号

## 关键 Claims

1. **C1**：错误类型感知修正比统一修正更有效（WikiTQ 准确率显著提升）
2. **C2**：消融实验证明每个组件（分类器、专用修正器、路由器）的贡献
3. **C3**：方法在 TabFact 上同样有效（跨数据集泛化）

## Must-Run 实验

### Block 1: 错误分类有效性（Sanity Check）
- 手动标注 100 个错误样本的错误类型
- 验证启发式分类器的准确率
- 分类器目标：>80% 分类准确率

### Block 2: 类型专用修正 vs 统一修正（Main Result）
- WikiTQ 100 samples: Baseline vs Type-Aware Correction
- WikiTQ 4344 samples: Baseline vs Type-Aware Correction
- 消融：去掉分类器（随机分派）、去掉专用修正器（统一 prompt）

### Block 3: 路由效率（AdaRefine 集成）
- TYPE-LITE vs TYPE-FULL vs FULL 的准确率和 API 成本
- 路由信号消融

### Block 4: 跨数据集（TabFact）
- TabFact full dataset: Baseline vs Type-Aware Correction

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 启发式分类器不够准确 | 先手动标注验证，允许 fallback 到 FULL |
| 专用 prompt 改进有限 | 消融实验量化，即使小幅提升也有价值 |
| 与 StepCo 过于相似 | 强调表格推理领域的独特性（结构信号 + 多智能体） |
| 零微调约束限制了分类器能力 | 分类器只做粗分（4 类），不需要高精度 |

## 与已有工作的关系

- **V-Critic**（已实现）：降级为辅助信号源，结构验证失败 → 倾向 NUMERICAL/SORTING 类型
- **AdaRefine**（已实现）：路由器整合到 TYPE-LITE/TYPE-FULL 决策中
- **TableAnalyzer**（已实现）：ENTITY 类型修正时消费 column_normalizations hint
- **Error Tree**（已有）：作为专用修正器的知识库，检索相关 Blueprint

## References
- StepCo (ACL 2025): arXiv 2410.12934
- CORRECT (ICLR 2026): openreview.net/forum?id=6skwd1QtTO
- "LLMs Cannot Find Reasoning Errors..." (ACL Findings 2024): aclanthology.org/2024.findings-acl.826
- ReVISE (ICML 2025): arXiv 2502.14565
- CRITIC (ICLR 2024): openreview.net/forum?id=Sx038qxjek
- VERGE (arXiv 2026): arXiv 2601.20055
