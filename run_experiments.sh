#!/usr/bin/env bash
# run_experiments.sh — G-CRAFT 实验编排脚本
#
# 在本机用 Ollama 跑 Qwen3.5-4B/9B 的图增强实验矩阵。
# 直接调用三阶段脚本（preprocess_atgo → thought → refine），绕过 run_*.sh
# 的 P1/P2 同开同关限制，支持 baseline/P1/P2/P1+P2 独立组合（R018）。
#
# 评测可信度修复（M0）依赖：
#   - R001: evaluator 固定分母（已修，evaluate.py）
#   - R002: frozen_memory 开关（main_tree_based.py --frozen_memory，跳过 UPDATE_TREE 写回）
#   - R005: 路径全维度隔离（本脚本路径含 model/variant/gamma/thinking/memory）
#
# 用法:
#   bash run_experiments.sh --stage smoke  [--model 4b|9b|2b] [--dataset wikitq|tabfact|both] [--variant baseline|p1|p2|p1p2|all]
#   bash run_experiments.sh --stage pilot  --model 4b --dataset wikitq --variant all
#   bash run_experiments.sh --stage full   --model 4b --dataset wikitq --variant p1p2
#
# stage:   smoke=50 条 / pilot=500 条 / full=全量(-1)
# variant: baseline(P1=P2=off) / p1(P1 on,γ=0.1) / p2(P2 on) / p1p2(P1+P2 on,γ=0.1)

set -uo pipefail

# ============== 默认配置 ==============
BACKEND="${BACKEND:-}"          # ollama | vllm（参数解析后据 backend 设 base_url/n_proc）
OLLAMA_URL="${OLLAMA_URL:-}"    # 据 backend 默认：ollama→11434, vllm→8000
API_KEY="EMPTY"
RESULTS_BASE="${RESULTS_BASE:-test/results}"
SEED=0
N_PROC="${N_PROC:-}"            # 据 backend 默认：ollama→1, vllm→4
CHUNK_SIZE="${CHUNK_SIZE:-1}"
THINKING="nothinking"          # ollama 原生路径自动 think:False（_is_ollama_qwen）
MEMORY="frozen"                # frozen_memory=True，禁止 UPDATE_TREE 写回

STAGE=""
MODEL=""
DATASET=""
VARIANT=""

# ============== 参数解析 ==============
while [[ $# -gt 0 ]]; do
    case "$1" in
        --stage)   STAGE="$2"; shift 2 ;;
        --model)   MODEL="$2"; shift 2 ;;
        --dataset) DATASET="$2"; shift 2 ;;
        --variant) VARIANT="$2"; shift 2 ;;
        --first_n) FIRST_N_OVERRIDE="$2"; shift 2 ;;
        --backend) BACKEND="$2"; shift 2 ;;
        -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

[[ -z "$STAGE" ]] && { echo "Error: --stage required (smoke|pilot|full)" >&2; exit 2; }
[[ -z "$MODEL" ]] && MODEL="4b"
[[ -z "$DATASET" ]] && DATASET="wikitq"
[[ -z "$VARIANT" ]] && VARIANT="p1p2"

case "$STAGE" in
    smoke) FIRST_N=50 ;;
    pilot) FIRST_N=500 ;;
    full)  FIRST_N=-1 ;;
    *) echo "Error: --stage must be smoke|pilot|full" >&2; exit 2 ;;
esac
# --first_n overrides stage default (for quick pipeline validation)
[[ -n "${FIRST_N_OVERRIDE:-}" ]] && FIRST_N="$FIRST_N_OVERRIDE"

[[ -z "${BACKEND:-}" ]] && BACKEND="ollama"
case "$BACKEND" in
    ollama)
        [[ -z "$OLLAMA_URL" ]] && OLLAMA_URL="http://localhost:11434/v1"
        [[ -z "${N_PROC:-}" ]] && N_PROC=1
        case "$MODEL" in
            2b) MODEL_NAME="qwen3.5:2b" ;;
            4b) MODEL_NAME="qwen3.5:4b" ;;
            9b) MODEL_NAME="qwen3.5:9b" ;;
            *) echo "Error: --model must be 2b|4b|9b" >&2; exit 2 ;;
        esac
        ;;
    vllm)
        [[ -z "$OLLAMA_URL" ]] && OLLAMA_URL="http://localhost:8000/v1"
        [[ -z "${N_PROC:-}" ]] && N_PROC=4
        case "$MODEL" in
            2b) MODEL_NAME="Qwen/Qwen3.5-2B" ;;
            4b) MODEL_NAME="Qwen/Qwen3.5-4B" ;;
            9b) MODEL_NAME="Qwen/Qwen3.5-9B" ;;
            *) echo "Error: --model must be 2b|4b|9b" >&2; exit 2 ;;
        esac
        ;;
    *) echo "Error: --backend must be ollama|vllm" >&2; exit 2 ;;
