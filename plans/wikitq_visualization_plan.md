# WikiTableQuestions 结果可视化规划

## 任务概述

为以下两个结果目录创建可视化脚本：
- **Thought阶段**: `/home/ubuntu/mnt/lx/Table-Critic/results/thought/wikitq/qwen3:32b/cache`
- **Refine阶段**: `/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/qwen3:32b/cache`

参考实现：`visualize_results.py` (TabFact数据集)

## 现有实现分析

### 1. visualize_results.py (TabFact实现)
- **数据集**: TabFact (表格事实验证)
- **评估方式**: 二分类 (Yes/No)
- **标签字段**: `label` (0或1)
- **支持阶段**: Thought, Critic, Refine
- **主要功能**:
  - 加载pkl文件（支持cache目录和final_result.pkl）
  - 统计操作类型分布
  - 计算预测准确率
  - 显示详细样本信息
  - 对比不同阶段结果

### 2. visualize_wikitq_results.py (WikiTQ实现 - 已存在)
- **数据集**: WikiTableQuestions (表格问答)
- **评估方式**: 答案匹配
- **标签字段**: `ids` (样本ID)
- **支持阶段**: Thought, Refine
- **主要功能**:
  - 加载目标答案映射 (target_values_map)
  - 使用wikitq_match_func进行答案匹配
  - 统计操作类型和答案长度分布
  - 计算准确率并对比提升
  - 显示详细样本信息

## 数据结构分析

### Thought阶段样本结构
```python
{
    'id': str,
    'ids': str,  # WikiTQ使用ids字段
    'statement': str,  # 问题
    'table_caption': str,
    'table_text': List[List],  # 表格数据
    'chain': List[Dict],  # 推理链
        # 每个操作包含: operation_name, thought, parameter_and_conf
}
```

### Refine阶段样本结构
```python
{
    # Thought阶段的所有字段
    'critique': str,  # Critic分析结果
    'conclusion': str,
    'max_step': int,
    'judge': str,  # Judge判断结果
    'tree': str,  # Tree错误路由
}
```

## 已知准确率数据

| 阶段 | 准确率 | 提升幅度 |
|------|--------|----------|
| Thought | 81.98% | - |
| Refine | 83.40% | +1.42% |

## 规划方案

### 方案A: 使用现有脚本 (推荐)

**优点**:
- `visualize_wikitq_results.py` 已经存在且配置正确
- 已经针对WikiTQ数据集优化
- 支持准确率计算和对比
- 代码完整且经过测试

**操作**:
- 直接运行 `visualize_wikitq_results.py`
- 如需调整，可以修改max_samples参数

### 方案B: 创建新脚本

如果需要创建新的可视化脚本，可以基于以下设计：

#### 脚本名称
`visualize_wikitq_comparison.py`

#### 主要功能模块

1. **数据加载模块**
   - 加载cache目录中的pkl文件
   - 支持final_result.pkl（如果存在）
   - 加载目标答案映射

2. **统计分析模块**
   - 样本数量统计
   - 操作类型分布
   - 推理链长度分布
   - 答案长度分布
   - 准确率计算

3. **对比分析模块**
   - Thought vs Refine 准确率对比
   - 操作类型分布对比
   - 推理链长度对比
   - 提升幅度计算

4. **详细展示模块**
   - 显示前N个样本的详细信息
   - 包含表格内容、推理链、预测答案
   - 标注答案正确性

5. **可视化输出**
   - 控制台输出格式化统计信息
   - 可选：保存结果到文件

