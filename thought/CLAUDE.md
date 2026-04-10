[根目录](../CLAUDE.md) > **thought**

# Thought 模块

## 变更记录 (Changelog)

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-04-10 | 初始化 | 由架构师扫描生成 |

---

## 模块职责

Thought 模块是 Table-Critic 流水线的**第一阶段**，负责使用 LLM 对表格数据进行初始推理。通过动态生成操作链（function chain）逐步变换表格，最终得出预测答案。

核心流程：对每个样本，LLM 循环决定下一步操作（add_column / select_row / select_column / group_column / sort_column），执行操作后更新表格状态，直到决定 `<END>`，最后执行 `simple_query` 得出最终答案。

---

## 子模块索引

| 子模块 | 路径 | 职责 |
|--------|------|------|
| TableFV | `thought/TableFV/` | 事实验证任务的初始推理 |
| TableQA | `thought/TableQA/` | 问答任务的初始推理 |

---

## 入口与启动

### TableFV 入口
```bash
python thought/TableFV/main.py \
  --thought_results_dir results/thought/tabfact/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name \
  --first_n -1
```

### TableQA 入口
```bash
python thought/TableQA/main.py \
  --thought_results_dir results/thought/wikitq/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name \
  --first_n -1
```

---

## 关键依赖与配置

- 依赖 `utils/llm.py` 中的 `LLM` 类进行 API 调用
- 依赖 `utils/chain.py` 中的 `dynamic_chain_exec_with_cache_mp()` 执行动态链
- 依赖 `utils/load_data.py` 加载数据集
- 依赖 `operations/` 中的 5 种表格操作函数
- 缓存目录：`{thought_results_dir}/cache/case-{idx}.pkl`

---

## 对外接口

### 输出
- `final_result.pkl` -- 包含所有样本推理结果的列表，每个样本附带完整的 `chain`
- `acc.txt` -- Thought 阶段的准确率

### 数据格式
每个样本在 Thought 阶段后，`chain` 字段包含一系列操作记录：
```python
{
    "operation_name": "select_row",
    "parameter_and_conf": [("f_select_row(row 1, row 3)", -0.693)],
    "thought": "We need to find rows where..."  # 可选
}
```

---

## 相关文件清单

```
thought/
  TableFV/
    main.py              # FV 入口
    data/tabfact/        # TabFact 数据集
    utils/
      llm.py             # LLM 封装
      chain.py           # 动态链生成与执行（核心）
      helper.py          # table2string 等辅助函数
      load_data.py       # 数据集加载
      evaluate.py        # TabFact 准确率评估
    operations/          # 5 种表格操作
    third_party/         # 第三方代码
  TableQA/
    main.py              # QA 入口
    data/wikitq/         # WikiTQ 数据集
    utils/
      llm.py             # LLM 封装
      chain.py           # 动态链生成与执行（核心）
      helper.py          # 辅助函数
      load_data.py       # 数据集加载
      evaluate.py        # WikiTQ 准确率评估（含 Value 匹配）
    operations/          # 5 种表格操作
    third_party/         # 第三方代码
```
