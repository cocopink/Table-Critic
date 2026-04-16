# Thought 模块文档

[根目录](../CLAUDE.md) > **thought**

> 最后更新：2026-04-16 00:17:51

---

## 变更记录 (Changelog)

### 2026-04-16
- 初始化 thought 模块文档
- 识别 TableQA 和 TableFV 两种任务类型
- 建立 operations 和 utils 文档

---

## 模块职责

Thought 模块是 Table-Critic 的**初始推理阶段**，负责执行动态链推理，生成第一版答案。

### 核心功能

1. **动态链执行**：基于 Chain-of-Table 的动态推理链
2. **表格操作**：6 种核心表格操作（select_row, select_column, group_by, sort_by, add_column, final_query）
3. **Schema 锚定**（可选）：Clarifier 提取的轻量化关键词典
4. **Token 统计**：自动记录 API 调用的 token 使用量

---

## 入口与启动

### TableQA 任务入口

**文件**：`thought/TableQA/main.py`

```bash
# 命令行调用
python thought/TableQA/main.py \
  --thought_results_dir results/new/thought/wikitq \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --use_clarifier True
```

**参数说明**：
- `--thought_results_dir`：结果输出目录
- `--base_url`：LLM API base URL
- `--openai_api_key`：API 密钥
- `--model_name`：模型名称
- `--first_n`：处理前 N 个样本（-1 表示全部）
- `--use_clarifier`：是否启用 Clarifier

### TableFV 任务入口

**文件**：`thought/TableFV/main.py`

```bash
python thought/TableFV/main.py \
  --thought_results_dir results/new/thought/tabfact \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --n_proc 8 \
  --chunk_size 4 \
  --use_clarifier True
```

---

## 对外接口

### 主要函数

#### 1. dynamic_chain_exec_with_cache_mp

**文件**：`thought/TableQA/utils/chain.py`

```python
def dynamic_chain_exec_with_cache_mp(
    dataset: List[Dict[str, Any]],
    llm: LLM,
    llm_options: Dict,
    strategy: str = "top",
    cache_dir: str = None,
    n_proc: int = 8,
    chunk_size: int = 4,
) -> Tuple[List[Dict], Dict]:
    """
    动态链执行（多进程，支持缓存）

    Args:
        dataset: 数据集列表
        llm: LLM 实例
        llm_options: LLM 调用选项
        strategy: 选择策略（"top" 或 "sample"）
        cache_dir: 缓存目录
        n_proc: 进程数
        chunk_size: 分块大小

    Returns:
        (处理后的样本列表, 统计信息)
    """
```

**功能**：
- 对每个样本动态选择操作序列
- 支持多进程并发执行
- 自动缓存中间结果

#### 2. fixed_chain_exec_mp

**文件**：`thought/TableQA/utils/chain.py`

```python
def fixed_chain_exec_mp(
    llm: LLM,
    proc_samples: List[Dict],
    fixed_chain: List[Tuple],
    n_proc: int = 4,
    chunk_size: int = 2,
) -> Tuple[List[Dict], Dict]:
    """
    固定链执行（多进程）

    Args:
        llm: LLM 实例
        proc_samples: 预处理样本列表
        fixed_chain: 固定操作链
        n_proc: 进程数
        chunk_size: 分块大小

    Returns:
        (最终结果列表, 统计信息)
    """
```

**功能**：
- 执行固定的操作序列（如 Simple query）
- 用于生成最终答案

---

## 表格操作（Operations）

### 操作列表

| 操作 | 文件 | 功能 | 输入 | 输出 |
|------|------|------|------|------|
| **select_row** | `operations/select_row.py` | 选择行 | table, 条件 | filtered_table |
| **select_column** | `operations/select_column.py` | 选择列 | table, 列名 | projected_table |
| **group_by** | `operations/group_by.py` | 分组聚合 | table, 分组列 | grouped_table |
| **sort_by** | `operations/sort_by.py` | 排序 | table, 排序列 | sorted_table |
| **add_column** | `operations/add_column.py` | 添加列 | table, 计算式 | extended_table |
| **final_query** | `operations/final_query.py` | 最终查询 | table, 问题 | answer |

### 操作接口规范

每个操作文件都包含以下函数：

```python
def f_{operation_name}(table, param_dict):
    """
    执行表格操作

    Args:
        table: pandas DataFrame 或列表的列表
        param_dict: 参数字典

    Returns:
        操作后的表格
    """
    pass
```

### 操作示例

#### select_row

```python
def f_select_row(table, param_dict):
    """
    选择满足条件的行

    Args:
        table: 表格数据
        param_dict: {
            'condition': 'Score > 80',
            'index': 0  # 可选，从第几行开始
        }

    Returns:
        filtered_table: 过滤后的表格
    """
    condition = param_dict.get('condition')
    # 实现过滤逻辑
    return filtered_table
```

