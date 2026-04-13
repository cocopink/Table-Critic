# Table-Critic 代码合并指南

## 概述

本项目将原始 Table-Critic 代码与新功能代码（Controller、ClarifierAgent、Multi-Agent、Blueprint 等）合并到同一代码库中，通过 bool 开关实现两种模式的无缝切换。

**核心原则：新旧代码在有区别的地方完全遵从自己对应的那套逻辑，不混用。**

---

## 模式切换开关

| 开关 | 适用阶段 | True = 新模式 | False = 原始模式 |
|------|----------|--------------|----------------|
| `use_clarifier` | thought | 运行 ClarifierAgent（schema anchoring） | 跳过 ClarifierAgent |
| `use_controller` | refine | 使用 Controller 策略驱动精炼 | 使用原始 chain 管线 |
| `use_blueprint` | update_tree | 生成 blueprint，存储 dict 格式 `{"blueprint": ..., "content": ...}` | 直接存储纯字符串 `critic_template` |

### 开关传递链

```
run_QA.sh / run_FV.sh
  └─ MODE="new" / "orig"
      ├─ thought/main.py --use_clarifier <bool>
      │    └─ 控制 ClarifierAgent 是否执行
      └─ refine/main_tree_based.py --use_controller <bool> --use_clarifier <bool>
           ├─ use_controller=False → chain.py → update_error_tree(use_blueprint=False)
           └─ use_controller=True  → controller.py → update_error_tree(use_blueprint=True)
```

---

## 如何运行

### 通过 Shell 脚本（推荐）

修改脚本顶部的 `MODE` 变量即可：

```bash
# 新模式（Controller + ClarifierAgent + Blueprint）
MODE="new"   # 默认值

# 原始模式
MODE="orig"
```

**TableQA (WikiTQ):**
```bash
bash run_QA.sh
```

**TableFV (TabFact):**
```bash
bash run_FV.sh
```

### 直接调用 Python

**原始模式 — TableQA:**
```bash
# 1. Thought 阶段（无 ClarifierAgent）
python thought/TableQA/main.py \
  --thought_results_dir "results/orig/thought/wikitq/model_name" \
  --base_url "https://api.example.com/v1" \
  --openai_api_key "YOUR_KEY" \
  --model_name "model_name" \
  --first_n -1 \
  --use_clarifier False

# 2. Refine 阶段（原始 chain 管线）
python refine/TableQA/main_tree_based.py \
  --thought_results_dir "results/orig/thought/wikitq/model_name" \
  --refine_results "results/orig/refine/wikitq/model_name" \
  --base_url "https://api.example.com/v1" \
  --openai_api_key "YOUR_KEY" \
  --model_name "model_name" \
  --first_n -1 \
  --use_controller False \
  --use_clarifier False
```

**新模式 — TableQA:**
```bash
# 1. Thought 阶段（运行 ClarifierAgent）
python thought/TableQA/main.py \
  --thought_results_dir "results/new/thought/wikitq/model_name" \
  --base_url "https://api.example.com/v1" \
  --openai_api_key "YOUR_KEY" \
  --model_name "model_name" \
  --first_n -1 \
  --use_clarifier True

# 2. Refine 阶段（Controller 策略驱动）
python refine/TableQA/main_tree_based.py \
  --thought_results_dir "results/new/thought/wikitq/model_name" \
  --refine_results "results/new/refine/wikitq/model_name" \
  --base_url "https://api.example.com/v1" \
  --openai_api_key "YOUR_KEY" \
  --model_name "model_name" \
  --first_n -1 \
  --use_controller True \
  --use_clarifier True
```

TableFV 同理，将 `TableQA` 替换为 `TableFV`，`wikitq` 替换为 `tabfact`。

---

## 两种模式的关键区别

### 1. Thought 阶段

| 特性 | 原始模式 (`use_clarifier=False`) | 新模式 (`use_clarifier=True`) |
|------|----------------------------------|-------------------------------|
| ClarifierAgent | 不执行，不 import agents 模块 | 执行 schema anchoring |
| dataset | 直接使用原始 dataset | ClarifierAgent 处理后输出 |
| 结果目录 | `results/orig/thought/...` | `results/new/thought/...` |

### 2. Refine 阶段

| 特性 | 原始模式 (`use_controller=False`) | 新模式 (`use_controller=True`) |
|------|-----------------------------------|-------------------------------|
| 精炼策略 | 固定 chain 管线 | Controller 动态决策 |
| 错误树更新 | `chain.py` → `update_error_tree(use_blueprint=False)` | `controller.py` → `update_error_tree(use_blueprint=True)` |
| CriticTree JSON 格式 | 叶节点存储纯字符串 | 叶节点存储 dict `{"blueprint": ..., "content": ...}` |
| 结果目录 | `results/orig/refine/...` | `results/new/refine/...` |