#### 脚本结构

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiTableQuestions 结果对比可视化脚本
专门用于对比 Thought 和 Refine 两个阶段的结果
"""

import os
import pickle
import glob
from collections import defaultdict
import sys

# 添加评估模块路径
sys.path.append('thought/TableQA')
from utils.evaluate import to_value_list, check_denotation, tsv_unescape_list

# 配置路径
THOUGHT_PATH = '/home/ubuntu/mnt/lx/Table-Critic/results/thought/wikitq/qwen3:32b/cache'
REFINE_PATH = '/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/qwen3:32b/cache'
TAGGED_DATA_PATH = 'thought/TableQA/data/wikitq/tagged_data'

# 主要函数
def load_target_values_map(...)
def load_samples_from_directory(...)
def analyze_samples(...)
def calculate_accuracy(...)
def compare_stages(...)
def display_sample_details(...)
def main(...)
```

#### 输出格式示例

```
================================================================================
🎯 WikiTableQuestions 结果对比可视化
================================================================================

📊 阶段对比分析
================================================================================

阶段对比:
--------------------------------------------------------------------------------
阶段                 样本数           Cache文件数      目录
--------------------------------------------------------------------------------
Thought              200              200              results/thought/wikitq/qwen3:32b/cache
                     来源: cache目录
Refine               200              200              results/refine/wikitq/qwen3:32b/cache
                     来源: cache目录
--------------------------------------------------------------------------------

################################################################################
📁 THOUGHT 阶段结果目录: results/thought/wikitq/qwen3:32b/cache
################################################################################

📦 找到 200 个pkl文件

📈 统计信息 (基于 200 个样本):
  总文件数: 200
  已分析样本数: 200
  有推理链: 200
  平均链长度: 4.52 步
  预测准确率: 0.8198 (164/200)

  操作类型分布:
    select_column: 800
    select_row: 600
    final_query: 200
    ...

################################################################################
📁 REFINE 阶段结果目录: results/refine/wikitq/qwen3:32b/cache
################################################################################

📈 统计信息 (基于 200 个样本):
  总文件数: 200
  已分析样本数: 200
  有推理链: 200
  有Critic分析: 200
  有Judge分析: 200
  有Tree分析: 200
  平均链长度: 4.67 步
  预测准确率: 0.8340 (167/200)

  操作类型分布:
    select_column: 820
    select_row: 610
    final_query: 200
    ...

################################################################################
📊 准确率对比
################################################################################

阶段                 准确率          正确数          总数
--------------------------------------------------------------------------------
Thought              0.8198          164             200
Refine               0.8340          167             200
--------------------------------------------------------------------------------

📈 准确率提升:
  Thought: 0.8198
  Refine:  0.8340
  提升:    +0.0142 (+1.73%)

================================================================================
✅ 分析完成！
================================================================================
```

## 实现步骤

### 步骤1: 确认需求
- [ ] 确认是否使用现有脚本 `visualize_wikitq_results.py`
- [ ] 确认是否需要创建新的可视化脚本
- [ ] 确认输出格式和详细程度

### 步骤2: 实现脚本 (如果需要)
- [ ] 创建脚本文件 `visualize_wikitq_comparison.py`
- [ ] 实现数据加载函数
- [ ] 实现统计分析函数
- [ ] 实现对比分析函数
- [ ] 实现详细展示函数
- [ ] 实现主函数

### 步骤3: 测试验证
- [ ] 测试脚本是否能正确加载pkl文件
- [ ] 验证准确率计算是否正确
- [ ] 检查输出格式是否符合预期

### 步骤4: 优化改进 (可选)
- [ ] 添加更多统计指标
- [ ] 优化输出格式
- [ ] 添加可视化图表（如需要）

## 关键注意事项

1. **数据集差异**: WikiTQ是问答任务，不是分类任务，需要使用答案匹配而非简单的标签比较
2. **评估函数**: 必须使用 `thought/TableQA/utils/evaluate.py` 中的评估函数
3. **路径配置**: 确保所有路径正确，特别是tagged_data目录
4. **性能考虑**: 如果样本数量很大，考虑限制显示的样本数量
5. **错误处理**: 添加适当的异常处理，防止因单个样本加载失败导致整个程序崩溃

## 推荐方案

**推荐使用现有的 `visualize_wikitq_results.py`**，原因如下：

1. ✅ 已经完整实现了所有需要的功能
2. ✅ 已经配置了正确的路径
3. ✅ 已经针对WikiTQ数据集优化
4. ✅ 已经包含准确率计算和对比功能
5. ✅ 代码已经过测试

如果现有脚本不能满足需求，可以考虑：
- 修改现有脚本的参数（如max_samples）
- 基于现有脚本创建简化版本
- 添加额外的统计指标或可视化功能