#### group_by

```python
def f_group_by(table, param_dict):
    """
    按列分组并聚合

    Args:
        table: 表格数据
        param_dict: {
            'group_by_column': 'Category',
            'operation': 'sum',  # sum, avg, count, max, min
            'value_column': 'Amount'
        }

    Returns:
        grouped_table: 分组聚合后的表格
    """
    # 实现分组逻辑
    return grouped_table
```

#### final_query

```python
def f_final_query(table, param_dict):
    """
    基于表格生成最终答案

    Args:
        table: 表格数据
        param_dict: {
            'question': 'What is the total score?',
            'answer_format': 'short'  # short, long
        }

    Returns:
        answer: 最终答案
    """
    # 实现查询逻辑
    return answer
```

---

## 关键依赖与配置

### 依赖项

```python
# 内部依赖
from agents import ClarifierAgent
from utils.llm import LLM
from utils.load_data import load_wikitq_dataset, load_tabfact_dataset
from utils.helper import table2string
from utils.chain import dynamic_chain_exec_with_cache_mp, fixed_chain_exec_mp
from operations import *

# 外部依赖
import fire
import pandas as pd
import pickle
import os
from tqdm import tqdm
```

### LLM 配置

**文件**：`thought/TableQA/utils/llm.py`

```python
class LLM:
    def __init__(self, model_name, key, base):
        self.model_name = model_name
        self.key = key
        self.base = base
        self.input_tokens = 0
        self.output_tokens = 0
        self._token_log_dir = None
        self._run_tag = ""

    def set_token_log_dir(self, log_dir, run_tag=""):
        """设置 token 日志目录"""
        self._token_log_dir = log_dir
        self._run_tag = run_tag

    def get_model_options(
        self,
        temperature=0,
        per_example_max_decode_steps=150,
        per_example_top_p=1,
        n_sample=1,
    ):
        """获取模型调用选项"""
        options = dict(
            temperature=temperature,
            n=n_sample,
            top_p=per_example_top_p,
            max_tokens=per_example_max_decode_steps,
        )
        # 只有非 GPT 模型才添加 enable_thinking 参数
        if not self.model_name.startswith('gpt-'):
            options['extra_body'] = {"enable_thinking": False}
        return options
```

### 数据加载

**文件**：`thought/TableQA/utils/load_data.py`

```python
def load_wikitq_dataset(dataset_path, first_n=-1):
    """
    加载 WikiTableQuestions 数据集

    Args:
        dataset_path: 数据集路径（.jsonl 格式）
        first_n: 加载前 N 个样本

    Returns:
        dataset: 样本列表
    """
    pass

def load_tabfact_dataset(dataset_path, first_n=-1):
    """
    加载 TabFact 数据集

    Args:
        dataset_path: 数据集路径
        first_n: 加载前 N 个样本

    Returns:
        dataset: 样本列表
    """
    pass
```

---

## 数据流与处理流程

### TableQA 流程

```
输入样本
  ↓
[可选] Clarifier 提取 schema 锚点
  ↓
dynamic_chain_exec_with_cache_mp
  ├── 选择操作序列（select_row, group_by, etc.）
  ├── 执行操作
  └── 生成中间结果
  ↓
fixed_chain_exec_mp (Simple query)
  ↓
最终答案 + 准确率
```

### 数据格式

#### 输入格式

```python
{
    'id': 'sample_001',
    'table': [
        ['Name', 'Age', 'Score'],
        ['Alice', 25, 85],
        ['Bob', 30, 90]
    ],
    'question': 'What is the average score?',
    'answer': '87.5'  # 真实答案（用于评估）
}
```

#### Clarifier 输出格式

```python
{
    'id': 'sample_001',
    'table': [...],
    'question': '...',
    'answer': '...',
    'clarifier': {
        'headers': ['Name', 'Age', 'Score'],
        'entities': {'Person': ['Alice', 'Bob']},
        'units': {'Score': 'points', 'Age': 'years'},
        'keywords': ['average', 'total']
    }
}
```

#### 推理链格式

```python
{
    'id': 'sample_001',
    'table': [...],
    'question': '...',
    'chain': [
        {
            'step': 1,
            'operation': 'select_row',
            'params': {'condition': 'Score > 80'},
            'result': 'filtered_table',
            'explanation': 'Select rows with score > 80'
        },
        {
            'step': 2,
            'operation': 'group_by',
            'params': {'group_by_column': 'Category', 'operation': 'avg'},
            'result': 'grouped_table',
            'explanation': 'Group by Category and calculate average'
        },
        {
            'step': 3,
            'operation': 'final_query',
            'params': {'question': '...'},
            'result': '87.5',
            'explanation': 'The average score is 87.5'
        }
    ],
    'pred_answer': '87.5'
}
```