esac
echo "[BACKEND] $BACKEND | base_url=$OLLAMA_URL | model=$MODEL_NAME | n_proc=$N_PROC"

expand_datasets() {
    case "$DATASET" in
        both)          echo "wikitq tabfact" ;;
        wikitq|tabfact) echo "$DATASET" ;;
        *) echo "Error: --dataset must be wikitq|tabfact|both" >&2; exit 2 ;;
    esac
}

# variant → "P1 P2 gamma" (lowercase bool)
variant_to_pp() {
    case "$1" in
        baseline) echo "false false 0.0" ;;
        p1)       echo "true false 0.05" ;;
        p2)       echo "false true 0.0" ;;
        p1p2)     echo "true true 0.05" ;;
        *) return 1 ;;
    esac
}

expand_variants() {
    case "$VARIANT" in
        all) echo "baseline p1 p2 p1p2" ;;
        *)
            # 支持逗号分隔列表（如 baseline,p1p2），校验每个值
            local list; list=$(echo "$VARIANT" | tr ',' ' ')
            for v in $list; do
                case "$v" in
                    baseline|p1|p2|p1p2) ;;
                    *) echo "Error: --variant '$v' invalid; use baseline|p1|p2|p1p2|all or comma list" >&2; exit 2 ;;
                esac
            done
            echo "$list"
            ;;
    esac
}

# lowercase → fire bool string
to_fire_bool() { [[ "$1" == "true" ]] && echo "True" || echo "False"; }

# ============== 日志 + Manifest ==============
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
MANIFEST="${LOG_DIR}/experiment_manifest_${STAGE}_${MODEL}_${TIMESTAMP}.tsv"
echo -e "dataset\tvariant\tmodel\tstage\tfirst_n\tp1\tp2\tgamma\tthinking\tmemory\tthought_dir\trefine_dir\tstatus" > "$MANIFEST"
echo "📝 Manifest: $MANIFEST"

