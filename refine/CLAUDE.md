[根目录](../CLAUDE.md) > **refine**

# Refine 模块

## 变更记录 (Changelog)

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-04-10 | 初始化 | 由架构师扫描生成 |

---

## 模块职责

Refine 模块是 Table-Critic 流水线的**第三阶段**，负责根据 Critic 的反馈对推理链进行精炼和修正。这是框架的核心创新所在。

### 主流程：Tree-Based Refine (`main_tree_based.py`)
集成了 Judge、Tree、Critic 三个角色的完整循环：
1. **Judge** 判断答案是否正确
2. 若不正确，**Tree** 在错误树中定位错误路径
3. **Critic** 根据错误路径给出具体批评和错误步骤
4. 从错误步骤处**重新生成操作链**并执行到结束
5. 再次 Judge，循环最多 5 轮

### 实验性流程：Constraint-Based Refine (`main_constraint_based.py`)
基于约束诱导式剪枝的替代方案：
1. 从 Critic 结果中提取结构化约束（禁止的行/列/操作）
2. 在后续推理中强制遵守这些约束
3. 迭代多轮直到收敛

---

## 子模块索引

| 子模块 | 路径 | 职责 |
|--------|------|------|
| TableFV | `refine/TableFV/` | FV 任务的精炼 |
| TableQA | `refine/TableQA/` | QA 任务的精炼（含约束推理） |

---

## 入口与启动

### Tree-Based Refine（主流程）

```bash
# FV
python refine/TableFV/main_tree_based.py \
  --thought_results_dir results/thought/tabfact/{model_name} \
  --refine_results_dir results/refine/tabfact/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name

# QA
python refine/TableQA/main_tree_based.py \
  --thought_results_dir results/thought/wikitq/{model_name} \
  --refine_results_dir results/refine/wikitq/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name
```

### Constraint-Based Refine（实验性）

```bash
python refine/TableQA/main_constraint_based.py \
  --thought_results_dir results/thought/wikitq/{model_name} \
  --constraint_results_dir results/constraint_based/wikitq/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name \
  --max_rounds 5 \
  --temperature 0.5
```

---

## 关键文件说明

### utils/chain.py (核心)
最复杂的文件，包含：
- `judge_critic_refine_with_cache_mp()` -- Judge-Critic-Refine 完整循环的多进程执行
- `_judge_critic_refine_with_cache_mp_core()` -- 单样本的核心循环逻辑
- `dynamic_chain_exec_one_sample()` -- 从错误步骤处重新生成操作链
- `generate_prompt_for_critic_step()` -- 构建带批评的操作生成 prompt
- `generate_prompt_for_next_step()` -- 构建下一步操作的 prompt
- `get_critic_table_info()` -- 获取错误步骤前后的表格状态

### utils/extract_step.py
从 Critic 结论中解析错误步骤编号：
- `return_incorrect_max_step(sample)` -- 返回 `(incorrect_step, max_step)` 元组

### utils/evaluate.py
准确率评估函数（与 thought 模块相同）。

### utils/llm.py
LLM 封装（与 thought 模块结构相同）。

### utils/constraint_state.py (TableQA 专属)
约束状态管理类 `ConstraintState`：
- 存储禁止的行/列/操作/聚合约束
- 维护约束历史和统计

### utils/constraint_induction.py (TableQA 专属)
约束归纳器 `ConstraintInducer`：
- 从自然语言 critique 中提取错误类型
- 使用正则和 LLM 生成结构化约束

### utils/constraint_aware_chain.py (TableQA 专属)
约束感知的链执行逻辑。

---

## 对外接口

### 输出
- `final_result.pkl` -- 精炼后的样本列表
- `result.txt` -- 精炼后的准确率
- `cache/case-{idx}.pkl` -- 每个样本的精炼缓存

### 错误树更新
在精炼成功后，会通过 `update_error_tree()` 更新 `critic/{task}/tools/few_shot_critic.json`。

---

## 常见问题 (FAQ)

**Q: Refine 阶段依赖 Critic 的独立运行吗？**
A: 不依赖。`main_tree_based.py` 内部集成了 Critic 的功能，不需要先运行 `critic/main.py`。只需要 Thought 阶段的 `final_result.pkl` 作为输入。

**Q: 缓存机制如何工作？**
A: 每个样本的处理结果缓存为 `case-{idx}.pkl`。如果缓存存在，直接加载而不重新调用 LLM。删除 cache 目录可强制重新执行。

**Q: FV 和 QA 的 Refine 有什么区别？**
A: 核心逻辑相同，区别在于：
- prompt 用词：FV 用 "Statement"，QA 用 "Question"
- 评估函数：FV 用 `tabfact_match_func_for_samples`，QA 用 `wikitq_match_func_for_samples`
- 错误树路径：引用不同的 `few_shot_critic.json`

---

## 相关文件清单

```
refine/
  TableFV/
    main_tree_based.py           # Tree-Based Refine 入口
    utils/
      chain.py                   # Judge-Critic-Refine 循环（核心）
      extract_step.py            # 错误步骤解析
      evaluate.py                # TabFact 准确率评估
      helper.py                  # table2string 等辅助函数
      llm.py                     # LLM 封装
      read_pkl.py                # pkl 读取
    operations/                  # 5 种表格操作（含 critic 参数支持）
    third_party/                 # 第三方代码
  TableQA/
    main_tree_based.py           # Tree-Based Refine 入口
    main_constraint_based.py     # Constraint-Based Refine 入口（实验性）
    utils/
      chain.py                   # Judge-Critic-Refine 循环（核心）
      extract_step.py            # 错误步骤解析
      evaluate.py                # WikiTQ 准确率评估
      helper.py                  # 辅助函数
      llm.py                     # LLM 封装
      read_pkl.py                # pkl 读取
      constraint_state.py        # 约束状态管理
      constraint_induction.py    # 约束归纳器
      constraint_aware_chain.py  # 约束感知链执行
    operations/                  # 5 种表格操作
    third_party/                 # 第三方代码
    CONSTRAINT_BASED_README.md   # 约束推理说明文档
    QUICKSTART.md                # 快速开始指南
    IMPLEMENTATION_SUMMARY.md    # 实现总结
    BUG_FIXES.md                 # Bug 修复记录
```
