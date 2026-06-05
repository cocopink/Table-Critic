# StructDiff-Refine: Operation-Level Diff Diagnosis for Table-Critic

> Date: 2026-06-05
> Status: Design proposal
> Base framework: Table-Critic current pipeline
> Goal: improve final post-Refine accuracy while reducing ineffective Refine cost

---

## 1. Motivation

The previous structured table representation draft correctly identifies that flat table
linearization loses structural information. However, its main optimization target is
misaligned with the current research goal. The goal is not to replace Refine by making
Stage 1 stronger. The goal is to improve the final accuracy after Refine, while reducing
the high cost caused by broad Tree/Critic/Refiner calls and repeated full-chain
re-execution.

Existing evidence suggests Refine is still valuable:

| Task | Stage 1 only | Full pipeline | Refine delta |
|------|--------------|---------------|--------------|
| WikiTQ | 81.98% | 84.95% | +2.97% |
| TabFact | 93.63% | 95.55% | +1.92% |

Therefore, the better direction is to make Refine more accurate and more local, rather
than trying to bypass it.

---

## 2. Diagnosis of Current Bottleneck

The current Refine stage is expensive because it treats many errors as broad reasoning
failures:

1. Judge decides whether the sample is incorrect.
2. Tree classifies an error route using a large error tree context.
3. Critic diagnoses based mostly on the original table, reasoning chain, and final
   sub-table.
4. Refiner often re-runs a large part of the dynamic chain.

The key missing signal is operation-level change evidence. The code already has the
building block: `get_table_log()` can replay the operation chain and recover
intermediate table states. But the current Critic does not consistently see the
before/after state of the operation that likely caused the error.

This is analogous to debugging a transformation pipeline with only the input and final
output. To localize the bug, the critic needs the diff around each operation.

---

## 3. Core Idea

StructDiff-Refine turns Refine from global re-diagnosis into local evidence-based
repair.

```
Stage 1 Thought
    |
    v
Judge
    |
    v
Operation Trace Builder
    - replays chain with get_table_log()
    - records before/after table state for every operation
    |
    v
Evidence Pack Builder
    - row diff
    - column diff
    - sort/order evidence
    - group statistics
    - value normalization evidence
    - answer format evidence
    |
    v
Step Localizer
    - first uses deterministic checks when possible
    - falls back to a small LLM prompt only when uncertain
    |
    v
Diff-Critic
    - sees the suspected step, before table, after table, operation args, and evidence
    - outputs structured diagnosis
    |
    v
Local Repair Executor
    - repairs only the failing operation or failing suffix
    - falls back to current full Refine when confidence is low
    |
    v
Judge
```

---

## 4. Design Principles

### 4.1 Accuracy First

The system should not skip Refine aggressively. Any cost-saving mechanism must preserve
or improve final accuracy. When confidence is low, it should fall back to the existing
full Refine path.

### 4.2 Evidence Instead of Hints

The previous `table_analysis` hints are prompt-side suggestions. StructDiff-Refine uses
verifiable evidence:

| Evidence type | Example |
|---------------|---------|
| Row diff | selected rows `{1, 5}`; removed rows `{2, 3, 4, 6}` |
| Column diff | kept columns `player, country`; dropped `time, team` |
| Sort evidence | target column values before/after; monotonicity check |
| Group evidence | grouped column, unique ratio, group counts |
| Value evidence | parsed numeric/date values and failed parses |
| Answer evidence | final answer value and exact table value candidates |

Evidence should be compact and deterministic. It should avoid speculative semantic labels
unless confidence is high.

### 4.3 Local Repair Before Full Re-run

Most operations have structured parameters:

| Operation | Local repair target |
|-----------|---------------------|
| `select_row` | regenerate selected row ids |
| `select_column` | regenerate selected columns |
| `sort_column` | repair sort column/order/type, then replay |
| `group_column` | repair group column or reject over-unique grouping |
| `add_column` | regenerate derived column only when evidence supports it |
| `final_query` | repair final answer using exact values and final sub-table |

The current full Refine path remains as fallback.

---

## 5. Components

### 5.1 Operation Trace Builder

Reuse existing replay logic:

- `thought/*/utils/chain.py:get_table_log()`
- `refine/*/utils/chain.py:get_table_log()`
- operation `*_act()` functions

Output:

```python
{
    "steps": [
        {
            "step_id": 1,
            "operation_name": "select_row",
            "operation": {...},
            "before_table": [...],
            "after_table": [...],
            "act_chain": "f_select_row(row 1, row 5)"
        }
    ]
}
```

### 5.2 Evidence Pack Builder

Create deterministic summaries for each operation step.

Output:

```python
{
    "step_id": 1,
    "operation_name": "select_row",
    "row_diff": {
        "kept_row_ids": [1, 5],
        "removed_row_ids": [2, 3, 4, 6, 7, 8],
        "kept_count": 2,
        "removed_count": 6
    },
    "value_mentions": {
        "question_entities": ["Japan"],
        "matched_cells": []
    },
    "warnings": [
        "Question entity was not present in kept rows."
    ]
}
```

The builder should be conservative. A missing warning is acceptable; a false hard
constraint is dangerous.

### 5.3 Step Localizer

Localizer chooses the most suspicious step.

Priority:

1. Deterministic verifier signal, if available.
2. Operation-specific warning score from Evidence Pack.
3. Existing Critic/Judge signal.
4. Small LLM localization prompt over compact evidence.

Output:

