# 小模型视角下的 G-CRAFT 对比实验计划

**问题**：现有稿件以 32B、72B 和商用闭源模型为主，但 G-CRAFT 在强模型上的边际收益较小，难以支撑“普遍增强大模型”的叙事。

**方法主张**：G-CRAFT 的主要价值不是继续抬高强模型上限，而是通过显式证据组织、schema anchor 和 controller-routed refinement，补偿 4–9B 小模型在表格结构理解与自纠错上的能力缺口。

**日期**：2026-07-26

## 一、建议的叙事调整

### 1.1 从“强模型通用增强”改为“小模型能力补偿”

论文主线建议改成：

> 小语言模型具备低成本、可本地部署和数据可控的优势，但在复杂表格推理中更容易发生证据遗漏、schema 漂移和错误级联。G-CRAFT 通过无需训练的结构化推理编排，在 Qwen3.5-4B/9B 上获得更明显的收益，并缩小其与更大模型之间的差距。

当前证据已经给出明确动机：在已有消融中，14B 模型移除结构化修正方案或模式锚点后下降约 2.69–4.56 个百分点，而 32B 上仅下降 0.10–0.83 个百分点。这更符合“模型越小，越需要外部结构约束”的机制解释。

### 1.2 论文中模型的角色重新分配

| 角色 | 推荐模型 | 放置位置 | 用途 |
|---|---|---|---|
| 核心小模型 | Qwen3.5-4B、Qwen3.5-9B | 主表、主图、主消融 | 使用最新同代 dense checkpoint；9B 是该系列最接近原 8B 目标的档位 |
| 尺度参照 | Qwen3.5-2B、Qwen3.5-27B | 尺度曲线；27B 可移至附录 | 验证收益是否随参数规模增大而减弱 |
| 跨代稳健性 | Qwen3-4B、Qwen3-8B | 附录 | 排除结论只对 Qwen3.5 成立 |
| 商用/超大模型 | 现有 GPT、GLM、Qwen2.5-72B 结果 | 附录或局限性 | 说明方法边界，不再承担主结论 |

Qwen3.5 官方开放权重模型包含 2B、4B、9B、27B 等 dense 档位，主实验使用 4B/9B，尺度曲线使用 2B/4B/9B/27B。旧 Qwen3-4B/8B 只用于跨代复现，不与 Qwen3.5 混成一条参数缩放曲线。

### 1.3 任务重心

- **WikiTQ 是主任务**：多步问答更符合结构组织和错误修正的作用点，现有增益也更稳定。
- **TabFact 是边界任务**：用于说明在接近性能上限的事实验证上不破坏性能，并避免把温和增益包装成主要发现。
- 暂不新增数据集。先用完整、可信的 WikiTQ/TabFact 结果把新主张证明干净；更多数据集属于后续扩展。

## 二、Claim Map

| Claim | 为什么重要 | 最低可信证据 | 关联实验块 |
|---|---|---|---|
| C1：G-CRAFT 对 Qwen3.5-4B/9B 的提升显著大于对 27B 的提升 | 这是新叙事的核心机制结论 | 同一 Qwen3.5 代际、相同 prompt/解码/数据协议下的 2B/4B/9B/27B 尺度曲线；报告逐样本配对置信区间 | B1、B2 |
| C2：小模型收益来自结构化组件，而不是更多 token、测试集记忆或单纯增加调用次数 | 防止“小模型只是被堆算力”的反驳 | 冻结记忆的严格 inductive 评估；组件消融；等 token/等调用预算对照；准确率-延迟-显存曲线 | B2、B3、B4 |
| Anti-claim：收益不是 error-only 子集选择偏差 | 当前矩阵默认使用基线错误子集，风险很高 | 主结论全部在官方完整 test 上；error_data 只做诊断，不报告总体 accuracy | B1、B3 |
| Anti-claim：收益不是 Qwen3.5 thinking mode 或解码预算不一致造成 | Qwen3.5 默认启用 thinking，若不显式固定会产生混杂 | 所有主对比显式关闭 thinking，并固定 temperature、最大输出长度和失败处理；thinking mode 仅做附录对照 | B1、B4 |

