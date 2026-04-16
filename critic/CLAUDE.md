# Critic 模块文档

[根目录](../CLAUDE.md) > **critic**

> 最后更新：2026-04-16 00:17:51

---

## 变更记录 (Changelog)

### 2026-04-16
- 初始化 critic 模块文档
- 建立错误树结构文档
- 识别 Prompt 模板与更新逻辑

---

## 模块职责

Critic 模块是 Table-Critic 的**批评知识库**，负责维护错误树（Error Tree）、提供 Few-shot 案例和 Blueprint，并支持知识库的动态更新。

### 核心功能

1. **错误树管理**：层次化的错误分类树
2. **Few-shot 检索**：根据错误路由检索相关案例
3. **Blueprint 生成**：从错误案例中提取通用错误模式
4. **树更新**：基于新的错误案例动态更新知识库
5. **Prompt 模板**：提供标准化的 Prompt 指令

---

## 入口与启动

### TableQA 任务入口

**文件**：`critic/TableQA/main.py`

```bash
python critic/TableQA/main.py \
  --thought_results_dir results/new/thought/wikitq \
  --critic_results_dir results/new/critic/wikitq \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --n_proc 1 \
  --chunk_size 1
```

**功能**：
- 读取 Thought 阶段的输出
- 对每个样本执行批评（critique）
- 保存批评结果到 `critic_log_list.pkl`

### TableFV 任务入口

**文件**：`critic/TableFV/main.py`

```bash
python critic/TableFV/main.py \
  --thought_results_dir results/new/thought/tabfact \
  --critic_results_dir results/new/critic/tabfact \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --n_proc 1 \
  --chunk_size 1
```

---

## 错误树结构

### 错误树 JSON

**文件**：`critic/TableQA/tools/few_shot_critic.json`

### 结构示例

```json
{
  "name": "Table Reasoning Errors",
  "children": [
    {
      "name": "select_row_errors",
      "description": "Errors in row selection operations",
      "blueprint": "模型倾向于选择错误的行或忽略关键行",
      "confidence_score": 0.85,
      "children": [
        {
          "name": "condition_error",
          "description": "Incorrect condition in select_row",
          "blueprint": "模型在构建条件时经常使用错误的比较符或逻辑",
          "confidence_score": 0.78,
          "examples": [
            {
              "question": "What is the average score of students with score > 80?",
              "chain": [...],
              "critique": "Step 1 is incorrect. The condition should be '> 80' not '>= 80'.",
              "max_step": 1
            }
          ]
        },
        {
          "name": "index_error",
          "description": "Wrong starting index in select_row",
          "blueprint": "模型经常从错误的行开始选择，忽略表头",
          "confidence_score": 0.72,
          "examples": []
        }
      ]
    },
    {
      "name": "select_column_errors",
      "description": "Errors in column selection operations",
      "blueprint": "模型倾向于保留无关列或删除关键列",
      "confidence_score": 0.81,
      "children": [
        {
          "name": "irrelevant_column_kept",
          "description": "Keeping irrelevant columns",
          "blueprint": "模型无法识别问题中未提及的列应该被删除",
          "confidence_score": 0.75,
          "examples": []
        }
      ]
    },
    {
      "name": "group_by_errors",
      "description": "Errors in grouping operations",
      "blueprint": "模型经常选择错误的分组列或聚合函数",
      "confidence_score": 0.79,
      "children": [
        {
          "name": "wrong_group_column",
          "description": "Incorrect group-by column",
          "blueprint": "模型无法识别应该按哪个列分组",
          "confidence_score": 0.73,
          "examples": []
        },
        {
          "name": "wrong_aggregation",
          "description": "Wrong aggregation function",
          "blueprint": "模型经常混淆 sum/avg/max/min",
          "confidence_score": 0.76,
          "examples": []
        }
      ]
    },
    {
      "name": "final_query_errors",
      "description": "Errors in final query generation",
      "blueprint": "模型在计算最终答案时出现数值错误或单位混淆",
      "confidence_score": 0.83,
      "children": [
        {
          "name": "calculation_error",
          "description": "Numerical calculation errors",
          "blueprint": "模型在加减乘除、百分比计算等操作中出错",
          "confidence_score": 0.80,
          "examples": []
        },
        {
          "name": "unit_confusion",
          "description": "Unit conversion errors",
          "blueprint": "模型忽略了单位的一致性，如将米与厘米混淆",
          "confidence_score": 0.68,
          "examples": []
        }
      ]
    }
  ]
}
```

