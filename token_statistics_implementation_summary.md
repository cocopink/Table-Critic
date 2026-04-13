# Token统计功能实施总结

## ✅ 实施完成

已成功为`run_QA.sh`和`run_FV.sh`脚本添加了token统计功能（方案A - 简单统计）。

## 📝 修改的文件

### LLM类文件 (4个)
- `thought/TableQA/utils/llm.py`
- `thought/TableFV/utils/llm.py`
- `refine/TableQA/utils/llm.py`
- `refine/TableFV/utils/llm.py`

### 主程序文件 (4个)
- `thought/TableQA/main.py`
- `thought/TableFV/main.py`
- `refine/TableQA/main_tree_based.py`
- `refine/TableFV/main_tree_based.py`

## 🔧 核心功能

### 1. LLM类增强
每个LLM类现在包含：
- **Token计数器**：`input_tokens`、`output_tokens`
- **自动统计**：在API调用时自动提取usage信息
- **查询方法**：`get_token_usage()`返回统计结果
- **保存方法**：`save_token_usage(filepath)`保存到JSON文件

### 2. 主程序集成
每个主程序现在会：
- 在控制台显示token统计信息
- 保存详细的JSON统计文件
- 与现有accuracy统计无缝集成

## 📊 输出格式

### 控制台输出
```
Thought Stage Token Usage:
  Input Tokens:  150000
  Output Tokens: 50000
  Total Tokens: 200000
Token usage saved to results/thought/wikitq/gpt-5.4/token_usage.json
```

### JSON文件格式
```json
{
  "input_tokens": 150000,
  "output_tokens": 50000,
  "total_tokens": 200000,
  "timestamp": "2026-04-02 10:30:00",
  "model": "gpt-5.4"
}
```

## 📁 生成的统计文件

运行脚本后会自动生成：
- `results/thought/wikitq/{model_name}/token_usage.json`
- `results/refine/wikitq/{model_name}/token_usage.json`
- `results/thought/tabfact/{model_name}/token_usage.json`
- `results/refine/tabfact/{model_name}/token_usage.json`

## ⚠️ 注意事项

### 多进程限制
当前方案A在多进程场景下统计不精确：
- ✅ 单进程部分（Clarifier、Controller）：精确统计
- ⚠️ 多进程部分（dynamic_chain、fixed_chain）：仅统计主进程

### API兼容性
代码包含容错处理：
- 使用`hasattr(gpt_responses, 'usage')`检查
- 对于不返回usage信息的API，不会报错
- 建议测试验证目标API是否返回usage信息

## 🧪 测试建议

### 快速测试
```bash
# 修改run_QA.sh中的first_n参数
first_n=10  # 只处理10个样本进行测试

# 运行测试
bash run_QA.sh
```

### 验证点
1. 检查控制台是否显示token统计
2. 检查是否生成了`token_usage.json`文件
3. 验证JSON文件格式是否正确
4. 确认不影响原有功能

## 🚀 后续优化

### 方案B（精确统计）
如需多进程精确统计，可实施方案B：
- 使用多进程共享计数器
- 修改chain.py中的多进程函数
- 预计额外工作量：1.5小时

### 统计增强
可考虑添加：
- 按操作类型分类统计
- 实时token使用监控
- 成本估算功能
- 历史趋势分析

## 📈 预期效果

### 成本监控
- 了解各阶段token消耗
- 估算API调用成本
- 优化参数配置

### 性能分析
- 对比不同模型的token效率
- 识别token消耗热点
- 指导算法优化

---

*实施完成时间：2026-04-02*
*实施方案：方案A（简单统计）*
*状态：已完成，待测试*
