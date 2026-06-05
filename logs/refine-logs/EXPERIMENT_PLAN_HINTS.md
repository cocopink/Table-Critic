# Experiment Plan: Hints-to-Stage1 — 用前置 hints 替代 Refine 阶段

**Problem**: Table-Critic 的 Stage 2 Refine 虽然能提升 +2~3% 准确率，但成本高昂（3~6 次 LLM 调用/样本 × 2 轮迭代）。`table_analysis` hints 目前只在 Refine 消费，Stage 1 完全未使用。如果能将 hints 前置注入 Stage 1，使 Stage 1 一次做对，则可砍掉 Refine 大幅降低成本。

**Method Thesis**: 将 Stage 2 的 3 个 hint 注入点（column_normalizations → select_row, format_normalizations → sort_by, answer_format_hint → final_query）移植到 Stage 1 对应操作中，验证前置 hints 能弥补跳过 Refine 的准确率损失。

**Date**: 2026-05-25
**Branch**: feat/preprocess-finetune

## Claim Map

| Claim | Why It Matters | Minimum Convincing Evidence | Linked Blocks |
|-------|----------------|-----------------------------|---------------|
| C1 | 前置 hints 注入能提升 Stage 1 准确率 | E2 (hints) > E1 (no hints)，WikiTQ delta ≥1% | B1, B2 |
| C2 | hints + Stage1 能接近 full pipeline 准确率 | E2 vs E3 gap ≤1.5%（WikiTQ），否则 Refine 不可替代 | B2, B3 |
| C3 | 跨数据集泛化 | TabFact 同样有效 | B4 |

## Existing Baselines (no new runs needed)

| Task | Stage 1 Only | Full Pipeline (S1+S2) | Refine Delta |
|------|:-:|:-:|:-:|
| WikiTQ | 81.98% | 84.95% | +2.97% |
| TabFact | 93.63% | 95.55% | +1.92% |

Source: `results/flattened/thought/wikitq/gpt-5.4/acc.txt`, `results/flattened/refine/wikitq/gpt-5.4/acc.txt`

## Experiment Blocks

### Block 1: Stage 1 Hint Injection — Sanity Check（小样本验证）
- **Claim tested**: C1 (部分)
- **Why this block exists**: 最小成本验证 hint 注入代码的正确性
- **Dataset/split**: WikiTQ, 100 samples (前 100 个)
- **Compared systems**: E1 (no hints) vs E2 (with hints)
- **Metrics**: Accuracy, API calls, Total tokens
- **Setup details**: Stage 0 (flatten) + Stage 0.5 (table_analysis) + Stage 1 (thought only, skip Stage 2)
  - E1: `--use_clarifier False`，hints 不注入
  - E2: `--use_clarifier False`，hints 注入（代码修改后）
- **Success criterion**: E2 准确率 > E1，且 E2 ≥ E1 + 1%
- **Failure interpretation**: 如果 E2 ≈ E1，说明 hints 在 Stage 1 没有效果，需重新评估策略
- **Priority**: MUST-RUN

### Block 2: Stage 1 Hint Injection — Full Dataset（全量验证）
- **Claim tested**: C1 + C2
- **Why this block exists**: 全量验证 hints 价值，与 full pipeline 对比
- **Dataset/split**: WikiTQ full 4344 samples
- **Compared systems**: E1 (no hints, 81.98% baseline) vs E2 (with hints)
- **Metrics**: Accuracy
- **Setup details**: 同 B1，但 first_n=-1
- **Success criterion**: E2 准确率 ≥ 83.5%（接近 full pipeline 84.95%）
- **Failure interpretation**: 如果 E2 < 83%，hints 不足以替代 Refine
- **Priority**: MUST-RUN (depends on B1)

### Block 3: Cross-dataset Generalization（TabFact）
- **Claim tested**: C3
- **Why this block exists**: 验证方法不局限于 WikiTQ
- **Dataset/split**: TabFact full 2024 samples
- **Compared systems**: E1 (no hints, 93.63% baseline) vs E2 (with hints)
- **Metrics**: Accuracy
- **Success criterion**: E2 准确率 ≥ 94.5%（接近 full pipeline 95.55%）
- **Priority**: MUST-RUN (depends on B1)

## Run Order and Milestones

| Milestone | Goal | Runs | Decision Gate | Estimated Time | Risk |
|-----------|------|------|---------------|----------------|------|
| M0 | 实现 hint 注入代码 | 8 文件修改 | 代码完成 + pytest 通过 | 2-3h | 低 |
| M1 | B1: Sanity check | WikiTQ 100 samples | E2 > E1 | ~15 min | 中 |
| M2 | B2: WikiTQ full | WikiTQ 4344 samples | E2 ≥ 83.5% | ~4h | 中 |
| M3 | B3: TabFact | TabFact 2024 samples | E2 ≥ 94.5% | ~2h | 中 |

### Decision Gates
- **M1→M2**: E2 必须优于 E1（hints 有效）
- **M2→Step 2 (SLM 训练)**: 如果 E2 ≥ 83.5%，hints 价值足够 → 开始 Step 2（训练 SLM 生成更好的 analysis）
- **M1 失败**: hints 无效 → 重新评估，考虑混合架构或其他策略

## Implementation Details

### 需要修改的文件 (8 files)

**QA (4 files):**
1. `thought/TableQA/operations/select_row.py` — 注入 `column_normalizations` hints
2. `thought/TableQA/operations/sort_by.py` — 注入 `format_normalizations` hints
3. `thought/TableQA/operations/final_query.py` — 注入 `answer_format_hint`
4. `thought/TableQA/utils/chain.py` — 传递 `table_analysis` 参数

**FV (4 files):**
5. `thought/TableFV/operations/select_row.py`
6. `thought/TableFV/operations/sort_by.py`
7. `thought/TableFV/operations/final_query.py`
8. `thought/TableFV/utils/chain.py`

### 参考实现（Stage 2 已有）
- `refine/TableQA/operations/select_row.py:9-17` — column_normalizations 注入
- `refine/TableQA/operations/sort_by.py:60-71` — format_normalizations 注入
- `refine/TableQA/operations/final_query.py:240-241` — answer_format_hint 注入

### 新建文件
- `run_hint_experiment.sh` — 实验运行脚本（Stage 0 + 0.5 + 1 only）

### 关键设计决策
- hints 注入通过 `sample.get("table_analysis")` 安全访问，Stage 0.5 未启用时自动跳过
- 无 hints 注入时行为与现有代码完全一致（E1 baseline）
- QA 和 FV 的修改结构镜像
