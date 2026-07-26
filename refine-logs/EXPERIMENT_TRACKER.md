# 小模型实验 Tracker

> 状态枚举：`TODO / RUNNING / DONE / BLOCKED / CUT`。主结果必须记录逐样本输出路径、manifest 路径和 memory hash。

| Run ID | Milestone | 目的 | 系统 / 变量 | 数据 | 指标 | 优先级 | 状态 | Gate / 备注 |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | evaluator 固定分母测试 | Thought/Refine evaluator | 合成成功、异常、空输出样本 | coverage=100%，异常计错 | MUST | TODO | bare except 不得缩小分母 |
| R002 | M0 | 冻结测试记忆 | Full pipeline, frozen memory | WikiTQ/TabFact 各 10 条 | run 前后 hash | MUST | TODO | hash 必须一致 |
| R003 | M0 | 4B smoke | Qwen3.5-4B 4-bit + G-CRAFT | WikiTQ/TabFact 各 50 条 | parse rate、acc、tokens、samples/h | MUST | TODO | 本机 RTX 5060 8GB；parse failure <2% |
| R004 | M0 | 2B smoke | Qwen3.5-2B + G-CRAFT | WikiTQ/TabFact 各 50 条 | parse rate、acc、tokens、samples/h | MUST | TODO | 本机尺度下界与吞吐预算 |
| R005 | M0 | cache 隔离 | 同模型重复 10 条 | WikiTQ | output path、cache key、memory hash | MUST | TODO | variant/seed 不得互相覆盖 |
| R006 | M1 | 小模型方向 pilot | Qwen3.5-4B × Direct/CoT/Table-Critic/G-CRAFT | WikiTQ 分层 500 | acc、paired Δ、tokens | MUST | TODO | 本机执行；Full vs strongest ≥3 pp 为强 GO |
| R007 | M1 | 小模型方向 pilot | Qwen3.5-9B × Direct/CoT/Table-Critic/G-CRAFT | WikiTQ 同 500 | acc、paired Δ、tokens | MUST | TODO | ≥16GB GPU；不得用 CPU offload 做效率比较 |
| R008 | M1 | thinking 公平性 | Qwen3.5-4B/9B non-thinking vs thinking baseline | WikiTQ 同 500 | acc、reasoning tokens、latency | MUST | TODO | 请求体显式设置 thinking；确定主文 decoding mode |
| R009 | M2 | 主表 4B WikiTQ | 5 systems × Qwen3.5-4B | WikiTQ full 4,344 | acc/CI/tokens/calls/latency | MUST | TODO | 固定 denominator=4,344 |
| R010 | M2 | 主表 9B WikiTQ | 5 systems × Qwen3.5-9B | WikiTQ full 4,344 | acc/CI/tokens/calls/latency | MUST | TODO | 固定 denominator=4,344；远程 GPU |
| R011 | M2 | 主表 4B TabFact | 5 systems × Qwen3.5-4B | TabFact full 2,024 | acc/CI/tokens/calls/latency | MUST | TODO | 辅助边界任务 |
| R012 | M2 | 主表 9B TabFact | 5 systems × Qwen3.5-9B | TabFact full 2,024 | acc/CI/tokens/calls/latency | MUST | TODO | 退化不得超过 1 pp；远程 GPU |
| R013 | M3 | 2B 尺度下界 | strongest baseline vs Full | WikiTQ full | Δacc、VRAM、latency | MUST | TODO | 可在本机执行 |
| R014 | M3 | 27B 尺度上界 | strongest baseline vs Full | WikiTQ full | Δacc、VRAM、latency | MUST | TODO | 仅 M2 通过后启动；可降为 appendix |
| R015 | M3 | 4B 累加链 | Thought → +ATGO → +Anchor → +Controller | WikiTQ/TabFact full | acc、cost、wrong→right | MUST | TODO | 最小充分系统 |
| R016 | M3 | 4B 删除消融 | Full/w-o ATGO/Anchor/Controller/Plan | WikiTQ/TabFact full | paired Δ、CI | MUST | TODO | 回应组件拼接质疑 |
| R017 | M3 | 9B 关键消融 | Full/w-o Anchor/w-o Controller | WikiTQ full | paired Δ、CI | MUST | TODO | 检查机制可迁移性 |
| R018 | M3 | P1/P2 独立性 | baseline/P1/P2/P1+P2 | WikiTQ full, Qwen3.5-4B | acc、evidence coverage | MUST | TODO | 禁止用 error_data 总体 acc |
| R019 | M3 | 等预算对照 | Table-Critic extra-refine vs Full | WikiTQ full, 4B/9B | acc at equal tokens/calls | MUST | TODO | 排除纯算力增益 |
| R020 | M4 | 最终重复 4B | strongest baseline、Full × 3 runs | WikiTQ/TabFact full | mean/std、paired CI | MUST | TODO | 后端确定时可改为 bootstrap-only |
| R021 | M4 | 最终重复 9B | strongest baseline、Full × 3 runs | WikiTQ/TabFact full | mean/std、paired CI | MUST | TODO | 保存逐样本交集 |
| R022 | M4 | 效率画像 | R009–R021 日志聚合 | 两数据集 | peak VRAM、P50/P95、tokens | MUST | TODO | 同硬件同口径 |
| R023 | M5 | 错误分桶 | 复用主实验输出 | WikiTQ/TabFact | 长表/操作/答案类型 | MUST | TODO | 不新增模型调用 |
| R024 | M5 | 案例 | 2 成功 + 1 失败 | WikiTQ | 证据/anchor/route 轨迹 | MUST | TODO | 主文定性图 |
| R025 | M5 | 跨代复现 | Qwen3-4B/8B strongest vs Full | WikiTQ full | acc、tokens、latency | NICE | TODO | 不与 Qwen3.5 混画尺度曲线 |
| R026 | M5 | online memory 敏感性 | frozen vs online × 3 orders | WikiTQ 500 或 full | mean/range、order effect | NICE | TODO | 仅附录 |
| R027 | M5 | thinking + G-CRAFT | Qwen3.5-4B/9B | WikiTQ 500 | acc、tokens、latency | NICE | TODO | 若 non-thinking 已充分则 CUT |

## 首批启动顺序

1. R001：确认 evaluator 对异常输出的处理。
2. R002：确认测试期间 memory 完全冻结。
3. R003/R004：获得本机 4B/2B 的格式成功率与真实吞吐。
4. R006：本机完成 500 条 WikiTQ 4B pilot；通过 Gate 后，R007 在更大显存设备复现 9B。
