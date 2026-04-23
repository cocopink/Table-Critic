# Table Flatten Module Design Specification

**Date**: 2026-04-23
**Status**: Draft
**Author**: AI Assistant

---

## Overview

Design and implement a preprocessing module to flatten composite table structures in the Table-Critic framework. This module addresses bad cases caused by compound column headers (e.g., "date/time", "city/country") by intelligently splitting them into separate columns.

**Problem Statement**: Analysis of bad cases reveals that compound column headers (separated by `/`, `\n`, ` - `, etc.) cause confusion in table reasoning. The current pipeline cannot handle these multi-semantic column names effectively.

**Solution**: Implement a rule-based preprocessing stage that:
1. Detects compound column headers
2. Splits column names and corresponding cell values
3. Outputs flattened tables for downstream reasoning

---

## Architecture

### Current Pipeline

```
run_QA.sh → thought/TableQA/main.py → [Clarifier] → Reasoner → Results
             (reads test_lower.jsonl)    (optional)
```

### New Pipeline

```
run_QA.sh → preprocess.py → thought/TableQA/main.py → [Clarifier] → Reasoner → Results
              (reads test_lower.jsonl)   (reads test_flatten.jsonl)
              (writes test_flatten.jsonl)

Results Storage:
- Baseline:  results/thought/..., results/refine/...
- Flattened: results/flattened/thought/..., results/flattened/refine/...
```

### Directory Structure

```
Table-Critic/
├── preprocess.py                    # New: Preprocessing entry point
├── preprocess_utils/                # New: Preprocessing utilities
│   ├── __init__.py
│   ├── flatten.py                   # Core flattening logic
│   ├── detect.py                    # Compound header detection
│   └── cache.py                     # Caching utilities
├── thought/
│   └── TableQA/
│       ├── main.py                 # Unchanged (reads dataset via parameter)
│       └── data/
│           └── wikitq/
│               ├── test_lower.jsonl          # Original data (read-only)
│               └── test_flatten.jsonl        # Flattened data (generated)
└── results/
    ├── thought/                     # Baseline results (unchanged)
    ├── refine/                      # Baseline results (unchanged)
    └── flattened/                   # New: Flattened results
        ├── thought/
        ├── refine/
        └── preprocess/
            └── wikitq/
                └── flatten_stats.json
```

---

## Component Design

### 1. preprocess.py

**Purpose**: Entry point for preprocessing stage

**Interface**:
```python
def main(
    dataset_path: str = "thought/TableQA/data/wikitq/test_lower.jsonl",
    output_path: str = "thought/TableQA/data/wikitq/test_flatten.jsonl",
    task_type: str = "TableQA",  # TableQA or TableFV
    force_refresh: bool = False,
    stats_path: str = None,
)
```

**Flow**:
1. Check cache (if not force_refresh)
2. Load dataset from dataset_path
3. Apply flattening to all tables
4. Save to output_path
5. Generate statistics report

---

### 2. preprocess_utils/detect.py

**Purpose**: Detect compound headers in tables

**Key Functions**:

```python
def has_compound_headers(table: List[List]) -> bool:
    """Check if table has compound column headers.

    Args:
        table: Table as list of lists

    Returns:
        True if compound headers detected
    """
    header = table[0]
    separators = ['/', '\n', ' - ', '-', '|', ',']

    for cell in header:
        for sep in separators:
            if sep in str(cell):
                return True
    return False
```

---

### 3. preprocess_utils/flatten.py

**Purpose**: Core flattening logic

**Key Functions**:

```python
def flatten_table(table: List[List]) -> Tuple[List[List], Dict]:
    """Flatten a table with compound headers.

    Args:
        table: Original table

    Returns:
        (flattened_table, metadata)
    """
    header = table[0]
    compound_indices = find_compound_columns(header)

    if not compound_indices:
        return table, {"flattened": False}

    # Split compound columns
    new_header, split_map = split_header(header, compound_indices)
    new_rows = [new_header]

    for row in table[1:]:
        new_row = split_row(row, split_map)
        new_rows.append(new_row)

    metadata = {
        "flattened": True,
        "original_columns": len(header),
        "new_columns": len(new_header),
        "split_columns": len(compound_indices),
    }

    return new_rows, metadata
```

**Splitting Strategy**:

1. **Column Name Splitting**:
   - Use separator detected in header
   - Examples:
     - `"date/time"` → `"date"`, `"time"`
     - `"city\narea"` → `"city"`, `"area"`

