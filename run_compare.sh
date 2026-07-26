#!/usr/bin/env bash
# run_compare.sh — 串行跑核心对比实验 E01 + E02
#   E01: baseline_original（原版 Table-Critic, Peiying-Yu）× 4b × wikitq × 500
#   E02: ours(p1p2, γ=0.05)（G-CRAFT 全增强）× 4b × wikitq × 500
# 本机单 GPU，串行避免 ollama 推理竞争。
set -uo pipefail
cd /home/cocopink/code/Table-Critic

TS=$(date +%Y%m%d_%H%M%S)
LOG="logs/compare_E01_E02_${TS}.log"
exec > >(tee -a "$LOG") 2>&1

echo "##############################################"
echo "# E01: baseline_original (4b × wikitq × 500) #"
echo "##############################################"
bash run_original_baseline.sh
e01_rc=$?
echo "E01 exit code: $e01_rc"

echo ""
echo "##############################################"
echo "# E02: ours p1p2 (4b × wikitq × 500, γ=0.05) #"
echo "##############################################"
bash run_experiments.sh --stage pilot --model 4b --dataset wikitq --variant p1p2
e02_rc=$?
echo "E02 exit code: $e02_rc"

echo ""
echo "##############################################"
echo "# E01+E02 DONE"
echo "# E01 (baseline_original) rc=$e01_rc"
echo "# E02 (ours p1p2)        rc=$e02_rc"
echo "##############################################"
echo "--- E01 baseline_original refine acc ---"
cat "test/results/refine/wikitq/qwen3.5:4b/original_s0_nothinking/acc.txt" 2>/dev/null
echo "--- E02 ours(p1p2) refine acc ---"
cat "test/results/refine/wikitq/qwen3.5:4b/p1p2_g0.05_nothinking_frozen_s0/acc.txt" 2>/dev/null