```python
{
    "step_id": 2,
    "operation_name": "sort_column",
    "confidence": 0.82,
    "reason": "Sort column values are non-monotonic after execution."
}
```

### 5.4 Diff-Critic

Diff-Critic receives only localized evidence, not the whole error tree.

Input:

- original question
- operation history
- suspected operation
- before table
- after table
- evidence pack
- top-k retrieved blueprints or few-shot examples

Output:

```python
{
    "error_step": 2,
    "operation_name": "sort_column",
    "error_subtype": "wrong_sort_key",
    "evidence": "The question asks for attendance, but the chain sorted date.",
    "repair_action": {
        "type": "regenerate_operation_args",
        "target_operation": "sort_column",
        "constraints": {
            "must_use_column": "attendance"
        }
    }
}
```

### 5.5 Local Repair Executor

The executor applies the repair action and replays the suffix of the chain.

Repair modes:

- `regenerate_operation_args`: call only the operation prompt for the target step.
- `replace_operation`: choose a different operation when the selected operation type is wrong.
- `repair_final_query`: keep the chain, regenerate only final answer.
- `fallback_full_refine`: use existing Controller path when confidence is low.

---

## 6. Relationship to Structured Table Representation Draft

The old draft should be treated as a supporting idea, not the main implementation path.

Keep:

- compact column/value type summaries
- mixed-format parsing
- exact-answer format guidance
- optional structure annotations for prompts

Change:

- Do not replace `TableAnalyzer` as the first step.
- Do not make rule-based semantic decomposition a hard gate.
- Do not define success as skipping Refine.
- Move structural information into Refine evidence and local repair.

The stronger narrative is:

> Table representation alone is insufficient. The missing piece is operation-level
> evidence: what each table operation changed and whether that change helped or damaged
> the reasoning state.

---

## 7. Implementation Plan

### Phase 1: Evidence-Only Diff-Critic

Goal: improve Critic diagnosis without changing repair execution.

Tasks:

1. Add `operation_trace.py` helper for trace extraction.
2. Add `evidence_pack.py` helper for operation-specific diff summaries.
3. Add `get_cot_for_critic_diff()` in critic tools.
4. Add one controller branch that calls Diff-Critic for incorrect samples.
5. Feed the structured diagnosis into the existing Refiner prompt.

Success criterion:

- final accuracy improves over baseline full Refine on a 100-sample pilot;
- token increase stays below 10%.

### Phase 2: Local Repair

Goal: reduce full-chain re-execution and improve repair precision.

Tasks:

1. Implement suffix replay from a repaired operation.
2. Add operation-specific repair prompts for `select_row`, `select_column`, `sort_column`,
   and `final_query`.
3. Add confidence threshold and fallback to current full Refine.

Success criterion:

- final accuracy improves on full WikiTQ;
- Refine token/API cost does not exceed baseline.

### Phase 3: Adaptive Refine Routing

Goal: reduce cost on easy or already-correct cases without hurting accuracy.

Routes:

| Route | Trigger | Action |
|-------|---------|--------|
| SKIP | Judge correct with high confidence | return current answer |
| LITE | localized evidence high confidence | Diff-Critic + local repair |
| FULL | uncertain or previous repair failed | existing full Controller |

Success criterion:

- correct-case regression close to zero;
- total Refine cost reduced by 20-40%;
- final accuracy stays above baseline.

---

## 8. Evaluation

Primary metrics:

| Metric | Why |
|--------|-----|
| Final accuracy after Refine | main goal |
| Wrong-case correction rate | measures repair quality |
| Correct-case regression rate | catches harmful routing |
| Step localization accuracy | validates Diff-Critic |
| API calls and token count | measures cost |

Core experiments:

| Experiment | Description |
|------------|-------------|
| E0 | current full pipeline |
| E1 | Diff-Critic diagnosis + existing Refiner |
| E2 | Diff-Critic + local repair |
| E3 | Diff-Critic + local repair + adaptive routing |
| E4 | ablation without operation diff |
| E5 | ablation without retrieved blueprints |

Expected result:

- E1 should test whether operation diff improves diagnosis.
- E2 should test whether local repair improves final accuracy.
- E3 should test whether cost can be reduced without sacrificing accuracy.

---

## 9. Risks

| Risk | Mitigation |
|------|------------|
| Diff prompt becomes too long | show only suspected step plus compact evidence |
| Localizer chooses wrong step | fallback to existing full Refine |
| Local repair creates regressions | run Judge after repair and fallback on failure |
| Evidence builder false positives | warnings are soft unless directly verifiable |
| QA/FV divergence | implement QA first, mirror only stable helpers to FV |

---

## 10. Related Work Positioning

- Chain-of-Table shows that intermediate table states are useful reasoning carriers.
- OHD and GraphOTTER support richer structure-aware table representations.
- CABINET supports reducing irrelevant table noise before LLM reasoning.
- Table format studies show representation matters, but no single format solves all cases.

StructDiff-Refine differs by focusing on Refine-time debugging: it uses operation-level
before/after table diffs to improve critic diagnosis and local repair in a multi-agent
table reasoning framework.

---

## 11. Recommended Next Step

Implement Phase 1 only:

1. build operation trace and evidence pack;
2. add Diff-Critic prompt;
3. run a 100-sample WikiTQ pilot against current full Refine.

Do not commit to replacing TableAnalyzer or restructuring Stage 1 until Phase 1 proves
that operation-level diff evidence improves final Refine accuracy.
