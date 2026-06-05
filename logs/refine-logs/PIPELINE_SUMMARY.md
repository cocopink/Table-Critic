# Pipeline Summary

**Problem**: Table-Critic Refine 阶段对所有样本无差别处理，正确样本浪费 API 调用
**Final Method Thesis**: 自适应路由（AdaRefine）根据问题复杂度决定 SKIP/LITE/FULL 修正策略，降低 40%+ API 成本
**Final Verdict**: RETHINK (V-Critic 已证伪，转向 AdaRefine)
**Date**: 2026-05-21

## V-Critic 结论
- 全量实验：84.05% → 84.23%（+0.18%，对比不公平）
- 理论天花板：<1% 绝对提升
- **判定：V-Critic 不适合作为独立贡献，降级为路由信号源**

## 推荐方向：AdaRefine
- Dominant contribution: 首个将自适应路由引入多智能体表格推理
- Explicitly rejected: RL PRM, VLM 多模态, SPIN 对抗, 纯 V-Critic
- V-Critic 残余价值: 验证器结果作为路由信号之一

## Must-Prove Claims
1. WikiTQ 准确率损失 <0.5%，API 成本降低 40%+
2. 路由信号消融证明各组件贡献
3. TabFact 跨数据集泛化

## First Runs to Launch
1. 实现 Judge 预检路由器（最简单有效的信号）
2. WikiTQ 100 samples 快速验证 SKIP 策略效果
3. WikiTQ full dataset A/B 对比

## Main Risks
- 路由误判导致准确率下降 → 保守策略 + fallback
- 效率贡献可能不够新颖 → 强调首个 multi-agent table reasoning 路由

## Next Action
- 确认方向后实现 AdaRefine 路由器
