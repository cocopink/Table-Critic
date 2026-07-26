# G-CRAFT 代码—论文逻辑吻合审计

**代码仓库**：`/home/cocopink/code/Table-Critic`  
**论文**：`/home/cocopink/paper/G-CRAFT/G_CRAFT_revised_main.tex`  
**结论**：整体架构部分吻合，但关键因果路径和评测协议存在实质差距。三阶段系统骨架约为“较高吻合”，论文核心组件如何进入推理与修正的描述仅为“部分吻合”。当前不宜直接用代码结果支撑所有方法段强表述。

## 1. 已吻合部分

| 论文逻辑 | 代码证据 | 判断 |
|---|---|---|
| Preprocess → Thought → Refine 三阶段 | `run_QA.sh`、`run_FV.sh` 依次执行 ATGO、thought、refine | 吻合 |
| 表格图与 question-guided PPR 重排 | `preprocess_utils/atgo_rerank.py`、`table_structure/qg_ppr.py` | 基本吻合 |
| column smoothing | `table_structure/column_smoothing.py` | 吻合 |
| Clarifier 抽取 header/entity/unit/schema 线索 | `agents/clarifier_agent.py` | 基本吻合；实际为规则实现 |
| Controller 的停止、诊断、链修正、查询修正与错误树更新 | `agents/controller.py` 及 refine 的 `main_tree_based.py` | 基本吻合 |
| graph hint/schema anchor 影响部分 refine operation | `refine/TableQA/operations/select_column.py`、`select_row.py`、final query 路径 | 部分吻合 |

## 2. 关键不吻合

| 论文主张 | 当前代码事实 | 风险等级 | 建议 |
|---|---|---:|---|
| graph hint 与 schema anchor 进入初始 Planner/answer | 初始 thought planning prompt 主要只消费 table 与 question | MAJOR | 论文限定为 refinement-stage conditioning，或补实现后单独消融 |
| anchor 从 reranked table 提取 | Clarifier 当前读取原始 `table_text` | MAJOR | 论文改为原 schema anchor；若要图耦合则显式传 reranked table |
| Critic/Controller 联合消费 anchor 与 graph hint 定位错误 | Critic/Controller 决策路径没有稳定、显式消费这两个字段 | MAJOR | 收窄表述到具体 operation，不能写成全局控制信号 |
| 存在实例级 `ConstructPlan`/结构化计划对象 | 代码仅检索 blueprint/few-shot，没有对应 plan constructor | CRITICAL | 删除该算法步骤，改为 blueprint-conditioned diagnosis；除非新增实现和消融 |
| graph hint 包含局部节点与边集合 | 当前 context 主要输出 top rows/columns，不含完整边集合 | MAJOR | 修改数学定义，或扩展序列化实现 |
| PPR 公式 `(1-α)p0 + αAᵀp` | 代码实现为 `αp0 + (1-α)Aᵀp` | CRITICAL | 统一公式与实现后重新生成预处理结果 |
| 每个 cell 是 five-tuple graph node | 代码以 triple/record 携带行列字段，真实节点类型另有定义 | MINOR | 修改术语，不影响运行 |
| 主结果是 strict inductive/frozen independent memory | Controller 使用共享硬编码错误树，且更新锁不是跨进程锁 | CRITICAL | M0 增加只读快照、独立路径和 hash 校验 |
| 所有失败计入官方分母 | 多个 evaluator 在异常后 `continue`，可能缩小分母 | CRITICAL | R001 修复并加入 coverage 单测 |
| 不同 variant/gamma 的缓存独立 | shell 和部分 legacy cache key 未完整包含 gamma/hint/config | CRITICAL | R005 统一 cache/output identity |
| Qwen non-thinking 协议一致 | Ollama 路径显式关闭；OpenAI-compatible Qwen 路径的条件逻辑未可靠关闭 | CRITICAL | Qwen3.5 部署前统一请求体和日志字段 |

## 3. 对论文叙事的直接影响

当前代码能够支撑的保守叙事是：

> G-CRAFT 使用 ATGO 重排表格证据，通过规则式 schema anchor 和 controller-routed refinement 改善小模型的表格推理；anchor/graph hint 当前主要作用于若干修正操作。

当前代码不能直接支撑：

> graph 与 anchor 从初始规划到 Critic、Controller 的每个环节形成统一闭环；Controller 构造实例级结构化修正计划。

因此，优先采用“改论文以匹配真实代码”的 KISS 路线；只有当消融显示缺失的数据流是核心贡献时，才增加新的跨阶段注入或 plan object。

## 4. 实验启动前必须完成

1. 修复 evaluator 固定分母；
2. 冻结并隔离 memory；
3. 统一 cache/output identity；
4. 修正或统一 PPR 公式；
5. 显式固定 Qwen3.5 non-thinking；
6. 在论文中删除/收窄 `ConstructPlan`、初始 Planner 全局注入和完整 graph-edge hint 的未实现表述。

完成上述项目后，代码与保守版方法叙事可达到可评测的一致状态；否则实验结果仍可能由协议污染或未实现组件造成错误归因。
