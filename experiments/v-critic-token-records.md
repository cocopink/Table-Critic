# V-Critic Experiment Token Records

## Pilot: 100 Samples

### Stage 1: Thought (shared by both groups)
- **Samples**: 100
- **Model**: gpt-5.4
- **Input Tokens**: 1,238,964
- **Output Tokens**: 16,718
- **Total Tokens**: 1,255,682
- **API Calls**: 738

### Stage 2: Refine - Baseline (use_verifier=False)
- **Accuracy**: 82% (82/100)
- **Input Tokens**: 917,564
- **Output Tokens**: 19,467
- **Total Tokens**: 937,031
- **API Calls**: 285
- **Results Dir**: `test/results/flattened/refine/wikitq/gpt-5.4-pilot100-baseline/`

### Stage 2: Refine - V-Critic (use_verifier=True)
- **Accuracy**: 84% (84/100)
- **Input Tokens**: 877,635
- **Output Tokens**: 19,080
- **Total Tokens**: 896,715
- **API Calls**: 273
- **Results Dir**: `test/results/flattened/refine/wikitq/gpt-5.4-pilot100-vcritic/`

### Pilot Summary

| Metric | Baseline | V-Critic | Delta |
|--------|----------|----------|-------|
| Accuracy | 82% | 84% | +2% |
| API Calls | 285 | 273 | -4.2% |
| Total Tokens | 937,031 | 896,715 | -40,316 (-4.3%) |
| Input Tokens | 917,564 | 877,635 | -39,929 (-4.3%) |
| Output Tokens | 19,467 | 19,080 | -387 (-2.0%) |

### Verifier Cost
- Verifier itself: 0 tokens (pure code logic, no LLM calls)
- Token savings from fewer iterations: -40,316 tokens
- Net token cost: **negative** (V-Critic saves tokens)

## Quick Validation: 5 Samples

### Refine - Baseline
- **Accuracy**: 60% (3/5)
- **Total Tokens**: 90,686
- **API Calls**: 27

### Refine - V-Critic
- **Accuracy**: 100% (5/5)
- **Total Tokens**: 39,023
- **API Calls**: 12

---

## Full Dataset: 4344 Samples

### Baseline (existing, non-flattened)
- **Accuracy**: 84.05% (3651/4344)
- **Results Dir**: `results/refine/wikitq/gpt-5.4/`
- **Note**: Non-flattened Thought, no use_verifier

### V-Critic (flattened Thought, use_verifier=True)
- **Accuracy**: 84.23% (3660/4344)
- **Input Tokens**: 25,617,560
- **Output Tokens**: 652,244
- **Total Tokens**: 26,269,804
- **API Calls**: 7,584
- **Results Dir**: `results/flattened/refine/wikitq/gpt-5.4-vcritic/`
- **Note**: Flattened Thought, use_verifier=True
- **Duration**: ~11h 52m

### Full Summary

| Metric | Baseline | V-Critic | Delta |
|--------|----------|----------|-------|
| Accuracy | 84.05% | 84.23% | +0.18% |

### Caveat
Baseline uses non-flattened Thought while V-Critic uses flattened Thought.
The +0.18% may partially come from flattening rather than verifier alone.
A fair comparison would require running baseline with flattened Thought.
