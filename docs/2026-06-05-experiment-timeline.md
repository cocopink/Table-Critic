# Table-Critic Experiment Timeline

> Date: 2026-06-05
> Purpose: consolidate scattered experiment, design, and direction documents into a chronological research history
> Scope: currently retained Markdown files under `docs/`, `experiments/`, `idea-stage/`, `logs/refine-logs/`, and `plans/`

---

## 0. Reading Guide

This document separates three kinds of records:

- **Experiment result**: numbers were recorded from an actual run.
- **Experiment plan**: a concrete run matrix or implementation plan, but not necessarily executed.
- **Research/design proposal**: a method direction, usually before pilot validation.

Important caveat: several historical files have the same filesystem modification time because of repository sync or cleanup. The timeline below uses internal `Date` fields first, filename dates second, and only uses filesystem mtime when no better signal exists.

---

## 1. Executive Summary

The project evolved through four major research phases:

| Phase | Time | Main Question | Outcome |
| --- | --- | --- | --- |
| P0 | 2026-03 to 2026-04 | Can preprocessing / flattening reduce table structure noise? | Flatten module was designed and documented; later evidence suggests representation helps but is not enough. |
| P1 | 2026-05-21/22 | Can Refine cost be reduced by routing or verifier signals? | V-Critic and AdaRefine were explored; V-Critic full-run gain was only +0.18% with confound, AdaRefine was treated as cost routing not accuracy driver. |
| P2 | 2026-05-25/26 | Can Stage 1 be strengthened with table-analysis hints or learned preprocessing? | Hints-to-Stage1 and OpCurator were proposed as gates, but the direction depends on whether hints improve Stage 1 by at least 1%. |
| P3 | 2026-06-03 to 2026-06-05 | How to improve final post-Refine accuracy directly? | Direction shifted to Refine-time operation-level evidence: StructDiff-Refine with trace, evidence pack, localizer, Diff-Critic, local repair, and fallback. |

Current recommended line:

> Prioritize **StructDiff-Refine**: improve final post-Refine accuracy by giving Critic operation-level before/after evidence and repairing only the suspicious step or suffix, with full Refine fallback.

---

## 2. Chronological Timeline

### 2026-03-28: Controller-Clarifier Integration Decisions

**Type:** architecture decision record

**Primary source:**

- `plans/implementation_decisions_and_dilemmas.md`

**Context:**

The project was moving from a more explicit Multi-Agent branch toward a Controller-centered Refine flow.

**Key decisions:**

| Decision | Final choice | Rationale |
| --- | --- | --- |
| `use_clarifier` default | `True` | New data should automatically use Clarifier; old data falls back safely. |
| Clarifier data passing | `sample["clarifier"]` | Avoids changing many function signatures. |
| Multi-Agent branch | delete/retire in favor of Controller | Controller overlaps with Multi-Agent functions while being easier to maintain. |
| Old data handling | warn and return `{}` | Avoid runtime failure while keeping debugging visibility. |

**Research meaning:**

This phase established the current architecture constraint: future experiments should preferably extend the Controller path rather than revive a parallel Multi-Agent path.

---

### 2026-04-23 to 2026-04-27: Table Flatten Preprocessing

**Type:** design proposal + implementation plan + user guide

**Primary sources:**

- `docs/superpowers/specs/2026-04-23-table-flatten-design.md`
- `docs/superpowers/plans/2026-04-23-table-flatten.md`
- `docs/table-flatten-guide.md`

**Problem:**

Compound headers, multi-level headers, nested cells, and merged cells confuse downstream table reasoning.

**Method:**

Add a rule-based preprocessing stage before Thought:

```text
raw dataset -> preprocess.py -> flattened dataset -> Thought -> Refine
```

**Design intent:**

- Detect compound headers.
- Split compound columns and values.
- Preserve metadata for analysis.
- Keep baseline and flattened results under separate result directories.

**Status in timeline:**

This is the first major structure-focused direction. It targets input representation before Stage 1, not Refine-time diagnosis.

**Later interpretation:**

Flattening/representation improvements are useful infrastructure, but later V-Critic full-run results suggest representation alone is unlikely to deliver the main accuracy gain.

---

### 2026-05-10: Plans Module Organization

