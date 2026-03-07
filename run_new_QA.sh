#!/bin/bash

# Game-Driven Memory Evolution TableQA Framework
# New QA Pipeline with Multi-Agent System

# ============== Configuration ==============
# Read API key from siliconflow.txt
SILICONFLOW_API_KEY=$(cat siliconflow.txt | tr -d '\n\r')

# SiliconFlow API Configuration
BASE_URL="https://api.siliconflow.cn/v1"
OPENAI_API_KEY="${SILICONFLOW_API_KEY}"
MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"

# Dataset Configuration
DATASET_PATH="thought/TableQA/data/wikitq/test_lower.jsonl"
#FIRST_N=${FIRST_N:--1}  # -1 means all samples, can be overridden via environment variable
FIRST_N=3

# Results Directory Configuration
MODEL_DIR="qwen2.5-72b-instruct"
THOUGHT_RESULTS_DIR="results/${MODEL_DIR}/thought"
REFINE_RESULTS_DIR="results/${MODEL_DIR}/refine"

# Processing Configuration
N_PROC=${N_PROC:-8}       # Number of parallel processes
CHUNK_SIZE=${CHUNK_SIZE:-4}  # Chunk size for multiprocessing

# Multi-Agent Configuration
USE_MULTI_AGENT=${USE_MULTI_AGENT:-true}  # Enable multi-agent framework

# ============== Print Configuration ==============
echo "=================================================="
echo "TableQA Multi-Agent Pipeline"
echo "=================================================="
echo "Model: ${MODEL_NAME}"
echo "Dataset: ${DATASET_PATH}"
echo "First N: ${FIRST_N}"
echo "Parallel Processes: ${N_PROC}"
echo "Multi-Agent: ${USE_MULTI_AGENT}"
echo "=================================================="
echo ""

# ============== Stage 1: Thought Phase with Clarifier ==============
echo "[Stage 1] Running Thought phase with ClarifierAgent..."
echo "Output: ${THOUGHT_RESULTS_DIR}"

python thought/TableQA/main.py \
    --dataset_path "${DATASET_PATH}" \
    --thought_results_dir "${THOUGHT_RESULTS_DIR}" \
    --base_url "${BASE_URL}" \
    --openai_api_key "${OPENAI_API_KEY}" \
    --model_name "${MODEL_NAME}" \
    --first_n ${FIRST_N} \
    --n_proc ${N_PROC} \
    --chunk_size ${CHUNK_SIZE}

if [ $? -ne 0 ]; then
    echo "❌ Error in thought/TableQA/main.py"
    exit 1
fi

# Check thought stage accuracy
if [ -f "${THOUGHT_RESULTS_DIR}/acc.txt" ]; then
    echo "✓ Thought Stage Accuracy:"
    cat "${THOUGHT_RESULTS_DIR}/acc.txt"
fi

echo ""
echo "[Stage 1] ✓ Thought phase completed"
echo ""

# ============== Stage 2: Refinement Phase with Multi-Agent Framework ==============
echo "[Stage 2] Running Refinement phase with Multi-Agent Framework..."
echo "Output: ${REFINE_RESULTS_DIR}"

python refine/TableQA/main_tree_based.py \
    --thought_results_dir "${THOUGHT_RESULTS_DIR}" \
    --refine_results_dir "${REFINE_RESULTS_DIR}" \
    --base_url "${BASE_URL}" \
    --openai_api_key "${OPENAI_API_KEY}" \
    --model_name "${MODEL_NAME}" \
    --first_n ${FIRST_N} \
    --n_proc ${N_PROC} \
    --chunk_size ${CHUNK_SIZE} \
    --use_multi_agent ${USE_MULTI_AGENT}

if [ $? -ne 0 ]; then
    echo "❌ Error in refine/TableQA/main_tree_based.py"
    exit 1
fi

# Check refine stage accuracy
if [ -f "${REFINE_RESULTS_DIR}/acc.txt" ]; then
    echo "✓ Refinement Stage Accuracy:"
    cat "${REFINE_RESULTS_DIR}/acc.txt"
fi

if [ -f "${REFINE_RESULTS_DIR}/result.txt" ]; then
    echo "✓ Final Result:"
    cat "${REFINE_RESULTS_DIR}/result.txt"
fi

echo ""
echo "[Stage 2] ✓ Refinement phase completed"
echo ""

# ============== Summary ==============
echo "=================================================="
echo "Pipeline Execution Summary"
echo "=================================================="
echo "Thought Results: ${THOUGHT_RESULTS_DIR}"
echo "  - Final result: ${THOUGHT_RESULTS_DIR}/final_result.pkl"
echo "  - Accuracy: ${THOUGHT_RESULTS_DIR}/acc.txt"
echo "  - Clarifier outputs: ${THOUGHT_RESULTS_DIR}/clarifier/"
echo ""
echo "Refinement Results: ${REFINE_RESULTS_DIR}"
echo "  - Final result: ${REFINE_RESULTS_DIR}/final_result.pkl"
echo "  - Accuracy: ${REFINE_RESULTS_DIR}/acc.txt"
echo "  - Thinking chains: ${REFINE_RESULTS_DIR}/cache/"
echo "=================================================="
echo ""
echo "✓ TableQA pipeline completed successfully!"
