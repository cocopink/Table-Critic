# Structured Table Representation with Structural Constraints for Table Reasoning

> Date: 2026-06-03
> Branch: `feat/learned-preprocess`
> Status: Draft

---

## 1. Problem Statement

### 1.1 Current Architecture Limitations

Table-Critic's four-stage pipeline (Preprocess → TableAnalyzer → Thought → Refine) has a fundamental asymmetry:

| Stage | LLM Cost | Accuracy Contribution |
|-------|-----------|----------------------|
| Stage 0 + 0.5 (Preprocess + TableAnalyzer) | 0 | +0.18% (84.05% → 84.23%) |
| Stage 1 (Thought) | ~6 calls/sample | Base accuracy |
| Stage 2 (Refine) | ~6-12 calls/sample | **Primary contributor** |

The Refine stage (Judge → Tree → Critic → dynamic chain re-execution) accounts for 80%+ of LLM cost but is the only stage that meaningfully improves accuracy. Previous attempts to inject `table_analysis` hints into Refine operations yielded negligible improvement (+0.18%), strongly suggesting that **the information content of rule-based `table_analysis` is insufficient** to improve reasoning regardless of injection point.

### 1.2 Root Cause

The current pipeline has two distinct constraint levels:

1. **Operation-type constraint** (already exists): A state machine (`possible_next_operation_dict`) constrains which operation types can follow others. E.g., `<init>` → `[add_column, select_row, select_column, group_column, sort_column]`.

2. **Structural constraint** (missing): No constraint on *what the operations must do* with the table. The LLM freely selects columns, rows, sort keys based on flat `table_text` with no awareness of table hierarchy, column semantics, or value format consistency.

The missing structural constraint layer means:
- The LLM must infer table structure from flat markdown text every time.
- Complex headers (merged cells, hierarchical columns, mixed units) are often misinterpreted.
- No code-level guarantee that operations respect table semantics.
- The Refine stage compensates by re-executing failed chains — expensive but necessary.

### 1.3 Research Foundation

Two recent research directions support this approach:

**Table Representation (No Training Required):**
- **OHD** (arXiv 2602.01969, 2026): Orthogonal Hierarchical Decomposition into column-tree + row-tree achieves 69.34 EM on AITQA, +20.02 over Chain-of-Table baseline. Replacing tree paths with Markdown/HTML drops EM by 16.24 and 19.34 respectively — explicit hierarchical structure preserves significantly more task-relevant information.
- **GraphOTTER** (COLING 2025): Converts tables to undirected graphs; LLM self-infers header relationships without pretrained annotations.
- **ACL 2024 Findings**: CoT + structured representation is a key multiplier (+19pp for Gemini Pro with Bracket representation).

**Hierarchical Control (Robotics → NLP):**
- **HTN Planning**: High-level task decomposition is *binding* — the executor cannot skip, reorder, or substitute the decomposition.
- **Skill-Critic / HMARL-CBF**: Skill commands are *conditioning parameters* in the executor's state, mathematically enforced (not advisory).
- **Core insight**: Constraints are enforced by code, not by the executor's "willingness" to follow suggestions.

---

## 2. Proposed Solution

### 2.1 Core Idea

Transform the current "soft hints" approach into a **structured representation + structural constraints** paradigm:

```
Stage 0:   Flatten (existing)                    ← zero LLM cost
Stage 0.5: Structured Decomposition (new)          ← zero LLM cost
              ↓ column_tree + row_tree + meta_constraints
Stage 1:   Constrained Thought (modified)          ← same LLM calls
              ↓ operation-type constraint (existing state machine)
              ↓ structural constraint (NEW: code-level enforcement)
Stage 2:   Refine (existing, reduced need)         ← fewer iterations
```

### 2.2 What Changes, What Doesn't

| Component | Change? | Description |
|-----------|---------|-------------|
| Stage 0 (Flatten) | No change | Existing rule-based flattening |
| Stage 0.5 (TableAnalyzer) | **Replaced** | New `StructuredDecomposer` outputs structured representation instead of text hints |
| Stage 1 (Thought chain state machine) | No change | `possible_next_operation_dict` stays the same |
| Stage 1 (Operation prompts) | **Modified** | Inject structured table representation into each operation's prompt |
| Stage 1 (Chain execution) | **Modified** | Add structural validation after each operation step |
| Stage 2 (Refine) | No change | Keep existing, but expect fewer samples need Refine |

