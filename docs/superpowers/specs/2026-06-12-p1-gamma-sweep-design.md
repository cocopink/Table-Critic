# P1 Gamma Parameter Sweep Experiment Design

> Date: 2026-06-12
> Status: Approved
> Scope: TabFact + WikiTQ, Qwen3.5:35B INT4 coarse sweep + GPT-5.4 fine validation

## 1. Goal

1. **Find optimal gamma**: Determine the best `gamma` value for P1 column-smoothing in ATGO row reranking.
2. **Validate P1+P2 synergy**: Confirm that the P1+P2 combination remains robust across different gamma values.

## 2. Background

### What gamma does

In `table_structure/column_smoothing.py`, gamma controls the convex combination of the base QG-PPR propagation matrix and the column-smoothed variant:

```python
return (1 - gamma) * base + gamma * smooth
```

- `gamma=0.0`: Pure base propagation (no inter-column information flow)
- `gamma=0.1`: Current default (10% smoothing)
- `gamma=1.0`: Fully smoothed (completely replaces original structure)
- Range: `[0.0, 1.0]`, clamped in code

### Current experiment coverage

| gamma | P2 | Model | Acc (TabFact, 165 samples) |
|-------|----|-------|---------------------------|
| 0.0 | off | GPT-5.4 | 0.5515 (baseline) |
| 0.1 | on | GPT-5.4 | 0.6121 (P1+P2, current best) |
| 0.1 | off | GPT-5.4 | 0.5576 (P1 only) |
| 0.0 | on | GPT-5.4 | 0.5758 (P2 only) |

Only one non-zero gamma has been tested. The parameter space is largely unexplored.

### Why gamma is a preprocessing parameter

Gamma only affects Stage 0 (ATGO reranking). It changes the **row ordering** of the input table, not the LLM behavior in Stage 1 (Thought) or Stage 2 (Refine). This means gamma's relative ranking across values should have reasonable cross-model consistency — the key assumption behind the coarse→fine approach.

## 3. Approach: Two-Phase Coarse→Fine

### Phase 1: Coarse Sweep (Qwen3:32B INT4, local, zero API cost)

- **Model**: Qwen3.5:35B INT4 via Ollama (localhost:11434/v1)
- **Dataset**: TabFact (165 samples)
- **Hardware**: NVIDIA 5090 32GB (INT4 ≈ 22GB model + 10GB KV cache = ~32GB, fits with margin)
- **Context length**: Must set `OLLAMA_NUM_CTX=8192` (pipeline prompts typically 2500-4500 tokens; Ollama default 2048 is insufficient)
- **Model selection rationale**: Qwen3.5 > Qwen3 at same scale (newer generation). 35B INT4 retains more reasoning capability than 9B FP16, providing better sensitivity to gamma-induced input ordering changes for clearer coarse sweep curves. INT4 quantization loss is acceptable for coarse sweep (relative ranking, not absolute accuracy).
- **Fallback**: If OOM occurs, reduce to `chunk_size=1`; fall back to Qwen3.6:9B Q4_K_M if needed.
- **Purpose**: Identify top-3 gamma candidates from accuracy curve
- **Total**: 12 experiment runs

### Phase 2: Fine Validation (GPT-5.4, remote API)

- **Model**: GPT-5.4 (default API)
- **Datasets**: TabFact (165 samples) + WikiTQ (897 samples)
- **Purpose**: Confirm optimal gamma on the target model, validate cross-dataset generalization
- **Total**: 6 experiment runs (3 TabFact + 3 WikiTQ)

## 4. Experiment Matrix

### Phase 1: Coarse Sweep (Qwen3.5:35B INT4)

| Run | gamma | P2 | Purpose |
|-----|-------|----|---------|
| C01 | 0.0 | off | Qwen baseline (P1 disabled) |
| C02 | 0.0 | on | Qwen baseline (P1+P2, gamma=0) |
| C03 | 0.05 | off | P1 only, low smoothing |
| C04 | 0.05 | on | P1+P2, low smoothing |
| C05 | 0.2 | off | P1 only, medium smoothing |
| C06 | 0.2 | on | P1+P2, medium smoothing |
| C07 | 0.3 | off | P1 only, medium-strong smoothing |
| C08 | 0.3 | on | P1+P2, medium-strong smoothing |
| C09 | 0.5 | off | P1 only, strong smoothing |
| C10 | 0.5 | on | P1+P2, strong smoothing |
| C11 | 0.7 | off | P1 only, extreme smoothing |
| C12 | 0.7 | on | P1+P2, extreme smoothing |

