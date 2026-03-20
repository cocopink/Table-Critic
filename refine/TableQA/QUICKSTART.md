# 快速开始指南

## 前置条件

1. 已完成thought阶段的推理
2. 已安装所有依赖（见requirements.txt）
3. 配置好LLM API

## 快速开始

### 步骤1：准备环境

```bash
cd refine/TableQA
```

### 步骤2：运行约束诱导式推理

```bash
python main_constraint_based.py \
    --thought_results_dir ../../results/thought/wikitq \
    --constraint_results_dir ../../results/constraint_based/wikitq \
    --base_url http://localhost:11434/v1 \
    --openai_api_key EMPTY \
    --model_name qwen2.5-72b-instruct \
    --n_proc 4 \
    --chunk_size 10 \
    --max_rounds 5 \
    --strategy voting \
    --temperature 0.5
```

### 步骤3：查看结果

```bash
# 查看统计信息
python main_constraint_based.py evaluate_constraints \
    --constraint_results_dir ../../results/constraint_based/wikitq
```

## 示例输出

```
================================================================================
Constraint-Based Reasoning Statistics
================================================================================
Total samples: 100
Correct samples: 85
Accuracy: 85.00%

Constraint Statistics:
Total constraints added: 245
Average constraints per sample: 2.45
Total reasoning rounds: 312
Average rounds per sample: 3.12

Constraint Types:
  row_constraints: 98
  column_constraints: 87
  operation_constraints: 35
  aggregation_constraints: 25

Reasoning Round Distribution:
  1 round(s): 45 (45.0%)
  2 round(s): 30 (30.0%)
  3 round(s): 15 (15.0%)
  4 round(s): 7 (7.0%)
  5 round(s): 3 (3.0%)
```

## 参数调优建议

### 1. 进程数（n_proc）

- **小数据集**（<100样本）：n_proc=1-2
- **中等数据集**（100-1000样本）：n_proc=4-8
- **大数据集**（>1000样本）：n_proc=8-16

### 2. 最大轮次（max_rounds）

- **简单任务**：max_rounds=2-3
- **中等复杂度**：max_rounds=3-5
- **复杂任务**：max_rounds=5-7

### 3. 推理策略（strategy）

- **top**：更快，但可能不够准确
- **voting**：更准确，但计算成本更高

### 4. 温度（temperature）

- **低温度**（0.0-0.3）：更确定，适合简单任务
- **中等温度**（0.3-0.7）：平衡，适合大多数任务
- **高温度**（0.7-1.0）：更有创造性，适合复杂任务

## 常见问题

### Q1: 如何处理约束冲突？

A: 当前实现中，后添加的约束会覆盖先前的约束。可以通过修改`ConstraintState`类来实现更复杂的冲突解决策略。

### Q2: 如何调试约束归纳？

A: 设置`debug=True`参数，查看详细的推理过程和约束添加信息。

### Q3: 如何评估约束效果？

A: 使用`evaluate_constraints`命令，它会生成详细的约束分析报告。

### Q4: 如何提高约束归纳的准确性？

A: 
1. 改进Critic的few-shot示例
2. 使用更强大的LLM进行约束归纳
3. 添加更多的错误类型模式

## 下一步

1. 阅读[`CONSTRAINT_BASED_README.md`](CONSTRAINT_BASED_README.md)了解详细信息
2. 查看[`constraint_state.py`](utils/constraint_state.py)了解约束状态管理
3. 查看[`constraint_induction.py`](utils/constraint_induction.py)了解约束归纳机制
4. 查看[`constraint_aware_chain.py`](utils/constraint_aware_chain.py)了解约束感知推理

## 故障排除

### 问题1：ModuleNotFoundError

**错误信息**：
```
ModuleNotFoundError: No module named 'utils.constraint_state'
```

**解决方案**：
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题2：缓存问题

**错误信息**：
```
Error loading cache: ...
```

**解决方案**：
```bash
python main_constraint_based.py \
    --clear_cache \
    ...
```

### 问题3：内存不足

**错误信息**：
```
MemoryError: ...
```

**解决方案**：
- 减少`n_proc`
- 减少`chunk_size`
- 增加`max_rounds`以减少中间结果存储

## 性能优化

### 1. 使用缓存

```bash
python main_constraint_based.py \
    --use_cache True \
    ...
```

### 2. 批量处理

```bash
python main_constraint_based.py \
    --first_n 100 \
    --n_proc 8 \
    --chunk_size 20 \
    ...
```

### 3. 并行处理

```bash
python main_constraint_based.py \
    --n_proc 16 \
    --chunk_size 50 \
    ...
```

## 扩展功能

### 1. 自定义约束类型

在[`constraint_induction.py`](utils/constraint_induction.py)中添加新的错误类型模式：

```python
self.error_type_patterns["custom_error"] = [
    r"your pattern here"
]
```

### 2. 自定义约束检查

在[`constraint_aware_chain.py`](utils/constraint_aware_chain.py)中修改`_is_operation_forbidden_by_constraints`函数。

### 3. 自定义约束传播

在[`constraint_state.py`](utils/constraint_state.py)中添加新的约束传播逻辑。

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

Apache License 2.0