### 错误路由（Error Route）

错误路由是从根节点到叶子节点的路径，用于定位错误类型。

**示例**：
```
select_row_errors/condition_error
group_by_errors/wrong_aggregation
final_query_errors/calculation_error
```

---

## Prompt 模板

### Instruction 文件

**文件**：`critic/TableQA/tools/instruction.py`

### 1. Critic Instruction

```python
critic_instruction = """You are an intelligent critic tasked with determining which step of the table reasoning is incorrect based on the following information:

1. Original Table: The raw table data.
2. Question: The question pertaining to the table data.
3. Reasoning Steps: A step-by-step process of sub-table transformations and extractions based on the following functions.
    - f_add_column(): Adds a new column to the table.
    - f_select_row(): Selects specific rows based on the question.
    - f_select_column(): Removes irrelevant columns from the table.
    - f_group_column(): Groups rows based on the values in a specific column.
    - f_sort_column(): Sorts rows based on the values in a specified column.
4. Prediction Answer: Final derived answer following the reasoning chain.

Instruction:
1. **Step-wise Analysis**: Conduct an evaluation of each reasoning step's validity. The step that is unnecessary but does not affect the answer is considered correct.
2. **Analysis Categories**:
    - For correct steps: Provide validation reasoning and mark as `Step <NUM> is correct.`
    - For incorrect steps: Detail the logical flaws and mark as `Step <NUM> is incorrect.`
    - You should stop at the first incorrect step.
3. **Conclude this critique**: Summarize this critique with an explicit conclusion.
4. **Conclusion Categories**:
    - Conclude with 'Conclusion: [Incorrect] Step <NUM>'.
"""
```

### 2. Judge Instruction

```python
judge_instruction = """You are an intelligent judge tasked with determining whether the given Prediction Answer is correct or incorrect based on the following information:

1. Original Table: The raw table data.
2. Question: The question pertaining to the table data.
3. Prediction Answer: The answer to the above question, which needs validation.

Instruction:
1. **Explanation**: Conduct an explanation of why the Prediction Answer is correct or incorrect.
2. **Conclusion**:
    - If the Prediction Answer is correct, conclude with 'Conclusion: [Correct]'.
    - If the Prediction Answer is incorrect, conclude with 'Conclusion: [Incorrect]'.
"""
```

### 3. Tree Instruction（用于错误路由）

```python
tree_instruction = """You are an expert in professional logical analysis. With a high level of proficiency, you are required to rely on the following information to accurately identify which step within the reasoning process is incorrect and subsequently locate the corresponding error type within the error tree:

1. Original Table: The raw table data.
2. Question: The question pertaining to the table data.
3. Reasoning Steps: A step-by-step process of sub-table transformations and extractions based on the following functions.
    - f_add_column(): Adds a new column to the table.
    - f_select_row(): Selects specific rows based on the question.
    - f_select_column(): Removes irrelevant columns from the table.
    - f_group_column(): Groups rows based on the values in a specific column.
    - f_sort_column(): Sorts rows based on the values in a specified column.
4. Prediction Answer: The answer derived from the final sub-table.

Instruction:
1. **Analysis**: Conduct an analysis of each reasoning step's validity. The step that is unnecessary but does not affect the answer is considered correct.
    - For correct steps: Provide validation reasoning and mark as `Step <NUM> is correct.`
    - For incorrect steps: Detail the logical flaws and mark as `Step <NUM> is incorrect.`
    - You should stop at the first incorrect step.
2. **Conclusion**:
    - If the Prediction Answer is incorrect, conclude with either 'Conclusion: [Incorrect] (ERROR ROUTE)' or 'Conclusion: [Incorrect] (random)'.
    - Use '(ERROR ROUTE)' to indicate the specific path in the error tree that represents the error.
    - If no such route can be identified, use '(random)' instead.
"""
```

---

## 树更新逻辑

### update_tree 函数

**文件**：`critic/TableQA/tools/update_tree.py`