## 三、Paper Storyline

### 主文必须证明

1. 在 Qwen3.5-4B/9B 上，G-CRAFT 相比最强同预算基线稳定提升 WikiTQ，并在 TabFact 上不显著退化。
2. 增益沿 Qwen3.5-2B/4B/9B/27B 尺度增大而收缩，说明框架是在补偿小模型能力缺口，而不是普遍抬高所有模型上限。
3. Qwen3.5-4B + G-CRAFT 能以更低显存或更低部署成本接近 Qwen3.5-9B 的强推理基线。
4. 关键收益来自 schema anchor 与 controller refinement；图重排只作为辅助证据组织机制，不单独扩张创新性。

### 附录可以支持

- Qwen3-4B/8B 跨代复现。
- Qwen3.5 thinking mode 对照。
- 商用模型与 27B/72B 的既有结果，作为方法边界。
- online-memory transductive setting，并报告不同样本顺序的敏感性。
- gamma 完整扫描、详细错误路由和案例。

### 明确删减

- 不再把 GPT-5.4、GLM5.1、Qwen2.5-72B 并列放在核心主表中。
- 不在主文保留 End-to-End、Few-shot、CoT、CoT-Consistency、Reactable、MACT 等过长列表。
- 不用基线错误子集上的 accuracy 支撑总体性能结论。
- 不宣称 G-CRAFT 在所有模型、所有表格任务上均有效。

## 四、统一评测协议（必须先冻结）

### 4.1 数据与记忆

- 主结果使用完整官方测试集：TabFact 2,024 条、WikiTQ 4,344 条。
- `error_data.jsonl`（165/897 条）仅用于失败诊断和开发，不进入主 accuracy 表。
- 主结果采用 **strict inductive setting**：经验库仅由 train/dev 构建，每个模型、每个方法从相同只读快照启动；测试过程中禁止 `update_error_tree()` 写回。
- online-memory 仅作为附录实验，并至少用 3 个测试顺序报告均值与范围。
- 每个系统保存逐样本 ID、原始输出、规范化答案、解析状态、调用次数和 token 统计。

### 4.2 模型与解码

- 主模型：`Qwen3.5-4B`、`Qwen3.5-9B`；尺度参照：`Qwen3.5-2B`、`Qwen3.5-27B`。
- 主实验统一使用 instruction/chat checkpoint、相同精度和同一推理后端。
- Qwen3.5 主实验必须在请求体中显式固定 **non-thinking mode**；不得依赖后端默认值。thinking mode 仅进附录。
- temperature、top-p、最大输出 token、上下文截断策略必须对所有方法一致。推荐主结果 temperature=0；若后端仍存在非确定性，对最终两种系统做 3 次独立运行。
- 所有 prompt-based baseline 使用同一表格序列化输入；G-CRAFT 允许的额外信息只能来自其声明的结构模块。

### 4.3 指标与统计

**决定性指标**：

- 官方 full-test accuracy；解析失败、超时和异常均按错误计入固定分母。
- 相对最强基线的逐样本配对差值及 95% bootstrap CI。
- 同一测试集上使用 McNemar 检验比较 G-CRAFT 与最强基线；多模型比较做 Holm 校正。

**效率指标**：

- 每样本 input/output/total tokens、LLM 调用次数、端到端 P50/P95 延迟、峰值显存。
- 修正触发率、修正成功率、错误引入率：`wrong→right`、`right→wrong`。
- 同硬件下的 accuracy–latency 和 accuracy–VRAM Pareto 图。

**诊断指标**：

- 按表格行数四分位、操作类型、答案类型统计 accuracy。
- ATGO 的 top-k evidence coverage 只在可构造 gold evidence 的子集报告。
- 不把不同论文中统计口径不一致的 token 数直接放入核心效率表。

## 五、实验块

### B1：小模型核心主表