---

## 3. Component Design

### 3.1 Stage 0.5: StructuredDecomposer (Zero LLM Cost)

Replaces `agents/table_analyzer.py`. Produces three artifacts:

#### 3.1.1 Column Tree

Hierarchical decomposition of columns, capturing parent-child relationships, data types, and units.

```python
# Input: flat column headers
["Player", "Season", "Points", "Rebounds"]

# Output: column_tree
{
    "identity": {
        "Player": {"type": "string", "semantic": "name"},
        "Season": {"type": "int", "semantic": "year"}
    },
    "statistics": {
        "Points": {"type": "float", "semantic": "average", "unit": "points"},
        "Rebounds": {"type": "float", "semantic": "average", "unit": "rebounds"}
    }
}
```

For complex headers (e.g., `"Total Population (in millions)"`):
```python
{
    "demographics": {
        "Total Population": {
            "type": "float",
            "semantic": "total",
            "unit": "millions",
            "display_suffix": "(in millions)"
        }
    }
}
```

**Construction rules** (all deterministic, zero LLM):
1. Parse header string for unit indicators: `(in ...)`, `(%)`, `(K)`, `(M)`, `(B)`
2. Group columns by semantic similarity (suffix overlap + value type consistency)
3. Infer data types by scanning first N rows (int/float/string/date/percentage/currency)
4. Build tree: parent = shared prefix or semantic group; children = individual columns

#### 3.1.2 Row Structure

Per-column value format patterns, detecting inconsistencies.

```python
{
    "Season": {
        "format": "integer",
        "range": [1999, 2004],
        "consistent": true
    },
    "Points": {
        "format": "float",
        "range": [25.3, 30.0],
        "consistent": true
    },
    "displacement": {
        "format": "mixed",
        "patterns": ["4.0l (242cid)", "4.7l (287cid)", "2.7l diesel", "3.1l diesel"],
        "consistent": false,
        "note": "mixed format: volume + engine type"
    }
}
```

#### 3.1.3 Meta Constraints

Table-level constraints derived from structure, enforced by chain execution code.

```python
{
    "must_normalize_before_sort": ["displacement"],  # mixed format column
    "column_hierarchy": {"displacement": ["volume", "engine_type"]},
    "implicit_columns": {  # columns not in table but derivable
        "country_of_athlete": {"source": "Player", "method": "extract_country"}
    },
    "key_column_candidates": ["Player", "Season"]  # columns likely used for lookup
}
```

### 3.2 Stage 1: Structural Constraint Integration

#### 3.2.1 Prompt Enhancement

Each operation receives the structured representation alongside the flat table text. The representation acts as a "schema annotation" — not a suggestion, but a factual description of table structure.

Example for `select_row`:
```
/*
col : rank | lane | player | time
row 1 :  | 5 | olga tereshkova (kaz) | 51.86
row 2 :  | 6 | manjeet kaur (ind) | 52.17
*/

Table Structure:
- identity: {player: string/name, lane: int/rank}
- performance: {time: float/seconds}
- Format notes: "player" column contains country code in parentheses

Question: how many athletes come from Japan?
```

This is **factual annotation** (like a schema DDL), not a "hint" or "suggestion". The LLM cannot disagree with the structural facts — it can only use them or ignore them (and if it ignores them, the chain execution validates).

#### 3.2.2 Chain Execution Validation

After each operation step, `chain.py` performs structural validation:

```python
def validate_structural_constraint(sample, operation_result, table_structure):
    """Code-level validation after each operation step."""
    violations = []

    # 1. Sort validation: if must_normalize_before_sort, verify format
    if operation_result["operation"] == "sort_column":
        sort_col = operation_result["column"]
        if sort_col in table_structure["meta_constraints"]["must_normalize_before_sort"]:
            if not is_normalized(operation_result["column_values"]):
                violations.append(
                    f"Column '{sort_col}' must be normalized before sorting. "
                    f"Format is: {table_structure['row_structure'][sort_col]['format']}"
                )

    # 2. Group validation: warn on grouping columns with >80% unique values
    if operation_result["operation"] == "group_column":
        # (This already exists in current code)

    # 3. Column selection validation: verify selected columns exist
    # ...

    return violations
```

