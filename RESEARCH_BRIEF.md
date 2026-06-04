# Research Brief: Question-Aware Executable Table Curation

**Date**: 2026-05-26
**Base Framework**: Table-Critic (ACL 2025)
**Current Branch**: feat/table-analyzer

## Core Direction

Instead of fine-tuning a small model to replace rule-based preprocessing (naive narrative), reframe as:

**"Question-aware executable table curation / learned operation predictor for table reasoning"**

The small model does NOT generate complete transformed tables. Instead, it predicts a sequence of executable structural transformation operations, executed by a Python engine.

## Validation Path (Minimum Viable Validation)

### Step 0: Hints-to-Stage1 Pilot [ALREADY DESIGNED, NOT EXECUTED]
- Inject existing `table_analysis` hints into Stage 1 operations
- **Gate**: If hints cannot improve Stage 1 by ≥1%, the entire direction is questionable
- Existing plan: `refine-logs/EXPERIMENT_PLAN_HINTS.md`

### Step 1: Preprocessing Oracle Ceiling
- Manual/GPT-assisted annotation of 100-200 WikiTQ Stage1 bad cases
- Question: Which errors can actually be fixed by header splitting, value normalization, typed parsing, answer format normalization?
- **Gate**: If oracle ceiling < +2%, do not proceed to fine-tuning

### Step 2: Train Operation Sequence Predictor (NOT free JSON generator)
- Define small, hard operation DSL: split_header, normalize_values, parse_numeric, standardize_date, annotate_type, select/reorder_columns
- Model outputs operation sequences, not complete transformed tables
- Each operation executed deterministically — interpretable, debuggable, ablatable
- Like Chain-of-Table's preprocessing version — better paper narrative

### Step 3: Downstream Accuracy + Cost as Primary Metrics
- Prove: Stage1 + learned preprocessor ≈ full pipeline, but cheaper than Refine
- NOT just transform exact match

## Technical Approach

- **DSL Design**: split_header, normalize_values, parse_numeric, standardize_date, annotate_type, select/reorder_columns
- **Training**: LoRA fine-tune SLM (e.g., 3B class) on operation sequences
- **Label Construction**: NOT just GPT distillation — must include downstream reward signal
- **Execution**: Deterministic Python executor for each operation

## Risk Assessment

| Dimension | Score | Judgment |
|-----------|-------|----------|
| Engineering Feasibility | 7/10 | LoRA SLM + operation DSL is doable |
| Data Construction Difficulty | 5/10 | Biggest bottleneck: no "optimal preprocessing" ground truth |
| Academic Novelty | 5.5/10 (naive) → 7/10 (reframed) | "Fine-tuned preprocessing" not strong; "executable structural transform for reasoning" stronger |
| Expected Gain | Medium | WikiTQ possibly +1~2%, stable +3% is hard |
| Standalone Paper Risk | Medium-High | If only proving cheap replacement for rules, contribution seen as engineering |

## Related Work Landscape (Critical)

- **NormTab**: Already proved value normalization useful
- **FormaT5**: Already has "model generates table transform instructions" paradigm
- **AutoPrep/TART**: Data preparation / table formatting — compresses novelty
- **Chain-of-Table (ICLR 2024)**: Direct basis — our work is the "preprocessing version"

**Key differentiator**: Question-aware, executable structural operations, downstream reward alignment, small model low cost, oriented specifically for table reasoning

## Constraints

- Do NOT full-commit to 7B fine-tuning before oracle ceiling + Stage1 hints pilot
- Labels must come from downstream reward, not just GPT distillation
- Must validate ≥1.5% improvement on WikiTQ before committing to the full pipeline
- If improvement is small, pivot to operation-level table diff diagnostics from refine-logs

## Existing Baseline Data

| Task | Stage 1 Only | Full Pipeline (S1+S2) | Refine Delta |
|------|:-:|:-:|:-:|
| WikiTQ (gpt-5.4) | 81.98% | 84.95% | +2.97% |
| TabFact (gpt-5.4) | 93.63% | 95.55% | +1.92% |

Source: `results/flattened/thought/wikitq/gpt-5.4/acc.txt`, `results/flattened/refine/wikitq/gpt-5.4/acc.txt`