**Type:** documentation organization

**Primary source:**

- `plans/CLAUDE.md`

**Meaning:**

The `plans/` folder became the home for architecture and implementation plan documents:

- Controller design
- Multi-agent implementation analysis
- implementation comparison
- controller-clarifier integration plan

**Timeline role:**

These are architecture context documents, not direct experiment result records. They explain why later work should use `controller_main_loop()` and `ActionExecutor` as the main integration points.

---

### 2026-05-21: V-Critic Reassessment and AdaRefine Proposal

**Type:** experiment result + experiment plan

**Primary sources:**

- `logs/refine-logs/PIPELINE_SUMMARY.md`
- `logs/refine-logs/EXPERIMENT_PLAN.md`
- `logs/refine-logs/EXPERIMENT_TRACKER.md`
- `experiments/v-critic-token-records.md`

**Problem:**

Refine processes many samples with expensive Judge/Tree/Critic/Refiner calls, and correct samples may waste API calls.

**V-Critic result summary:**

| Split | Baseline | V-Critic | Delta | Notes |
| --- | ---: | ---: | ---: | --- |
| WikiTQ 5 sample quick validation | 60% | 100% | +40pp | Too small to trust. |
| WikiTQ 100 pilot | 82% | 84% | +2pp | Also reduced tokens from 937,031 to 896,715. |
| WikiTQ 4344 full | 84.05% | 84.23% | +0.18pp | Comparison is confounded by flattened vs non-flattened Thought. |

**Conclusion recorded in historical docs:**

V-Critic is not strong enough as an independent contribution. It should be downgraded to an auxiliary signal.

**AdaRefine thesis:**

Use adaptive routing to reduce Refine cost:

| Route | Trigger | Action |
| --- | --- | --- |
| SKIP | Judge says correct | return current sample |
| LITE | simple chain / small table | re-query only |
| FULL | complex or risky sample | existing full Controller |

**Experiment gates:**

- M1: Judge-Skip should reduce API calls by at least 20% with accuracy drop below 1%.
- M2: Multi-signal routing should reduce API calls by at least 40% with accuracy drop below 0.5%.
- M3: Full dataset should keep WikiTQ accuracy at least 83.5%.

**Later interpretation:**

AdaRefine is a cost-control direction. It is not sufficient for the current goal if the goal is final post-Refine accuracy improvement.

---

### 2026-05-21/22: Refine Direction Reviews and Operation-Level Table Diff

**Type:** adversarial review + refined proposal

**Primary sources:**

- `logs/refine-logs/DIRECTION_EXPLORATION.md`
- `logs/refine-logs/round-0-initial-proposal.md`
- `logs/refine-logs/round-1-review.md`
- `logs/refine-logs/round-1-refinement.md`
- `logs/refine-logs/round-2-review.md`
- `logs/refine-logs/REFINEMENT_REPORT.md`
- `logs/refine-logs/FINAL_PROPOSAL.md`
- `logs/refine-logs/score-history.md`

**Directions rejected or downgraded:**

| Direction | Historical score | Reason |
| --- | ---: | --- |
| V-Critic | about 4/10 | Structural verification coverage and full-run gain too low. |
| AdaRefine | about 5/10 | Mostly cost routing; LITE trigger weak; not enough as accuracy contribution. |
| Type-Aware Correction | 5.7/10 | Too close to prompt engineering. |
| CogDiag | 5.7/10 after review | Cognitive framing looked like static prompt templates; token saving was clearer than method novelty. |

**Key shift:**

The proposal moved from "routing / prompt templates" to **information-enhanced diagnosis**.

**Final insight:**

Current Critic sees the original table, reasoning chain, and final sub-table, but not the operation-level transformation evidence. This is like debugging a pipeline while only seeing input and final output.

**Proposed method at the time:**

Two-stage Critic:

```text
Stage 1: coarse error step localization using existing Critic
Stage 2: inject table_log[step-1] and table_log[step] as operation-level diff
```

**Validation matrix proposed:**

| Config | Table Diff | Structured Routing | Type-Specific Refiner | Purpose |
| --- | :-: | :-: | :-: | --- |
| A | no | no | no | baseline |
| B | no | no | no | enriched text baseline |
| C | yes | no | no | isolate diff evidence |
| D | yes | yes | no | test routing value |
| E | yes | yes | yes | full system |