### 3. update_error_tree 模式分支

| 特性 | 原始模式 (`use_blueprint=False`) | 新模式 (`use_blueprint=True`) |
|------|-----------------------------------|-------------------------------|
| LLM 调用次数 | 较少（只调用 expansion） | 较多（额外调用 LLM 生成 blueprint） |
| 存储格式 | `critic_template` 纯字符串 | `{"blueprint": "...", "content": "..."}` dict |
| vertical_expansion | `_vertical_expansion_orig()` | `vertical_expansion()` |
| horizontal_expansion | `_horizontal_expansion_orig()` | `horizontal_expansion()` |
| JSON 文件 | 与原始 Table-Critic 完全兼容 | 新格式，含 blueprint 摘要 |

### 4. JSON 路径统一

所有 27 处 `few_shot_critic.json` 硬编码路径已统一为常量 `CRITIC_TREE_JSON`：

```python
# critic/TableQA/tools/__init__.py
CRITIC_TREE_JSON = "critic/TableQA/tools/few_shot_critic.json"

# critic/TableFV/tools/__init__.py
CRITIC_TREE_JSON = "critic/TableFV/tools/few_shot_critic.json"
```

---

## 修改的文件清单

### 新增开关参数
- `thought/TableQA/main.py` — 添加 `--use_clarifier` 参数 + 结果目录自动切换
- `thought/TableFV/main.py` — 同上
- `refine/TableQA/main_tree_based.py` — 已有 `--use_controller` + `--use_clarifier`，添加结果目录自动切换
- `refine/TableFV/main_tree_based.py` — 同上

### update_tree.py 模式分支
- `critic/TableQA/tools/update_tree.py` — 添加 `_vertical_expansion_orig` / `_horizontal_expansion_orig`，`update_error_tree` 添加 `use_blueprint` 参数
- `critic/TableFV/tools/update_tree.py` — 同上

### 调用处更新
- `refine/TableQA/utils/chain.py` — `update_error_tree(..., use_blueprint=False)`
- `refine/TableFV/utils/chain.py` — 同上
- `refine/TableQA/utils/controller.py` — `update_error_tree(..., use_blueprint=True)`
- `refine/TableFV/utils/controller.py` — 同上

### JSON 路径统一
- `critic/TableQA/tools/__init__.py` — 添加 `CRITIC_TREE_JSON` 常量
- `critic/TableFV/tools/__init__.py` — 添加 `CRITIC_TREE_JSON` 常量
- `critic/TableQA/tools/get_info.py` — 引用常量替代硬编码
- `critic/TableFV/tools/get_info.py` — 同上
- `critic/TableQA/tools/multiprocess.py` — 同上
- `critic/TableFV/tools/multiprocess.py` — 同上
- `critic/TableQA/tools/few_shot_critic_json.py` — 同上
- `critic/TableFV/tools/few_shot_critic_json.py` — 同上
- `refine/TableQA/utils/chain.py` — 引用 `CRITIC_TREE_JSON`
- `refine/TableFV/utils/chain.py` — 同上
- `refine/TableQA/utils/controller.py` — 引用 `CRITIC_TREE_JSON`
- `refine/TableFV/utils/controller.py` — 同上
- `agents/*.py` — default `memory_path` 改为 `None`

### LLM 基础设施（4个 llm.py 统一为改进版）
- `thought/TableQA/utils/llm.py`
- `thought/TableFV/utils/llm.py`
- `refine/TableQA/utils/llm.py`
- `refine/TableFV/utils/llm.py`

改进内容：`_create_mock_response()`（DRY）、`set_token_log_dir()` + `_log_token_usage()`（多进程安全）、`save_token_usage()`、`collect_token_usage()`、`timeout=600.0`、`enable_thinking: False`、API 响应校验。

### Shell 脚本
- `run_QA.sh` — 添加 `MODE` 变量 + 自动切换参数
- `run_FV.sh` — 同上

### 原始代码备份
- `critic/TableQA/tools/update_tree_orig.py` — 原始 update_tree.py
- `critic/TableFV/tools/update_tree_orig.py` — 原始 update_tree.py

---

## 注意事项

1. **不要混用模式**：thought 阶段和 refine 阶段的模式必须一致。`MODE="orig"` 时 both 阶段都用 False，`MODE="new"` 时都用 True。
2. **JSON 格式不可混用**：原始模式的错误树 JSON 存储纯字符串，新模式存储 dict。两种模式的 JSON 文件不要互相替换。
3. **ClarifierAgent import 隔离**：`use_clarifier=False` 时不会 import agents 模块，避免原始环境缺少 agents 目录时报错。
4. **`append` 返回值 bug**：原代码中 `few_shot = few_shot.append(template_dict)` 是 bug（`append` 返回 None），已在新代码中修正为 `few_shot.append(template_dict)`。
