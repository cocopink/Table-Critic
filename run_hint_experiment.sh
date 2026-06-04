#!/bin/bash
# run_hint_experiment.sh
# Stage 0 + 0.5 + 1 only (skip Stage 2 Refine)
# Usage: bash run_hint_experiment.sh [QA|FV] [with_hints|no_hints] [first_n]
#
# Experiments:
#   E1 (no hints):  bash run_hint_experiment.sh QA no_hints -1
#   E2 (hints):     bash run_hint_experiment.sh QA with_hints -1
#
# Results go to: test/results/flattened/hint_exp/{task}/{model}/{label}/acc.txt

set -euo pipefail

TASK="${1:-QA}"
HINTS="${2:-with_hints}"        # "with_hints" or "no_hints"
FIRST_N="${3:--1}"               # number of samples, -1 = all

# API Configuration
base_url='https://113.44.247.131:47851/v1'
openai_api_key="$ANTHROPIC_AUTH_TOKEN"
model_name='gpt-5.4'

n_proc=8
chunk_size=4

# Mode: orig (no clarifier) to isolate hint effect
MODE="orig"

# ============== Task Configuration ==============
if [ "$TASK" = "FV" ]; then
    TASK_TYPE="TableFV"
    DATA_DIR="thought/TableFV/data/tabfact"
    ORIGINAL_DATA="${DATA_DIR}/test.jsonl"
    FLATTENED_DATA="${DATA_DIR}/test_flatten.jsonl"
    ANALYSIS_DATA="${DATA_DIR}/test_analyzed.jsonl"
    MAIN_SCRIPT="thought/TableFV/main.py"
    EXTRA_ARGS="--n_proc $n_proc --chunk_size $chunk_size"
else
    TASK_TYPE="TableQA"
    DATA_DIR="thought/TableQA/data/wikitq"
    ORIGINAL_DATA="${DATA_DIR}/test_lower.jsonl"
    FLATTENED_DATA="${DATA_DIR}/test_flatten.jsonl"
    ANALYSIS_DATA="${DATA_DIR}/test_analyzed.jsonl"
    MAIN_SCRIPT="thought/TableQA/main.py"
    EXTRA_ARGS=""
fi

# ============== Hints Configuration ==============
if [ "$HINTS" = "with_hints" ]; then
    USE_TABLE_ANALYZER="true"
    LABEL="E2_hints"
    echo "=========================================="
    echo "  Experiment: E2 (with table_analysis hints)"
    echo "  Task: $TASK | Samples: $FIRST_N"
    echo "=========================================="
elif [ "$HINTS" = "no_hints" ]; then
    USE_TABLE_ANALYZER="false"
    LABEL="E1_no_hints"
    echo "=========================================="
    echo "  Experiment: E1 (no hints, baseline)"
    echo "  Task: $TASK | Samples: $FIRST_N"
    echo "=========================================="
else
    echo "Usage: bash run_hint_experiment.sh [QA|FV] [with_hints|no_hints] [first_n]"
    exit 1
fi

# ============== Paths ==============
USE_FLATTEN="true"
RESULTS_BASE="test/results/flattened"
DATASET_TO_USE="$FLATTENED_DATA"
PREPROCESS_RESULTS="${RESULTS_BASE}/preprocess/${TASK,,}"
THOUGHT_RESULTS="${RESULTS_BASE}/hint_exp/${TASK,,}/${model_name}/${LABEL}"

# ============== Stage 0: Flatten ==============
echo ""
echo "Stage 0: Flatten"
echo "------------------------------------------"
mkdir -p "$PREPROCESS_RESULTS"

if [ ! -f "$FLATTENED_DATA" ]; then
    python preprocess.py \
        --dataset_path "$ORIGINAL_DATA" \
        --output_path "$FLATTENED_DATA" \
        --task_type "$TASK_TYPE" \
        --stats_path "$PREPROCESS_RESULTS/flatten_stats.json"
    if [ $? -ne 0 ]; then exit 1; fi
    echo "  Done"
else
    echo "  Using existing: $FLATTENED_DATA"
fi

# ============== Stage 0.5: Table Analysis (only for E2) ==============
if [ "$USE_TABLE_ANALYZER" = "true" ]; then
    echo ""
    echo "Stage 0.5: Table Analysis"
    echo "------------------------------------------"
    ANALYSIS_INPUT="$DATASET_TO_USE"

    if [ ! -f "$ANALYSIS_DATA" ] || [ "$ANALYSIS_DATA" -ot "$ANALYSIS_INPUT" ]; then
        python preprocess.py \
            --dataset_path "$ANALYSIS_INPUT" \
            --output_path "$ANALYSIS_DATA" \
            --task_type "$TASK_TYPE" \
            --analysis_only
        if [ $? -ne 0 ]; then exit 1; fi
        echo "  Done"
    else
        echo "  Using existing: $ANALYSIS_DATA"
    fi
    DATASET_TO_USE="$ANALYSIS_DATA"
fi

# ============== Stage 1: Thought (only, no Refine) ==============
echo ""
echo "Stage 1: Thought (hints=$HINTS, skip Refine)"
echo "------------------------------------------"
mkdir -p "$THOUGHT_RESULTS"

python "$MAIN_SCRIPT" \
    --dataset_path "$DATASET_TO_USE" \
    --thought_results_dir "$THOUGHT_RESULTS" \
    --base_url $base_url \
    --openai_api_key $openai_api_key \
    --model_name $model_name \
    --first_n $FIRST_N \
    --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False") \
    $EXTRA_ARGS

if [ $? -ne 0 ]; then
    echo "Error in Stage 1"
    exit 1
fi

# ============== Results ==============
echo ""
echo "=========================================="
echo "  Experiment Complete!"
echo "=========================================="
echo "  Task:       $TASK"
echo "  Config:     $LABEL"
echo "  Samples:    $FIRST_N"
echo "  Results:    $THOUGHT_RESULTS/"
echo ""
if [ -f "$THOUGHT_RESULTS/acc.txt" ]; then
    echo "  Accuracy:"
    cat "$THOUGHT_RESULTS/acc.txt"
fi
echo ""
echo "  Compare baselines:"
echo "    WikiTQ S1 orig:   test/results/flattened/thought/wikitq/${model_name}/acc.txt"
echo "    WikiTQ S1+S2 full: test/results/flattened/refine/wikitq/${model_name}/acc.txt"
echo "    TabFact S1 orig:   test/results/flattened/thought/tabfact/${model_name}/acc.txt"
echo "    TabFact S1+S2 full: test/results/flattened/refine/tabfact/${model_name}/acc.txt"