2. **Cell Value Splitting** (Intelligent Fallback):
   - **Try #1**: Use header separator
     - `"1944-03-08 10:30"` with `/` → fails
   - **Try #2**: Try common patterns (space, `/`, `\n`, `,`)
     - `"1944-03-08 10:30"` with space → `"1944-03-08"`, `"10:30"` ✅
   - **Try #3**: If all fail, copy value to both columns
     - `"unknown"` → `"unknown"`, `"unknown"`

---

### 4. run_QA.sh Modifications

**Add Configuration**:
```bash
# Flatten switch
USE_FLATTEN="true"  # Set to "false" for baseline

# Path configuration
DATA_DIR="thought/TableQA/data/wikitq"
ORIGINAL_DATA="${DATA_DIR}/test_lower.jsonl"
FLATTENED_DATA="${DATA_DIR}/test_flatten.jsonl"

if [ "$USE_FLATTEN" = "true" ]; then
    RESULTS_BASE="results/flattened"
    DATASET_TO_USE="$FLATTENED_DATA"
else
    RESULTS_BASE="results"
    DATASET_TO_USE="$ORIGINAL_DATA"
fi
```

**Add Preprocessing Stage**:
```bash
if [ "$USE_FLATTEN" = "true" ]; then
    echo "Stage 0: Preprocessing"

    if [ ! -f "$FLATTENED_DATA" ]; then
        python preprocess.py \
            --dataset_path "$ORIGINAL_DATA" \
            --output_path "$FLATTENED_DATA" \
            --task_type TableQA \
            --stats_path "$PREPROCESS_RESULTS/flatten_stats.json"
    fi
fi
```

---

## Error Handling

### Conservative Strategy (Principle: Do No Harm)

**Detection Failure**:
- Log warning with table ID
- Skip flattening, use original table
- Continue with pipeline

**Splitting Failure**:
- Try multiple separators (ordered)
- Fall back to copying value to all split columns
- Log failure for analysis

**Data Corruption Prevention**:
- Original dataset is read-only
- Flattened data written to separate file
- Never overwrite original data

### Logging Strategy

```python
# Log file: results/flattened/preprocess/wikitq/flatten_stats.json
{
    "total_samples": 4344,
    "flattened_count": 127,  # Tables with compound headers
    "skipped_count": 4217,   # Tables without compound headers
    "failed_count": 0,       # Failed flattening attempts
    "split_details": {
        "date/time": 45,
        "city/country": 38,
        "time/retired": 27,
        "other": 17
    },
    "timestamp": "2026-04-23T22:30:00"
}
```

---

## Data Format

### Input Format (test_lower.jsonl)

```json
{
  "id": "nu-0",
  "table_text": [
    ["no.", "date/time", "location"],
    ["1", "1944-03-08 10:30", "Germany"]
  ],
  "question": "...",
  "answer": ["..."]
}
```

### Output Format (test_flatten.jsonl)

```json
{
  "id": "nu-0",
  "table_text": [
    ["no.", "date", "time", "location"],
    ["1", "1944-03-08", "10:30", "Germany"]
  ],
  "question": "...",
  "answer": ["..."],
  "flatten_metadata": {
    "flattened": true,
    "original_columns": 3,
    "new_columns": 4,
    "split_columns": 1
  }
}
```

**Note**: Tables without compound headers have `"flattened": false` and no other changes.

---

## Performance Optimization

### Caching Strategy

- Flattened data saved to `test_flatten.jsonl`
- Subsequent runs check cache first
- Only re-flatten if:
  - Cache file missing
  - `force_refresh=True`
  - Original data modified

### Skip Simple Tables

All tables are checked, but only those with compound headers are processed:
- Detection is fast (string search)
- No overhead for simple tables
- Early exit optimization

---

## Testing Strategy

### Unit Tests

```python
# tests/test_flatten.py

def test_detect_compound_headers():
    table = [["a/b", "c", "d\ne"], ["1", "2", "3"]]
    assert has_compound_headers(table) == True

def test_simple_header_detection():
    table = [["a", "b", "c"], ["1", "2", "3"]]
    assert has_compound_headers(table) == False

def test_slash_splitting():
    table = [["date/time"], ["1944-03-08 10:30"]]
    flattened, meta = flatten_table(table)
    assert flattened[0] == ["date", "time"]
    assert flattened[1] == ["1944-03-08", "10:30"]

def test_fallback_copy():
    table = [["a/b"], ["unknown"]]
    flattened, meta = flatten_table(table)
    assert flattened[1] == ["unknown", "unknown"]
```

### Integration Tests

```python
def test_end_to_end_preprocess():
    # Run preprocess.py
    # Verify test_flatten.jsonl created
    # Verify metadata correctness
    # Compare accuracy with baseline
```