### Phase 2: Fine Validation (GPT-5.4)

| Run | gamma | P2 | Dataset | Purpose |
|-----|-------|----|---------|---------|
| F01 | top1 | on | TabFact | Best candidate, primary validation |
| F02 | top2 | on | TabFact | Runner-up validation |
| F03 | top3 | on | TabFact | Third candidate validation |
| F04 | top1 | on | WikiTQ | Cross-dataset validation |
| F05 | top2 | on | WikiTQ | Cross-dataset validation |
| F06 | top3 | on | WikiTQ | Cross-dataset validation |

### Gamma Selection Rationale

- Dense sampling in `[0.0, 0.3]`: Most likely optimal range
- Sparse sampling in `[0.5, 0.7]`: Probe for unexpected extreme-value optimum
- No `gamma > 0.7`: Original propagation matrix retains <30%, signal nearly destroyed

## 5. Execution

### Per-Run Commands

All runs reuse existing `run_FV.sh` (TabFact) and `run_QA.sh` (WikiTQ) via environment variables:

```bash
# Phase 1: Coarse sweep - Qwen3.5:35B INT4, P1+P2, gamma=0.2
ENABLE_P1=true ENABLE_P2=true P1_GAMMA=0.2 \
  base_url=http://localhost:11434/v1 \
  openai_api_key="ollama" \
  model_name="qwen3.5:35b" \
  first_n=165 \
  n_proc=1 \
  chunk_size=1 \
  OLLAMA_NUM_CTX=8192 \
  bash run_FV.sh

# Phase 2: Fine validation - GPT-5.4, P1+P2, gamma=0.3
ENABLE_P1=true ENABLE_P2=true P1_GAMMA=0.3 \
  bash run_FV.sh
```

### Concurrency Notes

- **Phase 1 (Qwen3.5:35B local)**: `n_proc=1, chunk_size=1` (single 5090, ~22GB model leaves ~10GB for KV cache; set `OLLAMA_NUM_CTX=8192`)
- **Phase 2 (GPT remote)**: `n_proc=8` (API-based, no local resource constraint)

### Cache Handling

The ATGO cache is parameter-aware (`_cache_path` encodes gamma in filename). Different gamma values naturally produce separate caches. **No manual cache deletion needed.**

However, for Phase 1→Phase 2 transition with the **same gamma value**, Stage 0 output files are identical (gamma determines the reranking, not the model). Consider reusing Stage 0 output:
- `thought/TableFV/data/tabfact/test_reranked_row.jsonl` is shared across models for the same gamma
- Only Stage 1 and Stage 2 results differ by model

## 6. Success Criteria

1. **Optimal gamma found**: Coarse sweep shows a clear peak (not a plateau); fine validation confirms.
2. **P1+P2 synergy holds**: Optimal gamma P1+P2 accuracy >= current 0.6121 on TabFact.
3. **Cross-model consistency**: Qwen and GPT gamma ranking trends are directionally aligned (not inverted).
4. **Cross-dataset generalization**: Optimal gamma on TabFact also performs well (or at least not significantly worse) on WikiTQ.

## 7. Risk Analysis

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Qwen curve is flat (cannot distinguish gamma values) | Medium | Focus on trend direction, not absolute values; consider extending to more gamma values |
| Optimal gamma differs between TabFact and WikiTQ | Medium | Report dataset-specific optimal; consider ensemble or weighted average |
| GPT fine validation does not confirm Qwen top-3 | Low | This would itself be a finding; run all 5 gamma values on GPT if needed |
| OOM on 5090 with Qwen3.5:35B | Medium | Reduce to `chunk_size=1`; fall back to Qwen3.6:9B Q4_K_M if needed |
| Ollama context truncation | Medium | Must set `OLLAMA_NUM_CTX=8192` before starting Ollama server |

## 8. Output Artifacts

1. **Accuracy table**: All 18 runs with accuracy, relative-to-baseline delta
2. **Gamma-accuracy curve**: Dual-model overlay plot (Qwen + GPT on same axes)
3. **P1-only vs P1+P2 comparison**: Per-gamma synergy analysis
4. **Regression analysis**: Degraded samples comparison between new optimal and current gamma=0.1
5. **Cross-dataset comparison**: TabFact vs WikiTQ optimal gamma (if applicable)
