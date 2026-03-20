# Constraint-Induced Table-Critic for Pruned Table Reasoning

## 概述

本实现基于Table-Critic框架，提出了一种**约束诱导式剪枝推理**方法。该方法的核心思想是将Critic的判别结果转化为可执行的结构性约束，并将其注入后续推理过程，从而对表格推理的可行空间进行逐步收缩。

## 核心创新

### 1. 约束归纳（Constraint Induction）

将Critic的自然语言判别结果转化为结构化约束：
- **错误类型识别**：row_error, column_error, aggregation_error, entity_confusion
- **结构定位**：提取被错误选择的行、列或操作
- **约束生成**：生成否定式约束规则

### 2. 约束状态管理（Constraint State）

维护推理过程中的约束集合：
- **行约束**：禁止选择的行集合
- **列约束**：禁止选择的列集合
- **操作约束**：禁止执行的操作序列
- **聚合约束**：强制修正的聚合作用域

### 3. 约束感知推理（Constraint-Aware Reasoning）

在推理过程中应用约束：
- **约束注入**：将约束信息注入到prompt中
- **约束检查**：在执行操作前检查是否违反约束
- **约束传播**：约束在多轮推理中有效传播

## 文件结构

```
refine/TableQA/
├── utils/
│   ├── constraint_state.py         # 约束状态管理
│   ├── constraint_induction.py      # 约束归纳器
│   ├── constraint_aware_chain.py   # 约束感知推理执行
│   ├── chain.py                  # 原始推理链（保持兼容）
│   └── ...
├── operations/
│   ├── select_row.py             # 行选择操作
│   ├── select_column.py          # 列选择操作
│   └── ...
└── main_constraint_based.py       # 主入口
```

## 使用方法

### 1. 基本使用

```bash
python main_constraint_based.py \
    --thought_results_dir results/thought/wikitq \
    --constraint_results_dir results/constraint_based/wikitq \
    --base_url <your_base_url> \
    --openai_api_key <your_api_key> \
    --model_name qwen2.5-72b-instruct \
    --n_proc 4 \
    --chunk_size 10 \
    --max_rounds 5 \
    --strategy voting
```

### 2. 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--thought_results_dir` | 初始推理结果目录 | results/thought/wikitq |
| `--constraint_results_dir` | 约束推理结果目录 | results/constraint_based/wikitq |
| `--base_url` | LLM API base URL | "" |
| `--openai_api_key` | LLM API密钥 | "EMPTY" |
| `--model_name` | 模型名称 | qwen2.5-72b-instruct |
| `--first_n` | 处理前N个样本（-1表示全部） | -1 |
| `--n_proc` | 进程数 | 1 |
| `--chunk_size` | 块大小 | 1 |
| `--max_rounds` | 最大推理轮次 | 5 |
| `--strategy` | 推理策略（"top"或"voting"） | voting |
| `--temperature` | 温度参数 | 0.5 |
| `--use_cache` | 是否使用缓存 | True |
| `--clear_cache` | 是否清除缓存 | False |

### 3. 评估结果

```bash
python main_constraint_based.py \
    evaluate_constraints \
    --constraint_results_dir results/constraint_based/wikitq \
    --output_file constraint_analysis.json
```

## 工作流程

```
1. 初始推理（thought phase）
   ↓
2. Critic评估
   ↓
3. 约束归纳
   - 分析critique
   - 识别错误类型
   - 提取结构定位
   - 生成约束规则
   ↓
4. 约束感知推理
   - 应用约束到prompt
   - 检查操作是否违反约束
   - 执行推理
   ↓
5. 重复2-4直到正确或达到最大轮次
```

## 约束类型

### 1. 行约束（Row Constraints）

禁止选择特定的行：

```python
constraint_state.add_forbidden_rows(
    rows=["row 1", "row 3"],
    error_type="row_error",
    source_step=1
)
```

**Prompt中的表示**：
```
DO NOT select the following rows: row 1, row 3
```

### 2. 列约束（Column Constraints）

禁止选择特定的列：