#### 最终输出格式

```python
{
    'id': 'sample_001',
    'table': [...],
    'question': '...',
    'chain': [...],
    'pred_answer': '87.5',
    'clarifier': {...}  # 如果启用
}
```

---

## 测试与质量

### 评估脚本

**文件**：`thought/TableQA/utils/evaluate.py`

```python
def wikitq_match_func_for_samples(samples):
    """
    计算 WikiTQ 数据集的准确率

    Args:
        samples: 样本列表

    Returns:
        accuracy: 准确率（0-1）
    """
    pass

def tabfact_match_func_for_samples(samples):
    """
    计算 TabFact 数据集的准确率

    Args:
        samples: 样本列表

    Returns:
        accuracy: 准确率（0-1）
    """
    pass
```

### 辅助工具

**文件**：`thought/TableQA/utils/helper.py`

```python
def table2string(table):
    """
    将表格转换为字符串表示

    Args:
        table: 表格数据（列表的列表）

    Returns:
        table_str: 表格字符串
    """
    pass

def parse_operation_from_response(response):
    """
    从 LLM 响应中解析操作

    Args:
        response: LLM 响应文本

    Returns:
        operation: 操作名称
        params: 参数字典
    """
    pass
```

---

## 常见问题 (FAQ)

### Q1: 如何添加新的表格操作？

**A**：
1. 在 `thought/TableQA/operations/` 创建新文件，如 `new_operation.py`
2. 实现操作函数：
   ```python
   def f_new_operation(table, param_dict):
       # 实现逻辑
       return result
   ```
3. 在 `operations/__init__.py` 中导入：
   ```python
   from .new_operation import f_new_operation
   ```
4. 在 `utils/chain.py` 中注册操作

### Q2: 如何调整推理链的长度？

**A**：
- **动态链**：LLM 自动决定何时停止（当认为可以回答问题时）
- **固定链**：在 `main.py` 中定义 `fixed_chain` 变量

### Q3: Clarifier 是如何集成的？

**A**：
```python
if use_clarifier:
    clarifier = ClarifierAgent(llm=gpt_llm)
    dataset = clarifier.clarify_batch(dataset)
    # 保存 clarifier 结果
    for sample in dataset:
        sample_id = sample.get('id', 'unknown')
        clarifier_path = os.path.join(clarifier_dir, f'case_dict_{sample_id}.pkl')
        pickle.dump(sample['clarifier'], open(clarifier_path, "wb"))
```

### Q4: Token 统计是如何工作的？

**A**：
1. 在 LLM 初始化时调用 `set_token_log_dir(log_dir, run_tag)`
2. 每次 API 调用后自动追加到 `{log_dir}/token_{run_tag}_{pid}.jsonl`
3. 在阶段结束时汇总到 `token_usage.json`

**查看统计**：
```python
token_usage = LLM.collect_token_usage(
    thought_results_dir,
    output_path=os.path.join(thought_results_dir, "token_usage.json")
)
print(f"Input Tokens: {token_usage['input_tokens']:,}")
print(f"Output Tokens: {token_usage['output_tokens']:,}")
```

### Q5: 如何处理缓存冲突？

**A**：
- 每个进程使用独立的缓存文件（基于 PID）
- 缓存目录结构：`{cache_dir}/cache_{pid}.pkl`
- 在多进程环境下自动避免冲突

---

## 相关文件清单

### TableQA 任务

- `thought/TableQA/main.py` - 入口文件
- `thought/TableQA/operations/__init__.py` - 操作导出
- `thought/TableQA/operations/select_row.py` - 选择行操作
- `thought/TableQA/operations/select_column.py` - 选择列操作
- `thought/TableQA/operations/group_by.py` - 分组操作
- `thought/TableQA/operations/sort_by.py` - 排序操作
- `thought/TableQA/operations/add_column.py` - 添加列操作
- `thought/TableQA/operations/final_query.py` - 最终查询操作
- `thought/TableQA/utils/llm.py` - LLM 封装
- `thought/TableQA/utils/load_data.py` - 数据加载
- `thought/TableQA/utils/helper.py` - 辅助函数
- `thought/TableQA/utils/evaluate.py` - 评估函数
- `thought/TableQA/utils/chain.py` - 推理链执行

### TableFV 任务

- `thought/TableFV/main.py` - 入口文件
- `thought/TableFV/operations/` - 操作定义（与 TableQA 类似）
- `thought/TableFV/utils/` - 工具函数（与 TableQA 类似）

---

**下一步建议**：

1. 补充各操作的详细实现文档
2. 建立 operations 的单元测试
3. 优化动态链的选择策略
4. 添加更多数据集支持
