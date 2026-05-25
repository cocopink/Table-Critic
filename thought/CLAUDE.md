# Thought 模块文档

[← 返回根文档](../CLAUDE.md) > **thought**

> 最后更新：2026-05-21 15:15:47

---

## 变更记录 (Changelog)

### 2026-05-21 (精简重构)
- 仅保留管线实际调用的代码路径
- 移除非管线内容

### 2026-05-13 (深度扫描)
- 6 种 Operations 完整深度扫描

---

## 模块职责

Thought 模块是 **Stage 1 初始推理**，基于 Chain-of-Table 的动态推理链生成第一版答案。

### TableQA 和 TableFV 各有一套完整实现

- `thought/TableQA/` - WikiTableQuestions 任务
- `thought/TableFV/` - TabFact 任务

两者结构相同：`main.py` + `operations/`（6 个操作）+ `utils/`（5 个工具）+ `third_party/`

---

## 管线入口

### run_QA.sh 调用

```bash
python thought/TableQA/main.py \
  --dataset_path "$DATASET_TO_USE" \
  --thought_results_dir "$THOUGHT_RESULTS" \
  --base_url $base_url \
  --openai_api_key $openai_api_key \
  --model_name $model_name \
  --first_n $first_n \
  --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")
```

### run_FV.sh 调用

```bash
python thought/TableFV/main.py \
  --dataset_path "$DATASET_TO_USE" \
  --thought_results_dir "$THOUGHT_RESULTS" \
  --base_url $base_url \
  --openai_api_key $openai_api_key \
  --model_name $model_name \
  --first_n $first_n \
  --n_proc $n_proc \
  --chunk_size $chunk_size \
  --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")
```

> 注意：FV 比 QA 多 `--n_proc` 和 `--chunk_size` 参数

---

## 表格操作（Operations）

### 统一接口模式

所有操作遵循**两阶段模式**：
1. `*_func`（规划阶段）：调用 LLM 决定操作参数
2. `*_act`（执行阶段）：对 `table_info` 执行表格变换

**置信度聚合**：多候选概率累加，取 top-1
**失败安全**：`skip_op` + `failure_table_info`，单步失败不崩溃

### 操作状态转换

```
<init> → [add_column, select_row, select_column, group_column, sort_column]
add_column → [select_row, select_column, group_column, sort_column, <END>]
select_row → [select_column, group_column, sort_column, <END>]
select_column → [group_column, sort_column, <END>]
group_column → [sort_column, <END>]
sort_column → [<END>]
```

### 6 种操作

| 操作 | 文件 | 关键特征 |
|------|------|----------|
| **select_column** | `operations/select_column.py` | 列转置 prompt、列并集（`union_num=2`） |
| **select_row** | `operations/select_row.py` | 1-based→0-based 转换、并集策略 |
| **sort_by** | `operations/sort_by.py` | 多类型排序、去重检测 |
| **add_column** | `operations/add_column.py` | 增量逐行填充、5 重安全检查 |
| **group_by** | `operations/group_by.py` | 合理性检查（唯一值 > 0.8 拒绝） |
| **final_query** | `operations/final_query.py` | 3 套 few-shot 模板、无 `*_act` |

### `__init__.py` 导出

```python
from .add_column import add_column_func, add_column_act
from .group_by import group_column_func, group_column_act
from .select_column import select_column_func, select_column_act
from .select_row import select_row_func, select_row_act
from .sort_by import sort_column_func, sort_column_act
from .final_query import simple_query
```

---

## 工具模块（Utils）

| 文件 | 职责 |
|------|------|
| `chain.py` | 推理链执行（`dynamic_chain_exec_with_cache_mp`、`fixed_chain_exec_mp`） |
| `llm.py` | LLM 封装 + Token 统计 |
| `helper.py` | `table2string()`、`table2df()`、`NoIndent` 等 |
| `evaluate.py` | `wikitq_match_func_for_samples()`、`tabfact_match_func_for_samples()` |
| `load_data.py` | `load_wikitq_dataset()`、`load_tabfact_dataset()` |

### 第三方

- `third_party/select_column_row_prompts/select_column_row_prompts.py` - `select_column_demo` / `select_row_demo` few-shot 模板

---

## sys.path 设置

`main.py` 中通过以下方式设置模块搜索路径：
```python
sys.path.append('thought/TableQA')   # 或 'thought/TableFV'
sys.path.append('.')                  # 根目录，用于 import agents
sys.path.append('critic/TableQA')    # 或 'critic/TableFV'，用于 import tools
```

---

## 数据流

```
输入 JSONL（含 table_analysis 字段）
  ↓
[可选] ClarifierAgent.clarify_sample() → sample['clarifier']
  ↓
dynamic_chain_exec_with_cache_mp()
  ├── LLM 动态选择操作序列
  ├── 执行 operations（select_row, group_by, ...）
  └── 生成 chain + pred_answer
  ↓
fixed_chain_exec_mp()（Simple query 生成最终答案）
  ↓
输出 pickle 到 thought_results_dir
```

---

## 相关文件清单

### TableQA

- `thought/TableQA/main.py` - 入口
- `thought/TableQA/operations/` - 6 个操作文件 + `__init__.py`
- `thought/TableQA/utils/` - chain.py, llm.py, helper.py, evaluate.py, load_data.py
- `thought/TableQA/third_party/` - select_column_row_prompts
- `thought/TableQA/tools/read_pkl.py` - pickle 读取

### TableFV

- `thought/TableFV/main.py` - 入口
- `thought/TableFV/operations/` - 6 个操作文件 + `__init__.py`
- `thought/TableFV/utils/` - chain.py, llm.py, helper.py, evaluate.py, load_data.py
- `thought/TableFV/third_party/` - select_column_row_prompts