- **Claim tested**：C1。
- **为什么存在**：直接回答“G-CRAFT 是否真正帮助 Qwen3.5-4B/9B 小模型”。
- **数据/任务**：完整 WikiTQ（主）、完整 TabFact（辅）。
- **比较系统（最多三类 baseline family）**：
  1. Prompt baseline：Direct、CoT（二者中结果弱者可移附录）；
  2. Structured reasoning：Chain-of-Table；
  3. Feedback baseline：Table-Critic；
  4. G-CRAFT（ours）。
- **模型**：Qwen3.5-4B、Qwen3.5-9B。
- **指标**：accuracy、95% CI、tokens、calls、P50/P95 latency、peak VRAM。
- **成功标准**：WikiTQ 上 G-CRAFT 对 4B 与 9B 的最强基线均有正向配对 CI；实际决策门槛建议至少 `+2.0 pp`，或一档达到 `+3.0 pp` 且另一档不退化。TabFact 不显著退化超过 `1.0 pp`。
- **失败解释**：若只在 4B 有效，则收窄为“极小模型补偿”；若 WikiTQ 也无稳定提升，则不能采用小模型总体性能叙事，应转向特定长表/错误修复能力。
- **目标表/图**：主文 Table 1。
- **优先级**：MUST-RUN。

### B2：同代尺度效应与“小模型替代大模型”

- **Claim tested**：C1、C2。
- **为什么存在**：证明收益随规模变化，并把小模型价值转化为部署层面的结论。
- **数据/任务**：WikiTQ 完整测试集；TabFact 可只保留 G-CRAFT 与最强基线。
- **比较系统**：最强 baseline 与 G-CRAFT；Qwen3.5-2B/4B/9B/27B。
- **指标**：`Δaccuracy = Acc(G-CRAFT)-Acc(baseline)`、模型大小、显存、延迟、tokens。
- **关键比较**：
  - Qwen3.5-4B + G-CRAFT vs Qwen3.5-9B baseline；
  - Qwen3.5-9B + G-CRAFT vs Qwen3.5-27B baseline（仅作为扩展，不作为必须达到的替代结论）；
  - 各规模下 G-CRAFT 的边际增益。
- **成功标准**：4B/9B 的增益明显大于 27B；至少 Qwen3.5-4B + G-CRAFT 在 accuracy 上进入 9B baseline 的 `±1 pp`，同时峰值显存显著更低。
- **失败解释**：若尺度趋势不单调，只报告“小模型有效”而不声称规模规律；若小模型无法接近大模型，则删除“替代”表述，只保留“改善”。
- **目标表/图**：主文 Figure 3（参数规模–增益曲线）和效率 Pareto 图。
- **优先级**：MUST-RUN；27B 仅在 M2 gate 通过后再跑。

### B3：机制隔离与最小充分系统

- **Claim tested**：C2。
- **为什么存在**：排除收益只是更多调用或模块堆叠，并回应创新性不足。
- **数据/任务**：Qwen3.5-4B × WikiTQ/TabFact 完整测试；Qwen3.5-9B × WikiTQ 做关键复现。
- **推荐累加链**：
  1. Thought / Chain-of-Table；
  2. `+ ATGO row reordering`；
  3. `+ schema anchor`；
  4. `+ controller-routed refinement`（Full）。
- **推荐删除消融**：Full、w/o ATGO、w/o schema anchor、w/o controller routing、w/o retrieved plan。
- **P1/P2 特别处理**：P1（gamma smoothing）与 P2（graph hint）需在完整测试集上独立开关；当前 `run_FV.sh/run_QA.sh` 禁止部分组合，因此应由矩阵 runner 统一执行，但必须把输入从 `error_data.jsonl` 切到完整 test。
- **等预算对照**：给最强 baseline 与 G-CRAFT 相同的最大调用次数/总输出 token，或增加 `Table-Critic + one extra refine`，验证优势不是纯计算量。
- **成功标准**：Full 优于各关键删除版本；schema/controller 至少有一个在 4B 上产生稳定、配对 CI 为正的贡献；Full 位于 accuracy–cost Pareto 前沿。
- **失败解释**：若 ATGO 无贡献或负贡献，从核心贡献降为可选预处理；若路由不优于固定 refine，删去“controller-routed 是核心创新”的强表述。
- **目标表/图**：主文 Table 2；完整组合进附录。
- **优先级**：MUST-RUN。

