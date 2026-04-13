# Token统计实现计划

## 📋 项目概述
为`run_QA.sh`和`run_FV.sh`脚本添加token用量统计功能，追踪thought阶段和refine阶段的API调用成本。

### 🎯 实现目标
- 统计每个阶段的input/output token数量
- 计算平均token用量和总用量
- 生成JSON格式的统计报告
- 支持多进程场景的精确统计

## 📊 当前状态分析

**代码结构**：
- `run_QA.sh` → `thought/TableQA/main.py` + `refine/TableQA/main_tree_based.py`
- `run_FV.sh` → `thought/TableFV/main.py` + `refine/TableFV/main_tree_based.py`

**LLM调用点**：
1. Clarifier处理（单进程）
2. 动态链执行（多进程，n_proc=8）
3. 最终查询（多进程，n_proc=4）
4. Controller循环（单进程）

**现有问题**：
- ❌ 无token统计功能
- ❌ OpenAI API的`usage`字段未被提取
- ❌ 多进程场景下统计困难

## 🔧 实现方案

### 方案A：简单统计（当前实施方案）
**特点**：实现简单，适合快速评估
**局限**：多进程场景下统计不精确

**需要修改的文件**：
1. `thought/TableQA/utils/llm.py`
2. `thought/TableFV/utils/llm.py`
3. `refine/TableQA/utils/llm.py`
4. `refine/TableFV/utils/llm.py`
5. `thought/TableQA/main.py`
6. `thought/TableFV/main.py`
7. `refine/TableQA/main_tree_based.py`
8. `refine/TableFV/main_tree_based.py`

**核心改动**：
- 在LLM类中添加token计数器
- 在API响应中提取usage信息
- 在主程序中保存统计结果

### 方案B：精确统计（未来可选）
**特点**：使用多进程共享计数器，统计精确
**复杂度**：需要修改多进程相关函数

## 📝 实施步骤

### 阶段1：基础LLM类修改（约30分钟）
1. 修改4个LLM类，添加token统计功能
2. 在`generate_plus_with_score`方法中提取usage信息
3. 添加`get_token_usage()`和`save_token_usage()`方法

### 阶段2：主程序集成（约20分钟）
1. 在4个main文件中调用token统计保存
2. 添加控制台输出显示token消耗
3. 生成JSON格式的统计文件

### 阶段3：测试验证（约10分钟）
1. 使用小数据集测试（first_n=10）
2. 验证token统计准确性
3. 检查JSON文件生成

## 📈 预期输出

**生成的统计文件**：
```
results/thought/wikitq/{model_name}/token_usage.json
results/refine/wikitq/{model_name}/token_usage.json
results/thought/tabfact/{model_name}/token_usage.json
results/refine/tabfact/{model_name}/token_usage.json
```

**统计内容**：
```json
{
  "input_tokens": 150000,
  "output_tokens": 50000,
  "total_tokens": 200000,
  "avg_tokens_per_sample": 2000,
  "timestamp": "2026-04-02 10:30:00",
  "model": "gpt-5.4",
  "stage": "thought"
}
```

## ⏱️ 工作量评估

| 方案 | 代码量 | 时间 | 难度 | 精确度 |
|------|--------|------|------|--------|
| 方案A | ~100行 | 1小时 | ⭐ | 中等 |
| 方案B | ~200行 | 2.5小时 | ⭐⭐ | 高 |

## 🎯 实施进度

### ✅ 已完成
- 计划文档创建
- 代码结构分析

### 🔄 进行中
- 方案A实施

### 📋 待办
- 测试验证
- 文档完善

## 📌 注意事项

1. **API兼容性**：部分API可能不返回usage信息
2. **多进程安全**：当前方案在多进程下统计不精确
3. **向后兼容**：修改不影响现有功能
4. **成本计算**：可根据token统计估算API成本

## 🚀 实施记录

### 2026-04-02
- ✅ 创建计划文档
- ✅ 完成方案A（简单统计）实施
- ✅ 修改LLM类添加token统计功能（4个文件）
- ✅ 修改主程序集成统计功能（4个文件）

### 已修改的文件清单
**LLM类文件（4个）：**
- `thought/TableQA/utils/llm.py`
- `thought/TableFV/utils/llm.py`
- `refine/TableQA/utils/llm.py`
- `refine/TableFV/utils/llm.py`

**主程序文件（4个）：**
- `thought/TableQA/main.py`
- `thought/TableFV/main.py`
- `refine/TableQA/main_tree_based.py`
- `refine/TableFV/main_tree_based.py`

### 核心修改内容
1. **LLM类修改**：
   - 添加`input_tokens`和`output_tokens`计数器
   - 在`generate_plus_with_score`和`generate_plus_with_score_final_query`中提取token使用信息
   - 添加`get_token_usage()`和`save_token_usage()`方法

2. **主程序修改**：
   - 在程序结束时显示token统计信息
   - 保存token统计到JSON文件
   - 与现有的accuracy统计并行输出

---

*文档创建时间：2026-04-02*
*版本：v1.0*
*状态：实施中*