```python
def update_tree(
    error_tree: Dict[str, Any],
    sample: Dict[str, Any],
    error_route: str,
    blueprint: str = None,
    success: bool = True,
    confidence_increment: float = 0.1
) -> Dict[str, Any]:
    """
    更新错误树

    Args:
        error_tree: 错误树字典
        sample: 错误样本
        error_route: 错误路由（如 'select_row_errors/condition_error'）
        blueprint: Blueprint 摘要（可选）
        success: 是否成功引导修正
        confidence_increment: 置信度增量

    Returns:
        更新后的错误树
    """
    # 解析错误路由
    route_parts = error_route.split('/')

    # 遍历到目标节点
    current_node = error_tree
    for part in route_parts:
        # 查找匹配的子节点
        for child in current_node.get('children', []):
            if child['name'] == part:
                current_node = child
                break
        else:
            # 未找到，创建新节点
            new_node = {
                'name': part,
                'description': '',
                'blueprint': '',
                'confidence_score': 0.5,
                'children': [],
                'examples': []
            }
            current_node.setdefault('children', []).append(new_node)
            current_node = new_node

    # 更新 Blueprint
    if blueprint:
        current_node['blueprint'] = blueprint

    # 更新置信度
    if success:
        current_node['confidence_score'] = min(1.0, current_node['confidence_score'] + confidence_increment)
    else:
        current_node['confidence_score'] = max(0.0, current_node['confidence_score'] - confidence_increment)

    # 添加示例
    current_node['examples'].append({
        'question': sample['question'],
        'chain': sample.get('chain', []),
        'critique': sample.get('critique', ''),
        'max_step': sample.get('max_step', -1)
    })

    return error_tree
```

---

## Few-shot 检索

### get_info 工具

**文件**：`critic/TableQA/tools/get_info.py`

```python
def get_judge_few_shot(
    error_tree: Dict[str, Any],
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    获取 Judge 的 Few-shot 示例

    Args:
        error_tree: 错误树
        k: 检索数量

    Returns:
        Few-shot 示例列表
    """
    # 从错误树中随机选择 k 个示例
    examples = []
    for node in traverse_tree(error_tree):
        if 'examples' in node and len(node['examples']) > 0:
            examples.extend(node['examples'])
            if len(examples) >= k:
                break

    return random.sample(examples, min(k, len(examples)))

def get_cot_for_judge(sample: Dict) -> str:
    """
    获取 Judge 的 Chain-of-Thought

    Args:
        sample: 样本

    Returns:
        Chain-of-Thought 字符串
    """
    # 构建 CoT
    cot = f"Question: {sample['question']}\n"
    cot += f"Table: {table2string(sample['table'])}\n"
    cot += f"Prediction Answer: {sample.get('pred_answer', '')}\n"
    return cot

def get_critique_few_shot(
    error_tree: Dict[str, Any],
    error_route: str,
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    获取 Critic 的 Few-shot 示例

    Args:
        error_tree: 错误树
        error_route: 错误路由
        k: 检索数量

    Returns:
        Few-shot 示例列表
    """
    # 根据 error_route 定位节点
    target_node = locate_node_by_route(error_tree, error_route)

    if not target_node:
        return []

    # 返回该节点的示例
    examples = target_node.get('examples', [])
    return random.sample(examples, min(k, len(examples)))

def get_cot_for_critic(sample: Dict) -> str:
    """
    获取 Critic 的 Chain-of-Thought

    Args:
        sample: 样本

    Returns:
        Chain-of-Thought 字符串
    """
    cot = f"Question: {sample['question']}\n"
    cot += f"Table: {table2string(sample['table'])}\n"
    cot += "Reasoning Steps:\n"
    for i, step in enumerate(sample.get('chain', []), 1):
        cot += f"Step {i}: {step.get('operation', '')} - {step.get('explanation', '')}\n"
    cot += f"Prediction Answer: {sample.get('pred_answer', '')}\n"
    return cot
```

---

## 关键依赖与配置

### 依赖项

```python
# 内部依赖
from thought.TableQA.utils.helper import table2string
from thought.TableQA.utils.llm import LLM

# 外部依赖
import json
import random
from typing import Dict, List, Any
```

### 配置文件

1. **错误树 JSON**：`critic/TableQA/tools/few_shot_critic.json`
2. **Prompt 模板**：`critic/TableQA/tools/instruction.py`
3. **Few-shot 案例集**：`critic/TableQA/tools/few_shot_judge.json`、`critic/TableQA/tools/few_shot_tree.json`

---

## 数据流与处理流程

### Critic 阶段流程

