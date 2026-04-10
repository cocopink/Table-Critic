[根目录](../CLAUDE.md) > **critic**

# Critic 模块

## 变更记录 (Changelog)

| 日期 | 操作 | 说明 |
|------|------|------|
| 2026-04-10 | 初始化 | 由架构师扫描生成 |

---

## 模块职责

Critic 模块是 Table-Critic 流水线的**第二阶段**，负责对 Thought 阶段的推理结果进行批评分析。在当前主流程（`main_tree_based.py`）中，Critic 阶段的功能已**内联到 Refine 模块**中，但独立的 `critic/main.py` 仍可单独运行，用于生成批评日志。

Critic 包含三个子角色：
1. **Critic** -- 逐步分析推理链，找出第一个错误步骤，给出结论 `[Incorrect] Step N` 或 `[Correct]`
2. **Judge** -- 判断最终答案是否正确，给出 `[Correct]` 或 `[Incorrect]`
3. **Tree** -- 在错误树中定位错误路径，如 `sub-table error -> row error`

---

## 子模块索引

| 子模块 | 路径 | 职责 |
|--------|------|------|
| TableFV | `critic/TableFV/` | FV 任务的批评分析 |
| TableQA | `critic/TableQA/` | QA 任务的批评分析 |

---

## 入口与启动

### 独立运行（可选）

```bash
python critic/TableFV/main.py \
  --thought_results_dir results/thought/tabfact/{model_name} \
  --critic_results_dir results/critic/tabfact/{model_name} \
  --base_url $base_url \
  --openai_api_key $api_key \
  --model_name $model_name
```

**注意**：在当前主流程（`run_FV.sh` / `run_QA.sh`）中，Critic 阶段被注释掉，其功能已集成到 Refine 的 `main_tree_based.py` 中。

---

## 关键文件说明

### tools/instruction.py
定义了三种角色的系统提示词（prompt）：
- `critic_instruction` -- 逐步分析推理步骤，定位错误
- `judge_instruction` -- 判断答案正确性
- `tree_instruction` -- 在错误树中定位错误路径

### tools/get_info.py
核心 prompt 构建逻辑：
- `get_cot_for_critic()` -- 构建 Critic 的 Chain-of-Thought prompt
- `get_cot_for_judge()` -- 构建 Judge 的 prompt
- `get_cot_for_tree()` -- 构建 Tree 的 prompt（包含错误树结构）
- `get_critic_few_shot()` -- 根据错误路径从错误树中检索 few-shot 示例
- `get_tree_few_shot()` -- 获取 Tree 的 few-shot 示例
- `get_judge_few_shot()` -- 获取 Judge 的 few-shot 示例

### tools/update_tree.py
错误树的动态维护：
- `update_error_tree()` -- 当 Critic 修正成功时，将新的批评案例插入错误树
- `vertical_expansion()` -- 垂直扩展：在叶节点处尝试拆分为子类别
- `horizontal_expansion()` -- 水平扩展：在错误树中添加新的错误路径分支

### tools/few_shot_critic.json
错误树数据结构，形如：
```json
{
    "sub-table error": {
        "row error": ["示例1", "示例2", ...],
        "column error": ["示例1", "示例2", ...]
    },
    "final query error": ["示例1", ...]
}
```

### tools/multiprocess.py
多进程执行批评分析的工具函数。

---

## 对外接口

### 输出（独立运行时）
- `critic_log_list.pkl` -- 包含每个样本的批评结果（critique 文本、conclusion、max_step）

### 被 Refine 模块调用的接口
- `critic_exec_one_sample(sample, error_route, llm, llm_options)` -- 对单个样本执行批评
- `judge_exec_one_sample(sample, llm, llm_options)` -- 对单个样本执行判断
- `tree_exec_one_sample(sample, llm, llm_options)` -- 对单个样本执行错误树定位
- `update_error_tree(sample, error_route, error_tree_json, llm, llm_options, lock)` -- 更新错误树

---

## 相关文件清单

```
critic/
  TableFV/
    main.py                          # Critic 独立入口
    tools/
      __init__.py                    # 导出 critic_exec_one_sample 等
      instruction.py                 # 三种角色的系统提示词
      get_info.py                    # Prompt 构建与 few-shot 检索
      update_tree.py                 # 错误树动态维护
      multiprocess.py                # 多进程执行工具
      read_pkl.py                    # pkl 读取
      few_shot_critic.json           # Critic 错误树（动态更新）
      few_shot_judge.json            # Judge few-shot 示例
      few_shot_tree.json             # Tree few-shot 示例
      few_shot_critic_json.py        # 错误树 JSON 生成脚本
      few_shot_judge_json.py         # Judge 示例 JSON 生成脚本
      few_shot_tree_json.py          # Tree 示例 JSON 生成脚本
  TableQA/
    main.py                          # Critic 独立入口
    tools/                           # 结构同 TableFV
```
