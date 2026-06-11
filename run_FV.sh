# API Configuration
base_url="${HAOMIAO_URL:-https://113.44.247.131:47851/v1}"
openai_api_key="${HAOMIAO_AUTHEN_TOKEN:-${HAOMIAO_AUTH_TOKEN:-$ANTHROPIC_AUTH_TOKEN}}"
model_name='gpt-5.4'

first_n=-1
n_proc=8
chunk_size=4

# Mode switch: set to "orig" for original mode, "new" for new mode
MODE="new"

# ============== TableAnalyzer Configuration ==============
USE_TABLE_ANALYZER="true"  # Set to "false" to skip analysis stage

# ============== Results Path Configuration ==============
RESULTS_BASE="test/results"
DATA_DIR="thought/TableFV/data/tabfact"
ORIGINAL_DATA="${DATA_DIR}/test.jsonl"
DATASET_TO_USE="$ORIGINAL_DATA"

ANALYSIS_DATA="${DATA_DIR}/test_analyzed.jsonl"
ATG_RERANK_DATA="${DATA_DIR}/test_reranked.jsonl"
ATGO_ROW_DATA="${DATA_DIR}/test_reranked_row.jsonl"
ATGC_COL_DATA="${DATA_DIR}/test_reranked_col.jsonl"
THOUGHT_RESULTS="${RESULTS_BASE}/thought/tabfact/${model_name}"
REFINE_RESULTS="${RESULTS_BASE}/refine/tabfact/${model_name}"

# ============== Logging Setup ==============
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SCRIPT_NAME=$(basename "$0" .sh)
LOG_FILE="${LOG_DIR}/${SCRIPT_NAME}-${model_name}-${TIMESTAMP}.log"

# Write parameter header to log
_masked_key="${openai_api_key:0:8}...${openai_api_key: -4}"
cat > "$LOG_FILE" <<EOF
=== Run Parameters (${TIMESTAMP}) ===
base_url           = ${base_url}
openai_api_key     = ${_masked_key}
model_name         = ${model_name}
first_n            = ${first_n}
n_proc             = ${n_proc}
chunk_size         = ${chunk_size}
MODE               = ${MODE}
USE_TABLE_ANALYZER = ${USE_TABLE_ANALYZER}
RESULTS_BASE       = ${RESULTS_BASE}
ORIGINAL_DATA      = ${ORIGINAL_DATA}
ATG_RERANK_DATA    = ${ATG_RERANK_DATA}
ATGO_ROW_DATA      = ${ATGO_ROW_DATA}
ATGC_COL_DATA      = ${ATGC_COL_DATA}
THOUGHT_RESULTS    = ${THOUGHT_RESULTS}
REFINE_RESULTS     = ${REFINE_RESULTS}
========================================
EOF

echo "📝 Log: ${LOG_FILE}"

# Redirect all subsequent output to both terminal and log file
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=========================================="
echo "📊 Running TableFV Pipeline (ATG + QG-PPR)"
echo "=========================================="

# ============== Stage 0.5: Table Analysis (disabled - preprocess.py deleted) ==============
# if [ "$USE_TABLE_ANALYZER" = "true" ]; then
#     ...
# fi

# # ============== Stage 0.6: ATG Reranking ==============
# if [ ! -f "$ATG_RERANK_DATA" ] || [ "$ATG_RERANK_DATA" -ot "$DATASET_TO_USE" ]; then
#     echo ""
#     echo "Stage 0.6: ATG + QG-PPR Reranking"
#     echo "------------------------------------------"
#     python preprocess.py \
#         --dataset_path "$DATASET_TO_USE" \
#         --output_path "$ATG_RERANK_DATA"

#     if [ $? -ne 0 ]; then
#         echo "❌ Error in ATG reranking stage"
#         exit 1
#     fi
#     echo "✅ ATG reranking complete!"
# else
#     echo "✅ Using existing ATG reranking: $ATG_RERANK_DATA"
# fi
# DATASET_TO_USE="$ATG_RERANK_DATA"