**Key distinction from current hints**: Violations trigger **automatic corrective action** (re-prompt with explicit structural context), not just a text mention in the prompt. This is the "binding constraint" from HTN/Skill-Critic — the executor cannot proceed with an invalid operation.

### 3.3 Constraint Enforcement Levels

Three levels of enforcement, matching the robotics hierarchy:

| Level | Mechanism | Example | Enforced by |
|-------|-----------|---------|-------------|
| **L1: Factual annotation** | Structured representation in prompt | Column tree in `select_row` prompt | LLM (soft) |
| **L2: Pre-condition check** | Code validates operation before execution | Block `sort_column` on un-normalized mixed-format column | Code (hard) |
| **L3: Post-condition check** | Code validates result after execution | Verify sorted column is actually monotonic | Code (hard) |

L2 and L3 are the "binding constraints" — they cannot be bypassed by the LLM. This is analogous to HMARL-CBF's CBF constraints: the skill command is a conditioning parameter, not a suggestion.

---

## 4. Data Flow

```
Raw table (JSONL)
    │
    ▼
Stage 0: Flatten (existing)
    │ table_text (flattened markdown)
    │
    ▼
Stage 0.5: StructuredDecomposer (new)
    │ ├── column_tree     (JSON: hierarchical column structure)
    │ ├── row_structure   (JSON: per-column format analysis)
    │ └── meta_constraints(JSON: operation-level constraints)
    │
    │ All three stored as sample["table_structure"]
    │
    ▼
Stage 1: Constrained Thought
    │
    │ For each dynamic chain step:
    │   1. generate_prompt_for_next_step(sample, ...)
    │      └── table2string() enhanced with column_tree annotation
    │   2. LLM selects next operation + parameters
    │   3. L2 pre-condition check: validate against meta_constraints
    │      └── if violation: re-prompt with explicit constraint
    │   4. Execute operation
    │   5. L3 post-condition check: validate operation result
    │      └── if violation: retry with structural guidance
    │   6. Continue chain (respecting existing state machine)
    │
    ▼
Stage 2: Refine (existing, reduced need)
```

---

## 5. Implementation Plan

### Phase 1: StructuredDecomposer (Zero LLM)

Replace `agents/table_analyzer.py` with `agents/structured_decomposer.py`.

**Sub-modules:**
1. `ColumnTreeBuilder`: Parse headers → hierarchical tree (rule-based)
   - Unit extraction regex: `\((in |per |)(millions?|thousands?|%|K|M|B)\)`
   - Semantic grouping: suffix overlap + type consistency
   - Type inference: scan first 10 rows per column

2. `RowStructureAnalyzer`: Scan values → format patterns
   - Format detection: int/float/date/percentage/currency/mixed
   - Consistency check: all values match same format?
   - Range extraction: min/max for numeric columns

3. `MetaConstraintGenerator`: Structure → operation constraints
   - `must_normalize_before_sort`: columns with mixed/inconsistent formats
   - `column_hierarchy`: parent-child relationships for complex headers
   - `key_column_candidates`: columns with high uniqueness (>90% distinct)

**Compatibility**: Output stored as `sample["table_structure"]`, separate from existing `sample["table_analysis"]`. Backward compatible — existing code checks `table_analysis`, new code checks `table_structure`.

### Phase 2: Prompt Enhancement (Thought Operations)

Modify 6 operation files in `thought/TableQA/operations/` (and mirror to `thought/TableFV/operations/`):

- `select_column.py`: Inject column_tree to help LLM understand column relationships
- `select_row.py`: Inject row_structure + column_tree for precise row filtering
- `sort_by.py`: Inject format_normalizations from row_structure before sort
- `add_column.py`: Inject column_tree to suggest derivable columns
- `group_by.py`: Inject column_tree for semantic grouping
- `final_query.py`: Inject column_tree + row_structure for answer format

**Pattern**: Each operation's `*_build_prompt()` function gains an optional `table_structure=None` parameter. When present, a structured annotation block is appended to the prompt.

### Phase 3: Chain Execution Validation

Modify `thought/TableQA/utils/chain.py`:

