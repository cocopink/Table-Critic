# Scripts 模块文档

[根目录](../CLAUDE.md) > **scripts**

> 最后更新：2026-06-09 19:39:59

---

## 变更记录 (Changelog)

### 2026-06-09 (新建)
- 初始化 scripts 模块文档
- 扫描 3 个脚本文件

---

## 模块职责

Scripts 目录包含 Table-Critic 的**实验辅助脚本**，用于 pilot 数据集构建、实验结果汇总和结果重建。

---

## 文件清单

| 文件 | 职责 | 阶段 |
|------|------|------|
| `build_refine_pilot_set.py` | 从 thought/baseline 结果构建固定 pilot 索引集 | M0 |
| `summarize_refine_experiment.py` | 基线 vs 实验的成对对比报告 | M0 |
| `rebuild_final_result.py` | 从缓存重建 final_result.pkl | 辅助 |
| `openai_smoke_test.py` | OpenAI-compatible 接口连通性与鉴权烟测 | 辅助 |

---

## 入口与使用

### build_refine_pilot_set.py

构建实验用的固定 pilot 索引集，优先选取 baseline 错误样本。

```bash
python scripts/build_refine_pilot_set.py \
    --thought-pkl "results/thought/wikitq/gpt-5.4/final_result.pkl" \
    --output "results/pilot/wikitq/pilot_indices_100.json" \
    --size 100
```

**参数**:
- `--thought-pkl` (必填): thought 阶段 final_result.pkl 路径
- `--baseline-pkl` (可选): baseline refine final_result.pkl 路径
- `--output` (必填): 输出 pilot_indices.json 路径
- `--size` (默认 100): pilot 样本数
- `--seed` (默认 42): 随机种子

### summarize_refine_experiment.py

生成基线 vs 实验的标准化对比报告 (Markdown 格式)。

```bash
python scripts/summarize_refine_experiment.py \
    --baseline-pkl "results/refine/baseline/final_result.pkl" \
    --experiment-pkl "results/refine/experiment/final_result.pkl" \
    --experiment-token-json "results/refine/experiment/token_usage.json" \
    --output "results/report.md"
```

**报告包含**: accuracy 对比、changed_count、token usage 统计

### rebuild_final_result.py

从 cache 目录重建 final_result.pkl（仅执行 fixed_chain = simple_query）。

```bash
python scripts/rebuild_final_result.py --wikitq --n_proc 4
python scripts/rebuild_final_result.py --tabfact --n_proc 4
```

### openai_smoke_test.py

用于验证 `HAOMIAO_URL` 和 `HAOMIAO_AUTH_TOKEN` 是否可用于 OpenAI-compatible 接口调用。

```bash
python scripts/openai_smoke_test.py --model gpt-5.4
```

默认行为：
- `base_url` 优先读取 `HAOMIAO_URL`
- `api_key` 优先读取 `HAOMIAO_AUTH_TOKEN`，再兼容 `HAOMIAO_AUTHEN_TOKEN` / `OPENAI_API_KEY`
- `model` 默认 `gpt-5.4`
- 请求使用最小化 chat completions 调用

---

## 关键依赖

```python
from refine.TableQA.utils.read_pkl import read_pkl
```

脚本依赖 `sys.path.insert(0, ".")` 以加载项目模块。

---

## 相关文件清单

- `scripts/build_refine_pilot_set.py` - pilot 索引构建
- `scripts/summarize_refine_experiment.py` - 实验对比报告
- `scripts/rebuild_final_result.py` - 结果重建
