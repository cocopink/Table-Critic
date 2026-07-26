# G-CRAFT 实验列表

> baseline = 原版 Table-Critic（Peiying-Yu，无 ATG/Controller/Clarifier/Diff-Critic）
> ours = G-CRAFT（p1p2：ATGO + P1+P2 图增强 + Controller + Clarifier）
> 目标：回答"G-CRAFT 相比原版 Table-Critic 有没有效果"

## 一、系统设置（代码相关）

| 系统                        | 仓库                                      | P1/P2/γ      | Clarifier | Controller | Diff-Critic | frozen_memory | 脚本                                      |
| --------------------------- | ----------------------------------------- | ------------- | --------- | ---------- | ----------- | ------------- | ----------------------------------------- |
| **baseline_original** | `~/Table-Critic-original`（Peiying-Yu） | —（无 ATGO） | off       | off        | off         | off（原版无） | `run_original_baseline.sh`              |
| **ours(p1p2)**        | `~/Table-Critic`                        | on/on/0.05    | on        | on         | off         | on            | `run_experiments.sh --variant p1p2`     |
| ablation(P1=P2=off)         | `~/Table-Critic`                        | off/off/0.0   | on        | on         | off         | on            | `run_experiments.sh --variant baseline` |
| ablation(P1 only)           | `~/Table-Critic`                        | on/off/0.05   | on        | on         | off         | on            | `run_experiments.sh --variant p1`       |
| ablation(P2 only)           | `~/Table-Critic`                        | off/on/0.0    | on        | on         | off         | on            | `run_experiments.sh --variant p2`       |

> ours 与消融的区别仅在 P1/P2/γ；其余代码路径（ATGO 重排、Clarifier、Controller、frozen_memory）一致。
> baseline_original 用原版仓库，无任何增强；已注入 ollama 原生路径（think:False）。

## 二、LLM 设置（所有实验统一）

| 参数               | 值                                                            |
| ------------------ | ------------------------------------------------------------- |
| 推理后端           | ollama 原生 /api/chat（`_is_ollama_qwen` 自动走）           |
| base_url           | `http://localhost:11434/v1`                                 |
| temperature        | 0                                                             |
| top_p              | 1                                                             |
| thinking mode      | **off**（ollama `think:False`，Qwen3.5 non-thinking） |
| thought max_decode | 150                                                           |
| refine max_decode  | 2048                                                          |
| n_proc             | 1（本机 8GB）/ 1-4（服务器）                                  |
| chunk_size         | 1                                                             |

## 三、实验列表

| ID            | 实验                      | 系统              | 模型        | 数据×规模   | 优先级         | 跑法                                                                |
| ------------- | ------------------------- | ----------------- | ----------- | ------------ | -------------- | ------------------------------------------------------------------- |
| **E01** | 原版 baseline             | baseline_original | qwen3.5:4b  | wikitq×500  | **MUST** | `bash run_original_baseline.sh`                                   |
| **E02** | G-CRAFT ours              | ours(p1p2)        | qwen3.5:4b  | wikitq×500  | **MUST** | `bash run_experiments.sh --stage pilot --model 4b --variant p1p2` |
| **E03** | 消融 P1=P2=off            | ablation          | qwen3.5:4b  | wikitq×500  | MUST           | `... --variant baseline`                                          |
| E04           | 消融 P1 only              | ablation          | qwen3.5:4b  | wikitq×500  | NICE           | `... --variant p1`                                                |
| E05           | 消融 P2 only              | ablation          | qwen3.5:4b  | wikitq×500  | NICE           | `... --variant p2`                                                |
| **E06** | 原版 baseline 9B          | baseline_original | qwen3.5:9b  | wikitq×500  | MUST（服务器） | `MODEL_NAME=qwen3.5:9b bash run_original_baseline.sh`             |
| **E07** | G-CRAFT ours 9B           | ours(p1p2)        | qwen3.5:9b  | wikitq×500  | MUST（服务器） | `... --model 9b --variant p1p2`                                   |
| E08           | 原版 baseline 27B         | baseline_original | qwen3.5:27b | wikitq×500  | NICE（A100）   | 同 E06，需 A100                                                     |
| E09           | G-CRAFT ours 27B          | ours(p1p2)        | qwen3.5:27b | wikitq×500  | NICE（A100）   | 同 E07，需 A100                                                     |
| **E10** | 原版 baseline tabfact     | baseline_original | qwen3.5:4b  | tabfact×500 | MUST           | `run_original_baseline.sh` FV 版（待补）                          |
| **E11** | G-CRAFT ours tabfact      | ours(p1p2)        | qwen3.5:4b  | tabfact×500 | MUST           | `... --dataset tabfact --variant p1p2`                            |
| E12+          | 全量（pilot gate 通过后） | 各系统            | 各模型      | full×-1     | 后续           | 同上`--stage full`                                                |

## 四、对比逻辑（回答核心问题）

| 对比                                     | 回答                                             |
| ---------------------------------------- | ------------------------------------------------ |
| **E02 vs E01**（4B：ours vs 原版） | G-CRAFT 相比原版 Table-Critic 有没有效果（核心） |
| E07 vs E06（9B）                         | 效果是否在 9B 仍成立                             |
| E09 vs E08（27B）                        | C1：小模型增益是否 > 大模型（尺度效应）          |
| E02 vs E03（P1+P2 vs 无）                | P1/P2 图增强的增量（消融）                       |
| E03 vs E04 vs E05                        | P1、P2 各自贡献                                  |
| E11 vs E10                               | tabfact 跨任务稳健性                             |

## 五、跑实验的注意

1. **本机 4B**：E01-E05、E10-E11，每 500 条 ~5-12h
2. **服务器 9B/27B**：E06-E09，按 `docs/server_deploy_guide.md` 租 AutoDL 4090/A100
3. **frozen_memory**：ours 全部开（R002）；baseline_original 原版无此开关，记录 error_tree hash 是否变化
4. **已知坑**：`thought/main.py` 检查 `final_result.pkl` 存在则跳过 thought——重跑前需删旧 `final_result.pkl` 或换 thought_dir（run_experiments.sh 已用全维度路径规避；run_original_baseline.sh 用 `original_s0_nothinking` 路径）
5. **先 E01+E02** 拿到 4B 核心对比，再决定是否扩展 9B/27B/全量
