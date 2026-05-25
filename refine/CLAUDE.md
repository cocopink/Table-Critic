# Refine 模块文档

[← 返回根文档](../CLAUDE.md) > **refine**

> 最后更新：2026-05-21 15:15:47

---

## 变更记录 (Changelog)

### 2026-05-21 (精简重构)
- 仅保留管线实际调用的代码路径
- 移除非管线内容（约束模块保留在 QA 中标注）

### 2026-05-13
- Stage 0.5 Hint Consumption 文档

---

## 模块职责

Refine 模块是 **Stage 2 修正阶段**，通过 Controller 驱动的 Critic/Judge/Tree 协作，对 Thought 的错误答案进行迭代修正。

### TableQA 和 TableFV 各有一套实现

- `refine/TableQA/` - 含约束模块（constraint_*.py）
- `refine/TableFV/` - 基础版本

---

## 管线入口

### run_QA.sh 调用

```bash
python refine/TableQA/main_tree_based.py \
  --thought_results_dir "$THOUGHT_RESULTS" \
  --refine_results_dir "$REFINE_RESULTS" \
  --base_url $base_url \
  --openai_api_key $openai_api_key \
  --model_name $model_name \
  --first_n $first_n \
  --n_proc $n_proc \
  --chunk_size $chunk_size \
  --use_controller $([ "$MODE" = "new" ] && echo "True" || echo "False") \
  --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")
```

### run_FV.sh 调用

```bash
python refine/TableFV/main_tree_based.py \
  --thought_results_dir "$THOUGHT_RESULTS" \
  --refine_results_dir "$REFINE_RESULTS" \
  --base_url $base_url \
  --openai_api_key $openai_api_key \
  --model_name $model_name \
  --first_n $first_n \
  --n_proc $n_proc \
  --chunk_size $chunk_size \
  --use_controller $([ "$MODE" = "new" ] && echo "True" || echo "False") \
  --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")
```

---

## sys.path 设置

```python
# main_tree_based.py
sys.path.append('critic/TableQA')   # 或 'critic/TableFV' → from tools import ...
sys.path.append('refine/TableQA')   # 或 'refine/TableFV' → from utils.xxx / from operations import *
sys.path.append('.')                # 根目录 → from agents import ...
```

---

## Controller 架构（★ 核心）

**文件**：`refine/TableQA/utils/controller.py`（TableFV 也有对应副本）

### 核心组件

```python
@dataclass
class ControllerState:
    sample, question, chain, conclusion
    iteration: int = 0
    error_route: Optional[str] = None
    action_history: List[str]

class ControllerAction(Enum):
    STOP / EXECUTE_TREE / DIAGNOSE_BP / DIAGNOSE_FS / REFINE_CHAIN / REFINE_QUERY / UPDATE_TREE

@dataclass
class Decision:
    action: ControllerAction
    reason: str
    confidence: float
    source: str  # "rule" | "llm"
```

### 主循环

```python
def controller_main_loop(sample, llm, llm_options, max_iterations=5,
                         cache_dir=None, use_clarifier=True, thought_results_dir=None) -> Dict
```

**流程**：
1. 加载 Clarifier 信息
2. Judge 初始评判
3. 主循环：`decide()` → `execute()` → 检查 STOP
4. 一次迭代：`EXECUTE_TREE → DIAGNOSE_BP/FS → REFINE_CHAIN/QUERY`

### ActionExecutor

```python
class ActionExecutor:
    def __init__(self, llm, llm_options):
        from agents import RetrieverAgent  # ★ 唯一使用 agents 的地方
        self.retriever = RetrieverAgent(llm=llm, memory_path=CRITIC_TREE_JSON)

    def execute(self, state, decision) -> ControllerState:
        # EXECUTE_TREE → tree_exec_one_sample → error_route
        # DIAGNOSE_BP/FS → critic_exec_one_sample（支持预检索 few-shot）
        # REFINE_CHAIN → dynamic_chain_exec_one_sample + simple_query_cot_original
        # REFINE_QUERY → simple_query_with_critic
        # UPDATE_TREE → update_error_tree
```

---

## Stage 0.5 Hint Consumption

当 Stage 0.5 启用时，`sample["table_analysis"]` 通过 JSONL 数据集透传到 Refine。

### Hint 注入点

| Operation | Hint 字段 | 注入位置 |
|-----------|----------|---------|
| `select_row` | `column_normalizations` | `build_prompt()` 函数 |
| `sort_by` | `format_normalizations` | `build_prompt()` 函数 |
| `final_query` | `answer_format_hint` | 4 个 query 函数 |

**向后兼容**：所有注入使用 `sample.get("table_analysis")` 安全访问，Stage 0.5 未启用时自动跳过。

---

## 工具模块（Utils）

### 共有（QA + FV）

| 文件 | 职责 |
|------|------|
| `controller.py` | Controller 状态机 + ActionExecutor + 主循环 |
| `chain.py` | 链执行引擎（含 Critic 反馈引导重执行） |
| `llm.py` | LLM 封装 + Token 统计 |
| `helper.py` | `table2string()`、`table2df()` 等 |
| `evaluate.py` | 准确率评估函数 |
| `extract_step.py` | 错误步骤解析 |
| `read_pkl.py` | pickle 读取 |

### QA 独有

| 文件 | 职责 |
|------|------|
| `validator.py` | 验证器 |
| `verifier.py` | 校验器 |
| `router.py` | 路由变体 |
| `constraint_state.py` | 四类约束管理 |
| `constraint_induction.py` | Critic 反馈 → 约束转换 |
| `constraint_aware_chain.py` | 约束感知链执行 |

### FV utils

| 文件 | 职责 |
|------|------|
| `controller.py` | Controller（与 QA 结构相同） |
| `chain.py` | 链执行 |
| `llm.py` | LLM 封装 |
| `helper.py` | 辅助函数 |
| `evaluate.py` | 评估函数 |
| `extract_step.py` | 错误步骤解析 |
| `read_pkl.py` | pickle 读取 |

---

## Operations（含 Hint Consumption）

6 种操作与 Thought 阶段相同，但 Refine 版本额外支持 `table_analysis` hint 注入：

- `select_row.py` - 行选择（★ 消费 `column_normalizations`）
- `sort_by.py` - 排序（★ 消费 `format_normalizations`）
- `final_query.py` - 最终查询（★ 消费 `answer_format_hint`）
- `select_column.py` - 列选择
- `group_by.py` - 分组聚合
- `add_column.py` - 添加列

---

## 相关文件清单

### TableQA

- `refine/TableQA/main_tree_based.py` - 入口
- `refine/TableQA/utils/controller.py` - Controller（★）
- `refine/TableQA/utils/chain.py` - 链执行
- `refine/TableQA/utils/` - extract_step, evaluate, helper, llm, read_pkl, validator, verifier, router, constraint_*
- `refine/TableQA/operations/` - 6 个操作 + `__init__.py`
- `refine/TableQA/third_party/` - select_column_row_prompts

### TableFV

- `refine/TableFV/main_tree_based.py` - 入口
- `refine/TableFV/utils/` - controller, chain, llm, helper, evaluate, extract_step, read_pkl
- `refine/TableFV/operations/` - 6 个操作 + `__init__.py`
