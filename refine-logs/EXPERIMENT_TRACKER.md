# Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|--------|-----------|---------|------------------|-------|---------|----------|--------|-------|
| R001 | M1 | Judge-Skip sanity | Baseline (standard Refine) | WikiTQ 100 | acc, tokens | MUST | DONE | acc=82%, 285 API calls, 937K tokens |
| R002 | M1 | Judge-Skip sanity | Full AdaRefine (all signals) | WikiTQ 100 | acc, tokens, route dist | MUST | RUNNING | SKIP/LITE/FULL 三级路由，v2 阈值(chain<=3, complex_ops<=1, rows<=10) |
| R003 | M2 | Multi-signal | Full AdaRefine (all signals) | WikiTQ 100 | acc, tokens, route dist | MUST | TODO | SKIP/LITE/FULL 三级路由 |
| R004 | M3 | Full dataset | Baseline (existing 84.05%) | WikiTQ 4344 | acc | MUST | TODO | 已有结果 |
| R005 | M3 | Full dataset | Full AdaRefine | WikiTQ 4344 | acc, tokens, route dist | MUST | TODO | depends on R001-R003 |
| R006 | M4 | Signal ablation | No-Judge variant | WikiTQ 100 | acc, tokens | MUST | TODO | |
| R007 | M4 | Signal ablation | No-chain variant | WikiTQ 100 | acc, tokens | MUST | TODO | |
| R008 | M4 | Signal ablation | No-table variant | WikiTQ 100 | acc, tokens | MUST | TODO | |
| R009 | M5 | TabFact gen | Baseline | TabFact 2024 | acc, tokens | NICE | TODO | |
| R010 | M5 | TabFact gen | AdaRefine | TabFact 2024 | acc, tokens | NICE | TODO | |

## Notes
- R001 基线: 使用 `test/results/flattened/thought/wikitq/gpt-5.4-pilot100/` 的 Thought 结果，跑 `use_verifier=False`
- R001 基线数据: acc=82%, 285 API calls, 937K tokens
- R002 = Full AdaRefine (SKIP/LITE/FULL). v1 阈值太严(chain<=2,rows<=5,cols<=4)导致97% FULL，调整为 v2(chain<=3,complex_ops<=1,rows<=10)
- 路由器文件: `refine/TableQA/utils/router.py`
- LITE 模式: 跳过 Critic/Controller，直接用 simple_query_cot_original 做 1 次 LLM 调用
- SKIP 模式: 复用 controller_main_loop 已有的 Judge-Skip 逻辑
- R002 和 R003 合并为同一个实验（Full AdaRefine = M2 milestone）
- M1→M2 的决策门：Judge-Skip 准确率下降 <1% 且 API 减少 ≥20%
- M2→M3 的决策门：Full AdaRefine 准确率下降 <0.5% 且 API 减少 ≥40%