- Add `validate_structural_constraint()` function
- Integrate into `dynamic_chain_exec_one_sample()` loop
- On L2 violation: re-prompt with explicit constraint context (1 retry)
- On L3 violation: log warning, continue (soft enforcement for post-conditions)

### Phase 4: Evaluation

Run on WikiTableQuestions (TableQA) and TabFact (TableFV):

| Experiment | Stage 0.5 | Stage 1 | Stage 2 | Metric |
|-----------|-----------|---------|---------|--------|
| E0: Baseline (existing) | TableAnalyzer hints | Flat prompt | Full Refine | Accuracy, LLM calls |
| E1: Structured only | StructuredDecomposer | Enhanced prompt | Full Refine | Accuracy, LLM calls |
| E2: Constrained chain | StructuredDecomposer | Enhanced + L2/L3 | Full Refine | Accuracy, LLM calls |
| E3: No Refine | StructuredDecomposer | Enhanced + L2/L3 | **Skip** | Accuracy, LLM calls |

**Success criterion**: E3 accuracy ≥ E0 accuracy with <50% of E0's LLM calls.

---

## 6. Key Design Decisions

### 6.1 Why Not Train a Model?

The user explicitly requires a no-training approach. Reasons:
- Training data scarcity: Table reasoning datasets are small (~2K-4K samples)
- Generalization risk: A model trained on Wikipedia tables may not transfer to financial/scientific tables
- Deployment complexity: Training adds pipeline dependencies (GPU, training infra)
- The bottleneck is not representation quality — it's whether the downstream executor *uses* the representation correctly

### 6.2 Why Not Just Better Prompts?

The current `table_analysis` hints are already "better prompts." They didn't work (+0.18%). The difference is:

| Aspect | Current hints | Proposed structured representation |
|--------|--------------|-------------------------------------|
| Format | Flat text strings | Hierarchical JSON tree |
| Granularity | Column-level annotations | Type + unit + format + hierarchy |
| Enforcement | LLM discretion | Code-level L2/L3 validation |
| Information | "This column might contain dates" | "Column X has mixed date formats: [list patterns]" |

### 6.3 Why Code-Level Constraints (L2/L3)?

Following the robotics insight: constraints enforced by code are **binding**, while constraints in prompts are **advisory**. The current pipeline puts all structural information in prompts and relies on the LLM to use it. The proposed approach adds code-level gates that the LLM cannot bypass, analogous to CBF constraints in HMARL-CBF.

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Structured representation adds tokens | Higher input cost per LLM call | Keep annotation concise (<200 tokens); measure token overhead in Phase 4 |
| L2/L3 validation false positives | Block valid operations | Start with L2 only (pre-condition), add L3 after validation |
| Rule-based decomposer makes mistakes | Wrong structural annotation → wrong constraints | Conservative: only annotate high-confidence patterns; fallback to no annotation |
| No training limits representation quality | Ceiling on improvement | Evaluate; if E1/E2 show promise, consider lightweight model in future work |
| WikiTQ/TabFact tables are simple | OHD's gains were on complex tables (AITQA) | Test on complex-table subsets separately |

---

## 8. Open Questions

1. Should `column_tree` replace `table_text` in prompts, or supplement it? (Recommendation: supplement — keep flat table for data access, add tree as annotation)
2. How to handle L2 violation retries without infinite loops? (Proposal: max 1 retry, then proceed with warning)
3. Should `StructuredDecomposer` be a drop-in replacement for `TableAnalyzer`, or coexist? (Recommendation: coexist, output to separate key `table_structure`)
4. What's the token overhead of structured annotation? Need to measure before full evaluation.

---

## 9. References

- OHD (2026): "Orthogonal Hierarchical Decomposition for Table Reasoning" — arXiv 2602.01969
- GraphOTTER (COLING 2025): Graph-based table representation with LLM self-inferred headers
- ACL 2024 Findings: "How Does Table Format Affect LLMs' Performance on Table QA?"
- Table-Critic (ACL 2025): Yu et al. — the base framework this work extends
- Skill-Critic (2023): Hierarchical RL with binding skill commands — arXiv 2306.08388
- HMARL-CBF (NeurIPS 2025): CBF-constrained multi-agent hierarchical RL