### Manual Validation

Check first 10 flattened tables visually:
```bash
python preprocess.py ... | head -n 10
```

---

## Success Criteria

### Functional Requirements

- ✅ Detect all compound headers ( `/`, `\n`, ` - `, etc.)
- ✅ Split column names correctly
- ✅ Split cell values intelligently (multiple fallback strategies)
- ✅ Handle failures gracefully (copy value to both columns)
- ✅ Log all failures for analysis

### Non-Functional Requirements

- ✅ Zero data corruption (original data never modified)
- ✅ Performance: < 30 seconds for 4344 samples
- ✅ Caching works correctly
- ✅ Compatible with both TableQA and TableFV

### Quality Metrics

- **Data Integrity**: All flattened tables must be valid (no missing rows/columns)
- **Coverage**: ≥ 95% of compound headers correctly split
- **Fallback Success**: 100% (even worst case, copy values)

### Expected Impact

**Conservative Estimate**:
- Fix 2-5% of current bad cases
- Improve overall accuracy by 0.5-1.5 percentage points
- Minimal risk (conservative error handling)

**Measurement**:
```
Baseline:  results/thought/wikitq/{model}/acc.txt
Flattened: results/flattened/thought/wikitq/{model}/acc.txt

Expected: Flattened ≥ Baseline + 0.5%
```

---

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Create `preprocess_utils/` package
- [ ] Implement `detect.py` (compound header detection)
- [ ] Implement `flatten.py` (splitting logic with fallback)
- [ ] Create `preprocess.py` entry point
- [ ] Add logging and statistics

### Phase 2: Integration
- [ ] Modify `run_QA.sh` (add preprocessing stage)
- [ ] Modify `run_FV.sh` (add preprocessing stage)
- [ ] Test with TableQA
- [ ] Test with TableFV

### Phase 3: Validation
- [ ] Run baseline (USE_FLATTEN=false)
- [ ] Run flattened version (USE_FLATTEN=true)
- [ ] Compare accuracy
- [ ] Analyze bad cases
- [ ] Generate report

### Phase 4: Documentation
- [ ] Write user documentation (how to use)
- [ ] Write technical documentation (architecture)
- [ ] Update README.md
- [ ] Create examples

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Splitting incorrect values | Medium | Medium | Conservative fallback: copy to both columns |
| Performance degradation | Low | Low | Caching + early exit for simple tables |
| Breaking existing pipeline | Low | High | USE_FLATTEN flag for easy rollback |
| Edge cases not covered | Medium | Low | Comprehensive logging + iterative improvement |

---

## Future Enhancements

1. **LLM-Assisted Splitting**: Use LLM to detect semantic boundaries
2. **Custom Separators**: Per-dataset separator configuration
3. **Nested Table Support**: Handle true nested structures (tables within cells)
4. **Merge Column Support**: Inverse operation (merge related columns)
5. **Validation Rules**: Post-flatten data validation

---

## References

- Bad case analysis: `bad-case-analysis.md`, `semantic_bad_case_analysis.md`
- Example compound columns found: `date/time`, `city/country`, `time/retired`, `1939/40`, etc.
- Current pipeline documentation: `CLAUDE.md`

---

## Appendix A: Example Flattening

### Before (test_lower.jsonl)
```json
{
  "id": "nu-23",
  "table_text": [
    ["no.", "date/time", "aircraft", "location"],
    ["1", "8 march 1944", "me-109", "Germany"],
    ["2", "16 march 1944", "me-110", "Stuttgart"]
  ]
}
```

### After (test_flatten.jsonl)
```json
{
  "id": "nu-23",
  "table_text": [
    ["no.", "date", "time", "aircraft", "location"],
    ["1", "8 march 1944", "", "me-109", "Germany"],
    ["2", "16 march 1944", "", "me-110", "Stuttgart"]
  ],
  "flatten_metadata": {
    "flattened": true,
    "original_columns": 4,
    "new_columns": 5,
    "split_columns": 1,
    "split_details": ["date/time → date, time"]
  }
}
```

**Note**: Time field is empty in this case (no time information in original data).

---

## Appendix B: Separator Priority Order

```python
SEPARATOR_PRIORITY = [
    '/',      # Highest priority (most common)
    '\n',     # Newline (multi-level headers)
    ' - ',    # Dash with spaces
    '-',      # Dash without spaces
    '|',      # Pipe
    ',',      # Comma
]
```

**Rationale**: `/` is the most common separator in the dataset (observed in bad case analysis).

---

**End of Specification**