**Score evolution:**

| Round | Overall | Verdict |
| --- | ---: | --- |
| Round 1 | 5.85/10 | revise |
| Round 2 | 6.6/10 | conditional accept |

**Later interpretation:**

This is the conceptual ancestor of `StructDiff-Refine`. The useful part is not "two-stage" itself, but operation-level table diff as a new diagnostic signal.

---

### 2026-05-25: Hints-to-Stage1 Experiment Plan

**Type:** experiment plan

**Primary source:**

- `logs/refine-logs/EXPERIMENT_PLAN_HINTS.md`

**Problem:**

`table_analysis` hints were mostly consumed in Refine. If these hints help Stage 1, the system could reduce dependence on expensive Refine.

**Method:**

Inject existing `table_analysis` hints into Stage 1 operations:

| Hint | Stage 1 target |
| --- | --- |
| `column_normalizations` | `select_row` |
| `format_normalizations` | `sort_by` |
| `answer_format_hint` | `final_query` |

**Baseline recorded in plan:**

| Task | Stage 1 only | Full pipeline | Refine delta |
| --- | ---: | ---: | ---: |
| WikiTQ | 81.98% | 84.95% | +2.97pp |
| TabFact | 93.63% | 95.55% | +1.92pp |

**Decision gates:**

- 100-sample sanity check must show hints improve Stage 1.
- Full WikiTQ with hints should reach at least 83.5% to justify moving toward learned preprocessing.
- If hints fail on Stage 1, learned preprocessing should be reconsidered.

**Later interpretation:**

This is a low-cost gate for the learned preprocessing direction. It does not directly solve the current goal unless it improves final post-Refine accuracy or reduces Refine load without regression.

---

### 2026-05-26: Literature Review and OpCurator Idea Report

**Type:** literature review + research idea report

**Primary sources:**

- `idea-stage/LITERATURE_REVIEW.md`
- `idea-stage/IDEA_REPORT.md`

**Direction:**

Question-aware executable table curation: train a small model to predict question-conditioned executable preprocessing operations.

**Ranked ideas:**

| Rank | Idea | Status in report | Interpretation |
| --- | --- | --- | --- |
| 1 | OpCurator | recommended after Step 0 | Train SLM + DSL executor for question-conditioned preprocessing. |
| 2 | HintBoost | safest option | Move existing TableAnalyzer hints into Stage 1 first. |
| 3 | OracleCuration | diagnostic | Estimate the ceiling of preprocessing-fixable errors. |

**Key dependency:**

The report explicitly depends on Step 0:

> If current hints injected into Stage 1 cannot improve accuracy by at least 1%, the whole learned preprocessing direction needs reassessment.

**Later interpretation:**

OpCurator may still be useful as an efficiency or Stage 1 strengthening direction. It is not the shortest path to improving final post-Refine accuracy because it tries to avoid Refine rather than make Refine more accurate.

---

### 2026-06-03: Structured Table Representation Design

**Type:** research/design proposal

**Primary source:**

- `docs/2026-06-03-structured-table-representation-design.md`

**Problem framing:**

The proposal argues that flat table linearization loses structural semantics and that the pipeline lacks code-level structural constraints on operation arguments.

**Method:**

Replace/upgrade `TableAnalyzer` with structured decomposition:

- column tree
- row structure
- meta constraints
- structural validation after each operation

**Important assumption:**

The draft aims to reduce the need for Refine by making Stage 1 more structurally aware.

**Later assessment:**

The direction is reasonable as supporting infrastructure, but its objective is partially misaligned with the current goal:

- Current target is final post-Refine accuracy.
- Refine remains valuable: WikiTQ +2.97pp, TabFact +1.92pp.
- Rule-based structural hints have already shown limited impact when used naively.

**What to keep:**

- Compact column/value type summaries.
- mixed-format parsing.
- answer format guidance.
- optional structure annotations as prompt evidence.

**What not to keep as main path:**

- Replacing Refine.
- Hard rule-based semantic decomposition as a gate.
- Defining success as skipping Refine.

---

### 2026-06-05: StructDiff-Refine Design