# ============== 单配置运行 ==============
run_one() {
    local ds="$1" var="$2"
    local p1p2gamma p1 p2 gamma
    p1p2gamma=$(variant_to_pp "$var") || return 1
    p1=$(echo "$p1p2gamma" | cut -d' ' -f1)
    p2=$(echo "$p1p2gamma" | cut -d' ' -f2)
    gamma=$(echo "$p1p2gamma" | cut -d' ' -f3)
    local p2_arg; p2_arg=$(to_fire_bool "$p2")

    local data_dir thought_entry refine_entry original_data critic_tree
    case "$ds" in
        wikitq)
            data_dir="thought/TableQA/data/wikitq"
            original_data="${data_dir}/test_lower.jsonl"
            thought_entry="thought/TableQA/main.py"
            refine_entry="refine/TableQA/main_tree_based.py"
            critic_tree="critic/TableQA/tools/few_shot_critic.json"
            ;;
        tabfact)
            data_dir="thought/TableFV/data/tabfact"
            original_data="${data_dir}/test.jsonl"
            thought_entry="thought/TableFV/main.py"
            refine_entry="refine/TableFV/main_tree_based.py"
            critic_tree="critic/TableFV/tools/few_shot_critic.json"
            ;;
    esac

    # 全维度路径（R005 隔离）：model/variant/gamma/thinking/memory/seed
    local tag="${var}_g${gamma}_${THINKING}_${MEMORY}_s${SEED}"
    local preprocess_out="${RESULTS_BASE}/preprocess/${ds}/${tag}.jsonl"
    local thought_dir="${RESULTS_BASE}/thought/${ds}/${MODEL_NAME}/${tag}"
    local refine_dir="${RESULTS_BASE}/refine/${ds}/${MODEL_NAME}/${tag}"

    mkdir -p "$(dirname "$preprocess_out")" "$thought_dir" "$refine_dir"

    echo ""
    echo "=========================================="
    echo "▶ ${ds} / ${var} / ${MODEL_NAME}  (stage=${STAGE}, first_n=${FIRST_N})"
    echo "  P1=${p1} P2=${p2} gamma=${gamma} | memory=${MEMORY}"
    echo "  thought_dir=${thought_dir}"
    echo "  refine_dir=${refine_dir}"
    echo "=========================================="

    local status="OK"

    # --- error_tree hash before (R002 验证：frozen 下应不变) ---
    local hash_before=""
    if [[ -f "$critic_tree" ]]; then
        hash_before=$(sha256sum "$critic_tree" | cut -d' ' -f1)
    fi

    # Stage 0: ATGO row rerank (P1 gamma + P2 graph hint)
    if [[ ! -f "$preprocess_out" || "$preprocess_out" -ot "$original_data" ]]; then
        echo "▶ Stage 0: preprocess_atgo (row, γ=${gamma}, hint=${p2})"
        if ! python preprocess_atgo.py \
                --mode row \
                --dataset_path "$original_data" \
                --output_path "$preprocess_out" \
                --gamma "$gamma" \
                --inject_graph_hint "$p2_arg"; then
            status="PREPROCESS_FAIL"
            echo -e "${ds}\t${var}\t${MODEL_NAME}\t${STAGE}\t${FIRST_N}\t${p1}\t${p2}\t${gamma}\t${THINKING}\t${MEMORY}\t${thought_dir}\t${refine_dir}\t${status}" >> "$MANIFEST"
            return 1
        fi
    else
        echo "✓ reuse preprocess: ${preprocess_out}"
    fi

    # Stage 1: Thought (Chain-of-Table 初始推理)
    echo "▶ Stage 1: thought"
    if ! python "$thought_entry" \
            --dataset_path "$preprocess_out" \
            --thought_results_dir "$thought_dir" \
            --base_url "$OLLAMA_URL" \
            --openai_api_key "$API_KEY" \
            --model_name "$MODEL_NAME" \
            --first_n "$FIRST_N" \
            --n_proc "$N_PROC" \
            --chunk_size "$CHUNK_SIZE" \
            --use_clarifier True; then
        status="THOUGHT_FAIL"
        echo -e "${ds}\t${var}\t${MODEL_NAME}\t${STAGE}\t${FIRST_N}\t${p1}\t${p2}\t${gamma}\t${THINKING}\t${MEMORY}\t${thought_dir}\t${refine_dir}\t${status}" >> "$MANIFEST"
        return 1
    fi

    # Stage 2: Refine (Controller 驱动, frozen_memory=True)
    echo "▶ Stage 2: refine (frozen_memory=${MEMORY})"
    if ! python "$refine_entry" \
            --thought_results_dir "$thought_dir" \
            --refine_results_dir "$refine_dir" \
            --base_url "$OLLAMA_URL" \
            --openai_api_key "$API_KEY" \
            --model_name "$MODEL_NAME" \
            --first_n "$FIRST_N" \
            --n_proc "$N_PROC" \
            --chunk_size "$CHUNK_SIZE" \
            --use_clarifier True \
            --frozen_memory True; then
        status="REFINE_FAIL"
        echo -e "${ds}\t${var}\t${MODEL_NAME}\t${STAGE}\t${FIRST_N}\t${p1}\t${p2}\t${gamma}\t${THINKING}\t${MEMORY}\t${thought_dir}\t${refine_dir}\t${status}" >> "$MANIFEST"
        return 1
    fi

    # --- error_tree hash after (R002 验证) ---
    if [[ -n "$hash_before" && -f "$critic_tree" ]]; then
        local hash_after; hash_after=$(sha256sum "$critic_tree" | cut -d' ' -f1)
        if [[ "$hash_before" != "$hash_after" ]]; then
            echo "⚠ [FROZEN-MEMORY WARNING] ${critic_tree} MODIFIED during run! before=${hash_before:0:16} after=${hash_after:0:16}"
            status="${status};TREE_MODIFIED"
        else
            echo "✓ [FROZEN-MEMORY OK] ${critic_tree} unchanged: ${hash_after:0:16}"
        fi
    fi

    echo -e "${ds}\t${var}\t${MODEL_NAME}\t${STAGE}\t${FIRST_N}\t${p1}\t${p2}\t${gamma}\t${THINKING}\t${MEMORY}\t${thought_dir}\t${refine_dir}\t${status}" >> "$MANIFEST"
    echo "✓ ${ds} / ${var} done"
    return 0
}

# ============== 主循环 ==============
FAIL_COUNT=0
for ds in $(expand_datasets); do
    for var in $(expand_variants); do
        if ! run_one "$ds" "$var"; then
            echo "⚠ failed: ${ds}/${var}, continuing to next config"
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    done
done

echo ""
echo "=========================================="
echo "✅ Experiment batch complete (failures: ${FAIL_COUNT})"
echo "📝 Manifest: ${MANIFEST}"
echo "=========================================="
cat "$MANIFEST"
[[ "$FAIL_COUNT" -eq 0 ]] && exit 0 || exit 1