```python
constraint_state.add_forbidden_columns(
    columns=["column_name"],
    error_type="column_error",
    source_step=2
)
```

**Prompt中的表示**：
```
DO NOT select the following columns: column_name
```

### 3. 操作约束（Operation Constraints）

禁止执行特定的操作序列：

```python
constraint_state.add_forbidden_operation(
    operation_name="select_row",
    parameters=["row 1", "row 2"],
    error_type="entity_confusion",
    source_step=1
)
```

**Prompt中的表示**：
```
DO NOT perform the following operations: select_row(row 1, row 2)
```

### 4. 聚合约束（Aggregation Constraints）

强制修正聚合作用域：

```python
constraint_state.add_aggregation_constraint(
    constraint_key="group_column",
    constraint_value="correct_column",
    error_type="aggregation_error",
    source_step=3
)
```

**Prompt中的表示**：
```
Aggregation constraints: group_column should be 'correct_column'
```

## 示例

### 示例1：行错误

**Critique**：
```
Row 8 was omitted in Step 1, despite satisfying the criteria. 
The reasoning only considers rows 1, 2, and 4, which makes Step 1 incomplete.
```

**诱导的约束**：
```python
constraint_state.add_forbidden_rows(
    rows=["row 1", "row 2", "row 4"],  # 错误选择的行
    error_type="row_error",
    source_step=1
)
```

**效果**：后续推理将避免选择这些行。

### 示例2：列错误

**Critique**：
```
Step 2 incorrectly filters out the columns. The question asks for the entity 
that came in first, which means we need to retain the 'horse', 'jockey', 
'trainer', and 'owner' columns.
```

**诱导的约束**：
```python
constraint_state.add_forbidden_columns(
    columns=["finished"],  # 错误过滤的列
    error_type="column_error",
    source_step=2
)
```

**效果**：后续推理将保留必要的列。

## 优势

### 1. 推理空间收缩

- 约束集合单调增加
- 搜索空间逐步收缩
- 避免重复探索错误路径

### 2. 推理稳定性提升

- 约束提供明确的指导
- 减少随机性
- 提高一致性

### 3. 计算效率优化

- 减少不必要的推理步骤
- 避免重复的LLM调用
- 提高整体效率

## 与传统方法的对比

| 特性 | 传统多轮纠错 | 约束诱导式推理 |
|------|-------------|----------------|
| 错误处理 | 事后重试 | 预防性约束 |
| 搜索空间 | 保持不变 | 逐步收缩 |
| 约束传播 | 无 | 有 |
| 计算效率 | 较低 | 较高 |
| 推理稳定性 | 较低 | 较高 |

## 实验建议

### 1. 基线对比

- 原始Table-Critic方法
- 约束诱导式方法
- 消融实验（无约束归纳）

### 2. 评估指标

- 准确率（Accuracy）
- 平均推理轮次（Average Rounds）
- 平均约束数量（Average Constraints）
- 计算时间（Computation Time）

### 3. 数据集

- WikiTableQuestions
- TabFact
- 自定义数据集

## 扩展方向

### 1. 约束优先级

为不同类型的约束设置优先级，处理约束冲突。

### 2. 约束学习

从历史推理中学习约束模式，提高约束归纳的准确性。

### 3. 约束传播

探索约束在不同样本之间的传播机制。

### 4. 约束可视化

开发可视化工具，展示约束的添加和效果。

## 注意事项

1. **约束准确性**：约束归纳的准确性直接影响推理效果
2. **约束冲突**：多个约束可能冲突，需要优先级机制
3. **过度约束**：过多的约束可能限制推理的灵活性
4. **计算开销**：约束检查可能增加推理时间

## 引用

如果使用本实现，请引用：

```bibtex
@article{constraint_induced_table_critic,
  title={Constraint-Induced Table-Critic for Pruned Table Reasoning},
  author={Your Name},
  journal={arXiv preprint},
  year={2025}
}
```

## 联系方式

如有问题或建议，请联系：
- Email: your.email@example.com
- GitHub: https://github.com/yourusername/table-critic