### B4：公平性与 frontier necessity check

- **Claim tested**：C2 与两个 anti-claim。
- **为什么存在**：验证现代小模型本身的 thinking 能力是否已经足以替代 G-CRAFT，以及 G-CRAFT 是否只是在增加推理预算。
- **数据/任务**：Qwen3.5-4B/9B，WikiTQ 预注册 500 条分层子集；通过后可扩展 full test。
- **比较系统**：
  - non-thinking baseline；
  - thinking baseline；
  - non-thinking + G-CRAFT；
  - thinking + G-CRAFT（NICE-TO-HAVE）。
- **指标**：accuracy、reasoning tokens、延迟、调用次数。
- **成功标准**：non-thinking + G-CRAFT 在同等或更低总 token 下优于 thinking baseline，或在相近 accuracy 下显著降低延迟/显存。
- **失败解释**：若 thinking baseline 已完全覆盖收益，则论文应改为“小模型推理时结构化控制的效率/可诊断性”，不能再主张 accuracy 优势。
- **目标表/图**：附录主表或主文效率图。
- **优先级**：MUST-RUN（前三项）；组合项 NICE-TO-HAVE。

### B5：失败与边界分析

- **Claim tested**：解释 C1 成立或不成立的条件。
- **数据/任务**：B1 的逐样本预测，不额外调用模型。
- **分析**：按长表、列歧义、数值聚合、多跳操作、最终表达错误分桶；统计 Thought→Refine 的 `wrong→right` 与 `right→wrong`。
- **成功标准**：能定位至少两类小模型显著受益错误，并同时披露一类仍失败或被错误修正的样本。
- **目标表/图**：主文 error breakdown + 2 个案例；详细路由放附录。
- **优先级**：MUST-RUN，但不应延迟主结果。

## 六、主表设计

### Table 1：Small-model main results

行只保留 `Direct / CoT / Chain-of-Table / Table-Critic / G-CRAFT`，列为：

| Method | Qwen3.5-4B WikiTQ | Qwen3.5-4B TabFact | Qwen3.5-9B WikiTQ | Qwen3.5-9B TabFact | Avg Tokens | Calls | P95 Latency |
|---|---:|---:|---:|---:|---:|---:|---:|

每个 accuracy 单元报告 `mean ± std`；脚注给出与最强基线的配对检验。若 greedy 解码完全确定，则报告单次 accuracy + bootstrap CI，不制造无意义的 seed 标准差。

### Figure 3：Scale compensation curve

- x 轴：Qwen3.5 参数规模 2B/4B/9B/27B（log scale）。
- y 轴：相对最强 baseline 的 accuracy 增益。
- WikiTQ 为主线，TabFact 为浅色辅线。
- 该图只使用同代、同 checkpoint 类型和同解码协议的数据。

### Table 2：Minimal mechanism ablation

以 Qwen3.5-4B 为主，报告 Full 及四个关键删除版本；不要使用 27B 作为主消融模型。Qwen3.5-9B 只复现 Full、w/o schema、w/o controller 三行。

## 七、运行顺序与里程碑

| Milestone | 目标 | Runs | Decision Gate | 成本估计 | 风险 |
|---|---|---|---|---|---|
| M0 | 修复评测可信度 | evaluator 单元测试；失败样本固定分母；冻结 memory；50 条 2B/4B smoke | 任一系统样本数、ID、分母、memory hash 不一致则停止 | 0.5–1 天工程时间；约 200 sample-pipeline | 旧结果不可直接复用 |
| M1 | 低成本验证新方向 | WikiTQ 分层 500 条：4B 本地主 pilot；9B 在 ≥16GB GPU 复现 | 4B 达到 `+3 pp` 才扩展 9B；否则先做失败分析 | 2,000–4,000 sample-pipeline；以 M0 实测速率换算 GPU-hours | prompt 解析在 4B 上失效 |
| M2 | 核心主表 | 完整 WikiTQ/TabFact：4B/9B × 5 systems | WikiTQ 配对 CI 为正；TabFact 退化不超过 1 pp | 63,680 sample-pipeline/单次全矩阵 | 9B 需要远程或更大显存 |
| M3 | 尺度与消融 | WikiTQ 2B/27B 两系统；4B 全消融；9B 关键消融 | 4B/9B 增益大于 27B，且至少一个组件贡献稳定 | 约 45,000–65,000 sample-pipeline | 交互项导致趋势不单调 |
| M4 | 统计与效率复核 | 最强 baseline 与 G-CRAFT 在 4B/9B 做重复运行；采集延迟/显存/token | 结果方向在重复运行中一致 | 额外 25,472–50,944 sample-pipeline | endpoint 非确定性 |
| M5 | 附录和案例 | Qwen3-4B/8B、thinking、online memory、案例 | 不阻塞主文；只在 M2/M3 通过后执行 | NICE-TO-HAVE | 扩张实验范围 |