```
读取 Thought 结果
  ↓
遍历每个样本
  ↓
构建 Critic Prompt
  ├── Table
  ├── Question
  ├── Chain
  └── Prediction Answer
  ↓
调用 LLM 生成 Critique
  ↓
解析 Critique
  ├── max_step: 错误步骤编号
  ├── conclusion: 结论
  └── analysis: 分析
  ↓
执行错误树（可选）
  ├── 获取 error_route
  └── 定位错误类型
  ↓
保存 Critique 结果
  ↓
输出到 critic_log_list.pkl
```

---

## 测试与质量

### 当前状态

⚠️ **未发现系统化的测试文件**

### 建议的测试

1. **错误树更新测试**
   ```python
   # tests/test_update_tree.py
   def test_update_tree_success():
       error_tree = load_error_tree()
       sample = create_test_sample()
       updated_tree = update_tree(
           error_tree,
           sample,
           error_route='select_row_errors/condition_error',
           success=True
       )
       # 验证置信度增加
       node = locate_node(updated_tree, 'select_row_errors/condition_error')
       assert node['confidence_score'] > 0.5
       # 验证示例添加
       assert len(node['examples']) > 0
   ```

2. **Few-shot 检索测试**
   ```python
   # tests/test_retrieval.py
   def test_get_critique_few_shot():
       error_tree = load_error_tree()
       examples = get_critique_few_shot(
           error_tree,
           error_route='select_row_errors/condition_error',
           k=3
       )
       assert len(examples) <= 3
       for ex in examples:
           assert 'question' in ex
           assert 'critique' in ex
   ```

---

## 常见问题 (FAQ)

### Q1: 如何添加新的错误类型？

**A**：
1. 在 `few_shot_critic.json` 中添加新节点
2. 设置 `name`、`description`、`blueprint` 等字段
3. 添加初始示例（可选）
4. 更新 `tree_instruction` 中的错误类型列表

### Q2: Blueprint 是如何生成的？

**A**：
- **手动生成**：由人工编写错误模式摘要
- **自动生成**：使用 CuratorAgent 从多个相似案例中提取（见 `agents/curator_agent.py`）

### Q3: 如何调整置信度更新策略？

**A**：
在 `update_tree()` 函数中修改 `confidence_increment` 参数：
```python
# 成功时增加更多，失败时减少更多
if success:
    current_node['confidence_score'] = min(1.0, current_node['confidence_score'] + 0.2)
else:
    current_node['confidence_score'] = max(0.0, current_node['confidence_score'] - 0.15)
```

### Q4: 错误树是否会无限增长？

**A**：
- **当前版本**：错误树会持续增长
- **未来版本**：将实现 **Consolidation**（巩固）机制，将相似节点合并，并实现 **Active Forgetting**（主动遗忘）低置信度节点

### Q5: 如何评估错误树的质量？

**A**：
1. **覆盖率**：错误树是否覆盖了大部分错误类型？
2. **准确性**：Blueprint 是否准确描述了错误模式？
3. **置信度**：高置信度节点是否真的有效？
4. **检索效率**：Few-shot 检索是否返回了相关案例？

---

## 相关文件清单

### TableQA 工具

- `critic/TableQA/main.py` - 入口文件
- `critic/TableQA/tools/instruction.py` - Prompt 模板
- `critic/TableQA/tools/few_shot_critic.json` - 错误树 JSON
- `critic/TableQA/tools/few_shot_judge.json` - Judge Few-shot 案例
- `critic/TableQA/tools/few_shot_tree.json` - Tree Few-shot 案例
- `critic/TableQA/tools/update_tree.py` - 树更新逻辑
- `critic/TableQA/tools/get_info.py` - 信息检索工具
- `critic/TableQA/tools/multiprocess.py` - 多进程工具
- `critic/TableQA/tools/read_pkl.py` - 读取 pickle 文件
- `critic/TableQA/tools/few_shot_critic_json.py` - JSON 工具
- `critic/TableQA/tools/few_shot_judge_json.py` - JSON 工具
- `critic/TableQA/tools/few_shot_tree_json.py` - JSON 工具

### TableFV 工具

- `critic/TableFV/main.py` - 入口文件
- `critic/TableFV/tools/` - 与 TableQA 类似

---

**下一步建议**：

1. 实现 Consolidation 机制
2. 实现 Active Forgetting 机制
3. 优化 Blueprint 生成算法
4. 建立错误树质量评估指标