**Type:** research/design proposal

**Primary sources:**

- `docs/2026-06-05-structdiff-refine-design.md`
- `docs/2026-06-05-structdiff-refine-execution-plan.md`

**Goal:**

Improve final post-Refine accuracy while reducing ineffective broad Refine cost.

**Core idea:**

Convert Refine from global re-diagnosis into local evidence-based repair:

```text
Stage 1 Thought
  -> Judge
  -> Operation Trace Builder
  -> Evidence Pack Builder
  -> Step Localizer
  -> Diff-Critic
  -> Local Repair Executor
  -> Judge
```

**Key design distinction:**

This uses evidence, not hints.

| Evidence | Example |
| --- | --- |
| row diff | kept row ids, removed row ids |
| column diff | kept/dropped headers |
| sort evidence | target column values and monotonicity |
| group evidence | group column and counts |
| answer evidence | final answer and exact table-value candidates |

**Execution phases:**

| Milestone | Goal | Exit criterion |
| --- | --- | --- |
| M0 | Baseline / pilot slice fixed | reproducible 100/300-sample evaluation |
| M1 | Evidence-only Diff-Critic | accuracy not below baseline; token increase below 10% |
| M2 | Local Repair | correction rate improves without higher regression |
| M3 | Best-of-N + verifier ranking | hard subset improves; API calls within 1.2x full Controller |
| M4 | Adaptive Routing | full WikiTQ accuracy above baseline and cost down at least 20% |

**Current recommendation:**

Implement M1 only first:

1. operation trace
2. evidence pack
3. localization
4. Diff-Critic prompt
5. 100-sample pilot

Do not implement local repair, Best-of-N, and routing simultaneously; otherwise, the source of improvement cannot be isolated.

---

## 3. Experiment Result Registry

### Confirmed result records

| Experiment | Split | System | Accuracy | Cost / Tokens | Source |
| --- | --- | --- | ---: | ---: | --- |
| V-Critic quick validation | WikiTQ 5 | baseline | 60% | 90,686 tokens, 27 API calls | `experiments/v-critic-token-records.md` |
| V-Critic quick validation | WikiTQ 5 | V-Critic | 100% | 39,023 tokens, 12 API calls | `experiments/v-critic-token-records.md` |
| V-Critic pilot | WikiTQ 100 | baseline | 82% | 937,031 tokens, 285 API calls | `experiments/v-critic-token-records.md` |
| V-Critic pilot | WikiTQ 100 | V-Critic | 84% | 896,715 tokens, 273 API calls | `experiments/v-critic-token-records.md` |
| V-Critic full | WikiTQ 4344 | baseline | 84.05% | not recorded in same file | `experiments/v-critic-token-records.md` |
| V-Critic full | WikiTQ 4344 | V-Critic | 84.23% | 26,269,804 tokens, 7,584 API calls | `experiments/v-critic-token-records.md` |
| Stage 1 vs full pipeline | WikiTQ full | Stage 1 only | 81.98% | not recorded | `EXPERIMENT_PLAN_HINTS.md`, `StructDiff design` |
| Stage 1 vs full pipeline | WikiTQ full | full pipeline | 84.95% | not recorded | `EXPERIMENT_PLAN_HINTS.md`, `StructDiff design` |
| Stage 1 vs full pipeline | TabFact full | Stage 1 only | 93.63% | not recorded | `EXPERIMENT_PLAN_HINTS.md`, `StructDiff design` |
| Stage 1 vs full pipeline | TabFact full | full pipeline | 95.55% | not recorded | `EXPERIMENT_PLAN_HINTS.md`, `StructDiff design` |

### Important caveats

- The V-Critic full comparison is not fully fair: baseline uses non-flattened Thought, while V-Critic uses flattened Thought.
- The 5-sample result should only be treated as smoke validation.
- The 100-sample result is promising but not decisive.
- The full-run +0.18pp result makes V-Critic insufficient as a standalone contribution.

---

## 4. Direction Registry

### Active / recommended

