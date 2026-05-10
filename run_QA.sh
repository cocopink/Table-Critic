# API Configuration
base_url='https://113.44.247.131:47851'
openai_api_key="$ANTHROPIC_AUTH_TOKEN"
model_name='gpt-5.4'

first_n=-1
n_proc=8
chunk_size=4

# Mode switch: set to "orig" for original mode, "new" for new mode
MODE="new"

# ============== Flatten Configuration ==============
USE_FLATTEN="true"  # Set to "false" for baseline version
DATA_DIR="thought/TableQA/data/wikitq"
ORIGINAL_DATA="${DATA_DIR}/test_lower.jsonl"
FLATTENED_DATA="${DATA_DIR}/test_flatten.jsonl"

# ============== TableAnalyzer Configuration ==============
USE_TABLE_ANALYZER="true"  # Set to "false" to skip analysis stage

# ============== Results Path Configuration ==============
if [ "$USE_FLATTEN" = "true" ]; then
    RESULTS_BASE="results/flattened"
    DATASET_TO_USE="$FLATTENED_DATA"
    echo "=========================================="
    echo "🚀 Running with FLATTENED tables"
    echo "=========================================="
else
    RESULTS_BASE="results"
    DATASET_TO_USE="$ORIGINAL_DATA"
    echo "=========================================="
    echo "📊 Running with ORIGINAL tables (baseline)"
    echo "=========================================="
fi

PREPROCESS_RESULTS="${RESULTS_BASE}/preprocess/wikitq"
ANALYSIS_DATA="${DATA_DIR}/test_analyzed.jsonl"
THOUGHT_RESULTS="${RESULTS_BASE}/thought/wikitq/${model_name}"
REFINE_RESULTS="${RESULTS_BASE}/refine/wikitq/${model_name}"

# ============== Stage 0: Preprocessing ==============
if [ "$USE_FLATTEN" = "true" ]; then
    echo ""
    echo "Stage 0: Preprocessing (Flatten Tables)"
    echo "------------------------------------------"

    mkdir -p "$PREPROCESS_RESULTS"

    if [ ! -f "$FLATTENED_DATA" ]; then
        echo "Flattening tables..."
        python preprocess.py \
            --dataset_path "$ORIGINAL_DATA" \
            --output_path "$FLATTENED_DATA" \
            --task_type TableQA \
            --stats_path "$PREPROCESS_RESULTS/flatten_stats.json"

        if [ $? -ne 0 ]; then
            echo "❌ Error in preprocessing stage"
            exit 1
        fi
        echo "✅ Preprocessing complete!"
    else
        echo "✅ Using existing flattened data: $FLATTENED_DATA"
    fi
    echo ""
fi

# ============== Stage 0.5: Table Analysis ==============
if [ "$USE_TABLE_ANALYZER" = "true" ]; then
    ANALYSIS_INPUT="$DATASET_TO_USE"

    if [ ! -f "$ANALYSIS_DATA" ] || [ "$ANALYSIS_DATA" -ot "$ANALYSIS_INPUT" ]; then
        echo "Stage 0.5: Table Analysis"
        echo "------------------------------------------"
        python preprocess.py \
            --dataset_path "$ANALYSIS_INPUT" \
            --output_path "$ANALYSIS_DATA" \
            --task_type TableQA \
            --analysis_only

        if [ $? -ne 0 ]; then
            echo "❌ Error in analysis stage"
            exit 1
        fi
        echo "✅ Analysis complete!"
    else
        echo "✅ Using existing analysis: $ANALYSIS_DATA"
    fi
    DATASET_TO_USE="$ANALYSIS_DATA"
    echo ""
fi

# ============== Stage 1: Thought ==============
python thought/TableQA/main.py \
--dataset_path "$DATASET_TO_USE" \
--thought_results_dir "$THOUGHT_RESULTS" \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")
if [ $? -ne 0 ]; then
    echo "Error in thought/TableQA/main.py"
    exit 1
fi


# ============== Stage 2: Refine ==============
python refine/TableQA/main_tree_based.py \
--thought_results_dir "$THOUGHT_RESULTS" \
--refine_results_dir "$REFINE_RESULTS" \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_controller $([ "$MODE" = "new" ] && echo "True" || echo "False") \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

if [ $? -ne 0 ]; then
    echo "Error in refine/TableQA/main_tree_based.py"
    exit 1
fi

echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
if [ "$USE_FLATTEN" = "true" ]; then
    echo "Mode: 🆕 Flattened Version"
    echo "Results: $RESULTS_BASE"
    echo ""
    echo "📊 Compare with baseline:"
    echo "  Baseline:  results/thought/wikitq/${model_name}/acc.txt"
    echo "  Flattened: results/flattened/thought/wikitq/${model_name}/acc.txt"
else
    echo "Mode: 📊 Baseline (Original)"
    echo "Results: $RESULTS_BASE"
fi