`sample-pipeline` 表示一个系统完整处理一个样本。由于当前流水线包含多次串行 LLM 调用，直接给出未经测量的 GPU-hours 会误导。M0 必须记录 2B/4B 的 samples/hour、tokens/second 和 peak VRAM，再按：

```text
GPU-hours = sample-pipeline 数 / 实测 samples-per-GPU-hour
```

换算。按照当前 error-subset 日志的调用规模，完整矩阵可能达到数百到上千 endpoint-hours；因此必须先过 M1 gate，并使用 vLLM/SGLang continuous batching、预处理缓存和逐样本断点续跑。

## 八、必须运行与可选运行

### MUST-RUN

1. 评估器失败样本计错、固定分母和逐样本覆盖率检查。
2. 测试时冻结错误经验库；每个 run 保存初始/最终 memory hash。
3. Qwen3.5-4B/9B × WikiTQ/TabFact 核心主表。
4. Qwen3.5-4B 主消融与 Qwen3.5-9B 关键复现。
5. Qwen3.5-2B/4B/9B/27B 同代尺度曲线中的 G-CRAFT vs 最强 baseline。
6. 等 token/等调用预算对照。
7. 逐样本配对统计与效率指标。

### NICE-TO-HAVE

- Qwen3-4B/8B 跨代复现。
- Qwen3.5 thinking + G-CRAFT。
- online-memory 三种测试顺序。
- gamma 全扫描；主文只保留预注册默认值与 `gamma=0`。
- 更多数据集或其他 7–8B 模型族。

## 九、代码执行前的已知风险与缓解

- **评估分母错误**：多个 `evaluate.py` 存在 bare `except` 后 `continue`。必须改为记录失败并按错误计入固定分母，同时输出 coverage。
- **测试记忆泄漏**：Controller 会调用 `update_error_tree()`。主实验增加只读/frozen-memory 开关，并校验文件 hash 不变。
- **子集选择偏差**：矩阵 runner 的默认输入是 `error_data.jsonl`。增加显式 `--dataset_path` 或 full-test preset，主结果拒绝 error-only 输入。
- **脚本能力不一致**：`run_FV.sh/run_QA.sh` 强制 P1/P2 同开同关，但矩阵 runner 支持独立组合。统一由一个 runner 生成 manifest，避免不同脚本产生不同协议。
- **结果目录覆盖**：输出路径必须包含 model、dataset、variant、seed、thinking mode、memory mode 和时间戳；禁止复用含旧 cache 的目录。
- **4B 格式遵循失败**：M0 统计 invalid operation、JSON parse failure 和空答案率。若失败率高，先统一输出 grammar/stop tokens，不能静默跳过。
- **成本混杂**：保存每阶段 token/calls/latency；不再引用第三方不同口径 token 表作为核心证据。
- **量化混杂**：主尺度曲线尽量统一 BF16；本机 8GB 显存只能将 Qwen3.5-4B 作为 4-bit pilot。正式尺度结论必须在统一精度、统一后端的设备上复跑，不能把本机 4-bit 与远程 BF16 结果直接归因为参数规模效应。
- **本机执行边界**：RTX 5060 Laptop 8GB 仅承担 Qwen3.5-2B/4B 的 M0/M1；Qwen3.5-9B 的主结果使用至少 16GB 显存，27B 使用更大显存或多卡。CPU offload 结果不得进入延迟/显存公平比较。

