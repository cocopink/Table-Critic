#!/bin/bash

# ==========================================
# Table-Critic Optimized Architecture
# ==========================================
# Script to run the optimized multi-agent architecture
# ==========================================

# Read API key
# API_KEY=$(cat siliconflow.txt)
API_KEY=$(cat api.txt)
BASE_URL='https://api.holdai.top/v1'

MODEL="qwen3-14b"

# Set result directories
THOUGHT_DIR="results/thought/$MODEL"
REFINE_DIR="results//refine/$MODEL"

# ==========================================
# Stage 1: Thought
# ==========================================
echo "=========================================="
echo "Stage 1: Thought"
echo "=========================================="

python thought/TableQA/main.py \
    --dataset_path "thought/TableQA/data/wikitq/test_lower.jsonl" \
    --thought_results_dir "$THOUGHT_DIR" \
    --base_url "$BASE_URL" \
    --openai_api_key "$API_KEY" \
    --model_name "$MODEL" \
    --first_n 10 \
    --n_proc 8 \
    --chunk_size 4

if [ $? -eq 0 ]; then
    echo "✓ Thought stage completed successfully"
else
    echo "✗ Thought stage failed"
    exit 1
fi

# ==========================================
# Stage 2: Refine
# ==========================================
echo "=========================================="
echo "Stage 2: Refine"
echo "=========================================="

python refine/TableQA/main_tree_based.py \
    --thought_results_dir "$THOUGHT_DIR" \
    --refine_results_dir "$REFINE_DIR" \
    --base_url "$BASE_URL" \
    --openai_api_key "$API_KEY" \
    --model_name "$MODEL" \
    --first_n 10 \
    --n_proc 10 \
    --chunk_size 5 \
    --use_multi_agent

if [ $? -eq 0 ]; then
    echo "✓ Refine stage completed successfully"
else
    echo "✗ Refine stage failed"
    exit 1
fi


# ==========================================
# All Stages Completed
# ==========================================
echo "=========================================="
echo "All stages completed successfully!"
echo "=========================================="
echo "Result directories:"
echo "  - Thought: $THOUGHT_DIR"
echo "  - Refine:  $REFINE_DIR"
echo "=========================================="