# # ============== Stage 1: Thought ==============
# echo ""
# echo "Stage 1: Thought"
# echo "------------------------------------------"
# python thought/TableFV/main.py \
# --dataset_path "$DATASET_TO_USE" \
# --thought_results_dir "$THOUGHT_RESULTS" \
# --base_url $base_url \
# --openai_api_key $openai_api_key \
# --model_name $model_name \
# --first_n $first_n \
# --n_proc $n_proc \
# --chunk_size $chunk_size \
# --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

# if [ $? -ne 0 ]; then
#     echo "Error in thought/TableFV/main.py"
#     exit 1
# fi

# # ============== Stage 2: Refine ==============
# echo ""
# echo "Stage 2: Refine (Controller-driven)"
# echo "------------------------------------------"
# python refine/TableFV/main_tree_based.py \
# --thought_results_dir "$THOUGHT_RESULTS" \
# --refine_results_dir "$REFINE_RESULTS" \
# --base_url $base_url \
# --openai_api_key $openai_api_key \
# --model_name $model_name \
# --first_n $first_n \
# --n_proc $n_proc \
# --chunk_size $chunk_size \
# --use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

# if [ $? -ne 0 ]; then
#     echo "Error in refine/TableFV/main_tree_based.py"
#     exit 1
# fi

# ============== Stage 0.7a: ATGO Row-only Reranking ==============
if [ ! -f "$ATGO_ROW_DATA" ] || [ "$ATGO_ROW_DATA" -ot "$ORIGINAL_DATA" ]; then
    echo ""
    echo "Stage 0.7a: ATGO Row-only Reranking"
    echo "------------------------------------------"
    python preprocess_atgo.py \
        --mode row \
        --dataset_path "$ORIGINAL_DATA" \
        --output_path "$ATGO_ROW_DATA"

    if [ $? -ne 0 ]; then
        echo "❌ Error in ATGO row-only reranking stage"
        exit 1
    fi
    echo "✅ ATGO row-only reranking complete!"
else
    echo "✅ Using existing ATGO row-only reranking: $ATGO_ROW_DATA"
fi

# ============== Stage 1-ATGO: Thought (Row-only) ==============
echo ""
echo "Stage 1-ATGO: Thought (Row-only)"
echo "------------------------------------------"
python thought/TableFV/main.py \
--dataset_path "$ATGO_ROW_DATA" \
--thought_results_dir "${THOUGHT_RESULTS}_row" \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

if [ $? -ne 0 ]; then
    echo "Error in Stage 1-ATGO"
    exit 1
fi

# ============== Stage 0.7b: ATGC Col-only Reranking ==============
if [ ! -f "$ATGC_COL_DATA" ] || [ "$ATGC_COL_DATA" -ot "$ORIGINAL_DATA" ]; then
    echo ""
    echo "Stage 0.7b: ATGC Col-only Reranking"
    echo "------------------------------------------"
    python preprocess_atgo.py \
        --mode col \
        --dataset_path "$ORIGINAL_DATA" \
        --output_path "$ATGC_COL_DATA"

    if [ $? -ne 0 ]; then
        echo "❌ Error in ATGC col-only reranking stage"
        exit 1
    fi
    echo "✅ ATGC col-only reranking complete!"
else
    echo "✅ Using existing ATGC col-only reranking: $ATGC_COL_DATA"
fi

# ============== Stage 1-ATGC: Thought (Col-only) ==============
echo ""
echo "Stage 1-ATGC: Thought (Col-only)"
echo "------------------------------------------"
python thought/TableFV/main.py \
--dataset_path "$ATGC_COL_DATA" \
--thought_results_dir "${THOUGHT_RESULTS}_col" \
--base_url $base_url \
--openai_api_key $openai_api_key \
--model_name $model_name \
--first_n $first_n \
--n_proc $n_proc \
--chunk_size $chunk_size \
--use_clarifier $([ "$MODE" = "new" ] && echo "True" || echo "False")

if [ $? -ne 0 ]; then
    echo "Error in Stage 1-ATGC"
    exit 1
fi

echo ""
echo "=========================================="
echo "Pipeline Complete!"
echo "=========================================="
echo "Results: $RESULTS_BASE"
