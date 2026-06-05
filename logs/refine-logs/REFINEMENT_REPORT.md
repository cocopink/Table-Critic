# Refinement Report

**Problem**: Table-Critic Refine 阶段修正效率极低（+2%），Critic 诊断信息不充分
**Initial Approach**: AdaRefine（自适应路由降低 API 成本）→ 用户认为贡献点太小 → 转向错误类型感知修正
**Date**: 2026-05-21
**Rounds**: 2 / 5
**Final Score**: 6.6/10
**Final Verdict**: CONDITIONAL ACCEPT

## Problem Anchor

Table-Critic 的 Critic 只能看到推理链的最终子表（静态快照），看不到操作步骤的中间表格状态变化，导致错误定位不准确。Critic 输出是自由文本，Refiner 无法针对性地选择修正策略。

## Output Files
- Review summary: `refine-logs/round-1-review.md`, `refine-logs/round-2-review.md`
- Final proposal: `refine-logs/FINAL_PROPOSAL.md`
- Initial idea: `refine-logs/IDEA_TYPE_AWARE_CORRECTION.md`
- Round 0 proposal: `refine-logs/round-0-initial-proposal.md`
- Round 1 refinement: `refine-logs/round-1-refinement.md`

## Score Evolution

| Round | Problem Fidelity | Method Specificity | Contribution Quality | Frontier Leverage | Feasibility | Validation Focus | Venue Readiness | Overall | Verdict |
|-------|------------------|--------------------|----------------------|-------------------|-------------|------------------|-----------------|---------|---------|
| 1     | 7                | 8                  | 4                    | 5                 | 6           | 5                | 4               | 5.85    | REVISE  |
| 2     | 7                | 8                  | 6                    | 6                 | 7           | 7                | 5               | 6.6     | ACCEPT  |

## Round-by-Round Resolution

| Round | Main Concerns | What Changed | Solved? |
|-------|---------------|-------------|---------|
| 1     | "换个 prompt"质疑；中间表格被低估；循环依赖；错误分类粒度 | 主贡献从"错误类型路由"转向"中间表格注入+两阶段诊断"；设计两阶段解决循环依赖；对齐错误树 | Partial — 中间表格注入作为主贡献的叙事仍需在论文中强化 |
| 2     | "两阶段"叙事不够新颖；路由粒度可疑；+2%天花板 | 叙事锚定在"table diff"而非"两阶段"；增加 5 桶路由消融建议 | ✅ 核心改进完成 |

## Final Proposal Snapshot

- **核心 insight**: Critic 当前只能看"最终快照"，应该看"操作前后的 diff"（类比程序调试的 diff 视图）
- **主贡献**: Operation-Level Table Diff（操作级表格 Diff）——两阶段诊断让 Critic 看到中间表格状态
- **辅助贡献**: 基于诊断信号的智能修正路由（error_route → 专用 Refiner 模板）
- **零微调**: 所有组件都是 prompting 层面修改，~345 行新代码
- **关键消融**: 5 个配置（A-E）层层递进，足以回应"只是 prompt engineering"质疑

## Method Evolution Highlights

1. **最重要的转变**: 从"错误类型分类"转向"信息增强诊断" — 中间表格状态注入是唯一真正增加了新信息的改动
2. **最关键的解决**: 两阶段设计解决了循环依赖（阶段 1 粗定位 → 阶段 2 注入中间表格）
3. **最有价值的消融**: A-E 五配置消融设计，特别是 C vs A（信息增量本身的价值）和 D vs B（结构化路由 vs enriched prompt）

## Pushback Log

| Round | Reviewer Said | Author Response | Outcome |
|-------|---------------|-----------------|---------|
| 1 | "结构化输出+路由就是4个prompt" | 重新定位主贡献为中间表格注入；路由降为辅助 | Accepted — 贡献权重重新分配 |
| 1 | "中间表格注入被低估" | 提升为主贡献，引入 table diff 叙事 | Accepted — 成为提案核心 |
| 1 | "循环依赖" | 两阶段设计解决 | Accepted — 干净的解决方案 |
| 1 | "四分类太粗" | 对齐现有错误树 | Accepted — 复用已有知识 |
| 2 | "两阶段叙事不新颖" | 锚定在 table diff 而非两阶段 | Accepted — 叙事重构 |

## Remaining Weaknesses

1. **+2% 天花板**: 即使 table diff 有效，整体提升幅度可能有限。TabFact 验证是关键补充证据。
2. **Critic 分类可靠性**: 需 pre-flight 验证 Critic 能否可靠利用 table diff 做精细诊断。
3. **发表定位**: 作为 Table-Critic 的后续改进（不是全新框架），需要审稿人认可 incremental contribution 的价值。

## Next Steps

1. Pre-flight validation: 手动检查 50 个 Stage 2 Critic 输出，验证格式遵循率和分类质量
2. 实现 Stage 2 诊断逻辑（`get_cot_for_critic_stage2()` + `critic_stage2_exec()`）
3. 实现 Type-Aware Router 和 Refiner 模板
4. 运行 A-E 消融实验（100 samples pilot）
5. 如果 pilot 结果 positive → 全量 WikiTQ + TabFact

**Suggested next skill**: `/experiment-plan` to turn this proposal into a detailed execution-ready experiment roadmap
