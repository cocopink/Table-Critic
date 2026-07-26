#!/usr/bin/env bash
# run_original_baseline.sh — 原版 Table-Critic (Peiying-Yu) baseline
#
# 对比基准：无 ATG/QG-PPR/Controller/Clarifier/Diff-Critic，只有原版
# thought → critic → refine。用 ollama Qwen3.5-4B（已把我们的 ollama 原生
# 路径 think:False 注入原版 llm.py）。
#
# 用法:
#   bash run_original_baseline.sh                 # 默认 4b × wikitq × 500
#   FIRST_N=2 bash run_original_baseline.sh       # smoke 2 条
#   MODEL_NAME=qwen3.5:9b bash run_original_baseline.sh
#
# 结果存到本仓库 test/results/，与 G-CRAFT(ours) 的 p1p2 结果同目录层级，方便对比。

set -uo pipefail

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434/v1}"
API_KEY="EMPTY"
MODEL_NAME="${MODEL_NAME:-qwen3.5:4b}"
FIRST_N="${FIRST_N:-500}"
ORIG_REPO="${ORIG_REPO:-/home/cocopink/Table-Critic-original}"
OUR_REPO="/home/cocopink/code/Table-Critic"
RESULTS_BASE="${OUR_REPO}/test/results"

TAG="original_s0_nothinking"
THOUGHT_DIR="${RESULTS_BASE}/thought/wikitq/${MODEL_NAME}/${TAG}"
REFINE_DIR="${RESULTS_BASE}/refine/wikitq/${MODEL_NAME}/${TAG}"

mkdir -p "$THOUGHT_DIR" "$REFINE_DIR"

echo "=========================================="
echo "▶ Original Table-Critic baseline (Peiying-Yu)"
echo "  model=${MODEL_NAME}  dataset=wikitq  first_n=${FIRST_N}"
echo "  orig_repo=${ORIG_REPO}"
echo "  thought_dir=${THOUGHT_DIR}"
echo "  refine_dir=${REFINE_DIR}"
echo "=========================================="

cd "$ORIG_REPO" || { echo "❌ original repo not found: $ORIG_REPO"; exit 1; }

# error_tree hash before (原版无 frozen_memory，记录是否被写回)
CRITIC_TREE="${ORIG_REPO}/critic/TableQA/tools/few_shot_critic.json"
hash_before=""
if [[ -f "$CRITIC_TREE" ]]; then
    hash_before=$(sha256sum "$CRITIC_TREE" | cut -d' ' -f1)
    echo "[ORIGINAL] error_tree hash before: ${hash_before:0:16}"
fi

# Stage 1: Thought (原版，无 ATGO/Clarifier，直接用原始 test_lower.jsonl)
echo "▶ Stage 1: thought (original, no ATGO/Clarifier)"
python thought/TableQA/main.py \
    --dataset_path thought/TableQA/data/wikitq/test_lower.jsonl \
    --thought_results_dir "$THOUGHT_DIR" \
    --base_url "$OLLAMA_URL" \
    --openai_api_key "$API_KEY" \
    --model_name "$MODEL_NAME" \
    --first_n "$FIRST_N" \
    --n_proc 1 || { echo "❌ thought FAIL"; exit 1; }

# Stage 2: Refine (原版，无 Controller/Diff-Critic)
echo "▶ Stage 2: refine (original, no Controller)"
python refine/TableQA/main_tree_based.py \
    --thought_results_dir "$THOUGHT_DIR" \
    --refine_results_dir "$REFINE_DIR" \
    --base_url "$OLLAMA_URL" \
    --openai_api_key "$API_KEY" \
    --model_name "$MODEL_NAME" \
    --first_n "$FIRST_N" || { echo "❌ refine FAIL"; exit 1; }

# error_tree hash after
if [[ -n "$hash_before" && -f "$CRITIC_TREE" ]]; then
    hash_after=$(sha256sum "$CRITIC_TREE" | cut -d' ' -f1)
    if [[ "$hash_before" != "$hash_after" ]]; then
        echo "⚠ [ORIGINAL] error_tree MODIFIED during run (原版无 frozen_memory): before=${hash_before:0:16} after=${hash_after:0:16}"
    else
        echo "✓ [ORIGINAL] error_tree unchanged: ${hash_after:0:16}"
    fi
fi

echo "=========================================="
echo "✓ Original baseline done"
echo "  refine acc:"; cat "${REFINE_DIR}/acc.txt" 2>/dev/null
echo "  thought acc:"; cat "${THOUGHT_DIR}/acc.txt" 2>/dev/null
echo "=========================================="
