# G-CRAFT 小模型实验最终提案

**状态**：ready_for_experiment_bridge  
**目标仓库**：`/home/cocopink/code/Table-Critic`  
**主模型**：Qwen3.5-4B、Qwen3.5-9B  
**主任务**：WikiTQ；边界任务：TabFact

## 1. 研究定位

G-CRAFT 不再定位为对商用级大模型的普遍增强，而定位为一种无需训练的小模型表格推理补偿框架：通过表格证据重排、schema anchor 和错误路由修正，缓解 4–9B 模型的证据遗漏、schema 漂移和错误级联。

核心问题是：在严格冻结测试记忆、固定解码预算和完整测试集分母后，G-CRAFT 是否对 Qwen3.5-4B/9B 比对 27B 带来更大的边际收益。

## 2. 以当前代码为准的方法定义

G-CRAFT 由三个实际存在的阶段组成：

1. **ATGO preprocessing**：构造表格图并使用 question-guided PPR 对行列证据重排，可选 column smoothing 和 graph hint。
2. **Initial reasoning**：Chain-of-Table 生成操作链与初始答案；Clarifier 通过规则抽取 schema anchor。
3. **Controller-routed refinement**：Judge、Critic、错误树检索和 Controller 在有限轮次内选择诊断、执行、链修正、查询修正或停止。

当前可信表述：

- graph hint 与 schema anchor 已进入部分 refinement operation；
- Controller 支持错误路由、blueprint/few-shot 检索和在线错误树更新；
- 主实验将错误树冻结，只在附录研究 online memory。

当前不得宣称：

- graph hint/schema anchor 已被初始 Planner 和所有 Critic/Controller prompt 共同消费；
- 已实现实例级 `ConstructPlan`；
- graph hint 包含论文定义的完整局部边集合；
- 测试中在线更新仍属于严格 inductive evaluation。

论文若保留上述强表述，必须先补实现并单独消融；本轮实验默认采用代码已支持的较窄定义。

## 3. 模型与部署

| 角色 | 模型 | 精度/设备 | 用途 |
|---|---|---|---|
| 本机尺度下界 | Qwen3.5-2B | BF16 或量化，8GB GPU | smoke、尺度下界 |
| 核心本机模型 | Qwen3.5-4B | 4-bit，8GB GPU | M0/M1 与主消融 |
| 核心复现模型 | Qwen3.5-9B | 统一精度，≥16GB GPU | 主表与关键消融 |
| 尺度上界 | Qwen3.5-27B | 更大显存或多卡 | 仅通过 Gate 后运行 |

所有主实验显式关闭 thinking，temperature=0，固定上下文、最大输出 token、失败处理和表格序列化。不同精度结果不得用于纯参数尺度归因。

## 4. 首轮实现范围

`experiment-bridge` 首轮只实现评测可信度和可复现性修复：

1. 固定分母，异常、空输出和超时计错；
2. frozen-memory 开关及 hash 校验；
3. 完整测试集路径和 error-only 防误用；
4. model/config-aware cache 与输出隔离；
5. Qwen3.5 thinking 的后端一致控制；
6. 逐样本 JSONL、汇总 JSON/CSV、运行 manifest；
7. 2B/4B smoke 与 4B 500 条 pilot。

不在首轮重写整体架构，不添加未经主实验需要验证的模块。

## 5. 决策标准

- **GO**：4B pilot 相对最强同预算基线提升至少 3 pp，且评估/记忆/缓存检查全部通过；随后部署 9B。
- **NARROW**：总体增益较小，但预注册的长表、schema 歧义或多步子集有稳定收益；论文收窄作用范围。
- **STOP**：固定分母、冻结记忆和等预算后不优于 Table-Critic；停止扩展 27B 和大规模重复。

## 6. 代码—论文同步规则

实验结果只能支撑真实进入执行路径的组件。任何方法图、公式或算法步骤在写入主张前，必须能定位到入口脚本、数据字段、消费函数和结果日志。详细运行矩阵见 `EXPERIMENT_PLAN.md`，逐 run 状态见 `EXPERIMENT_TRACKER.md`。