| Direction | Status | Why |
| --- | --- | --- |
| StructDiff-Refine | active main line | Directly optimizes final post-Refine accuracy; reuses existing `get_table_log()` and verifier. |
| Evidence-only Diff-Critic | first implementation step | Isolates whether operation diff improves diagnosis before changing repair. |
| Local Repair | next step after positive M1 | Targets expensive broad re-execution and may improve precision. |
| Best-of-N + verifier ranking | conditional | Potential accuracy boost on hard cases, but cost must be gated. |

### Supporting / conditional

| Direction | Status | Condition |
| --- | --- | --- |
| Hints-to-Stage1 | gate experiment | Continue only if Stage 1 gain is at least 1pp. |
| OpCurator | longer-term preprocessing direction | Continue only if oracle/pre-hint experiments show enough ceiling. |
| Structured representation | supporting infrastructure | Use as evidence/metadata, not as a replacement for Refine. |
| AdaRefine routing | cost-control support | Use after accuracy path is stable; not as primary accuracy contribution. |

### Rejected / downgraded

| Direction | Reason |
| --- | --- |
| V-Critic standalone | Full-run gain too small and confounded. |
| Type-Aware Correction standalone | Too prompt-template-like. |
| CogDiag standalone | Cognitive framing weak; simpler random-few-shot/tree-skip baselines needed. |
| Pure Refine skipping | Misaligned with evidence that Refine adds 1.9-3.0pp. |

---

## 5. Current Research Narrative

The cleanest narrative is:

1. Table-Critic's final accuracy depends meaningfully on Refine.
2. Simple structure preprocessing and deterministic verifier signals are not enough as standalone contributions.
3. The real missing signal is operation-level transformation evidence.
4. `get_table_log()` already contains this signal, but the current Critic does not use it as a localized diff.
5. StructDiff-Refine turns Refine into a debugging loop:
   - trace operation states,
   - summarize deterministic evidence,
   - localize suspicious step,
   - criticize with focused diff context,
   - repair locally with fallback.

This reframes the project from:

```text
make Stage 1 strong enough to skip Refine
```

to:

```text
make Refine accurate, local, and evidence-driven
```

---

## 6. Recommended Next Work

### Immediate

Implement only M1 from the StructDiff execution plan:

- `operation_trace.py`
- `evidence_pack.py`
- `step_localizer.py`
- `diff_bundle.py`
- `get_cot_for_critic_diff()`
- `use_diff_critic=True` feature flag
- 100-sample pilot

### Do not do yet

- Do not train OpCurator before the Hints-to-Stage1 gate is validated.
- Do not implement Best-of-N before evidence-only Diff-Critic proves useful.
- Do not use adaptive routing to skip Refine aggressively until correct-case regression is measured.
- Do not move or delete historical docs until this timeline has been reviewed.

---

## 7. Source Index

### Architecture history

- `plans/implementation_decisions_and_dilemmas.md`
- `plans/controller.md`
- `plans/CLAUDE.md`

### Preprocessing / representation

- `docs/superpowers/specs/2026-04-23-table-flatten-design.md`
- `docs/superpowers/plans/2026-04-23-table-flatten.md`
- `docs/table-flatten-guide.md`
- `docs/2026-06-03-structured-table-representation-design.md`

### Refine direction exploration

- `logs/refine-logs/DIRECTION_EXPLORATION.md`
- `logs/refine-logs/PIPELINE_SUMMARY.md`
- `logs/refine-logs/FINAL_PROPOSAL.md`
- `logs/refine-logs/REFINEMENT_REPORT.md`
- `logs/refine-logs/round-0-initial-proposal.md`
- `logs/refine-logs/round-1-review.md`
- `logs/refine-logs/round-1-refinement.md`
- `logs/refine-logs/round-2-review.md`
- `logs/refine-logs/score-history.md`

### Experiment plans and trackers

- `logs/refine-logs/EXPERIMENT_PLAN.md`
- `logs/refine-logs/EXPERIMENT_PLAN_HINTS.md`
- `logs/refine-logs/EXPERIMENT_TRACKER.md`
- `experiments/v-critic-token-records.md`

### New active direction

- `docs/2026-06-05-structdiff-refine-design.md`
- `docs/2026-06-05-structdiff-refine-execution-plan.md`

### Idea-stage research

- `idea-stage/LITERATURE_REVIEW.md`
- `idea-stage/IDEA_REPORT.md`