## 十、Stop / Go 决策

### GO：采用“小模型能力补偿”主叙事

满足以下三项：

1. WikiTQ 上 4B/9B 至少一个相对最强基线提升不低于 3 pp，另一个不低于 0，且配对 CI 支持正向结论；
2. 关键消融能把收益归因到 schema/controller，而不是纯 token 增长；
3. 4B + G-CRAFT 接近 9B baseline，或在 accuracy–VRAM/latency 上形成 Pareto 优势。

### NARROW：只讲“小模型困难样本修复”

总体 accuracy 增益不稳定，但在长表、多步或 schema 歧义子集上有预注册、显著且可解释的收益。此时题目和摘要必须限定场景，不能事后只挑有利分桶。

### STOP：不采用新叙事

4B/9B 上 Full 不优于 Table-Critic，或收益在冻结 memory、固定分母、等预算后消失。此时应保留工程系统定位，不继续投入 27B 大规模重复实验。

## 十一、最终检查清单

- [ ] 主表聚焦 Qwen3.5-4B/9B
- [ ] 尺度结论只使用同代 Qwen3.5 模型
- [ ] 官方完整测试集覆盖，异常样本计为错误
- [ ] 主结果采用 frozen-memory inductive setting
- [ ] Qwen3.5 thinking mode 与解码预算固定
- [ ] novelty 通过小模型主消融隔离
- [ ] simplicity 通过最小累加链和删除消融证明
- [ ] efficiency 使用同硬件、同统计口径
- [ ] error-only 子集只用于诊断
- [ ] nice-to-have 不阻塞核心证据

## 十二、Workflow 1.5 执行契约

本节供 `/experiment-bridge` 直接解析。

- **Base repository**：`/home/cocopink/code/Table-Critic`
- **Plan**：`refine-logs/EXPERIMENT_PLAN.md`
- **Tracker**：`refine-logs/EXPERIMENT_TRACKER.md`
- **Method specification**：`refine-logs/FINAL_PROPOSAL.md`
- **Research contract**：`idea-stage/docs/research_contract.md`
- **Sanity first**：是；严格按 `R001 → R002 → R003/R004 → R006` 执行。
- **Auto deploy**：否。完成 M0 代码修复和 smoke 后，先报告显存、吞吐与预计总 GPU-hours，再决定是否部署 M1。
- **Local execution profile**：RTX 5060 Laptop 8GB；本机只部署 Qwen3.5-2B/4B，4B 使用 4-bit、batch=1、concurrency=1、non-thinking。
- **Remote execution profile**：Qwen3.5-9B 使用 ≥16GB GPU；Qwen3.5-27B 只在 M2 通过后调度。
- **Primary entry points**：`run_QA.sh`、`run_FV.sh`；矩阵执行统一收敛为单一 manifest runner。
- **Result format**：每个 run 必须产出逐样本 JSONL、汇总 JSON/CSV、运行 manifest、memory 前后 hash 和失败样本记录。
- **禁止部署条件**：评估分母、frozen memory、cache key、Qwen3.5 non-thinking 任一项未通过 M0 测试。

### 12.1 Bridge 首轮只允许实现的修复

1. 评估异常按错误计入固定分母，并输出 coverage。
2. 增加 frozen-memory 开关和运行前后 hash 校验。
3. cache/output key 纳入 model、dataset、variant、gamma、thinking、seed、memory mode。
4. OpenAI-compatible 与 Ollama 路径统一显式控制 Qwen3.5 thinking。
5. runner 显式接收完整 test 路径，拒绝把 `error_data.jsonl` 当总体评测。
6. 输出机器可解析的 JSONL/JSON/CSV，并记录 ground-truth 来源。

为遵守 KISS/YAGNI，首轮不得顺带重构整个多智能体框架，也不得实现论文中尚无代码依据的 `ConstructPlan`。方法表述以 `FINAL_PROPOSAL.md` 为准。
