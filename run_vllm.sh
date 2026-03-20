#!/bin/bash

# ========================================
# Table-Critic vLLM 驱动运行脚本
# 基于 run_ollama_model.sh 改编
# 使用 vLLM OpenAI API Server
# ========================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# vLLM 配置
VLLM_HOST="0.0.0.0"
VLLM_PORT="8000"
VLLM_API_BASE="http://localhost:${VLLM_PORT}/v1"
VLLM_API_KEY="EMPTY"

# 默认模型（需要预先下载到本地）
# DEFAULT_MODEL="/home/ubuntu/mnt/lx/model/Qwen3.5-27B-GPTQ-Int4"
DEFAULT_MODEL="/home/ubuntu/mnt/lx/model/Qwen3-14B"
# DEFAULT_MODEL="/home/ubuntu/mnt/lx/model/Qwen3-32B-AWQ"
# Qwen3-14B

# 数据处理参数
FIRST_N=100
N_PROC=1
CHUNK_SIZE=1

# 任务类型（FV 或 QA）
TASK_TYPE="FV"

# vLLM 服务进程
VLLM_PID=""

# 结果目录配置（不包含模型名，将在运行时动态添加）
BASE_THOUGHT_RESULTS_FV='results/thought_100/tabfact'
BASE_REFINE_RESULTS_FV='results/refine_vllm/tabfact'
BASE_THOUGHT_RESULTS_QA='results/thought_100/wikitq'
BASE_REFINE_RESULTS_QA='results/refine_vllm/wikitq'

# ========================================
# 函数定义
# ========================================

# 打印帮助信息
print_help() {
    echo "=========================================="
    echo "Table-Critic vLLM 驱动运行脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -t, --task TYPE      任务类型: FV (Table Fact Verification) 或 QA (Table Question Answering)"
    echo "  -m, --model MODEL    vLLM 模型名称 (默认: ${DEFAULT_MODEL})"
    echo "  -n, --first_n NUM    处理前 N 个样本 (默认: 100)"
    echo "  -p, --n_proc NUM     进程数 (默认: 1)"
    echo "  -c, --chunk_size NUM 批次大小 (默认: 1)"
    echo "  -s, --gpus NUM       GPU 数量 (默认: 1)"
    echo "  --port PORT          vLLM 服务端口 (默认: 8000)"
    echo "  -h, --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -t FV -m Qwen/Qwen2.5-14B-Instruct"
    echo "  $0 -t QA -m Qwen/Qwen2.5-7B-Instruct -s 1"
    echo "  $0 -t FV -m meta-llama/Llama-3.1-8B-Instruct -p 4"
    echo ""
    echo "常用 vLLM 模型 (HuggingFace 格式):"
    echo "  - Qwen/Qwen2.5-14B-Instruct"
    echo "  - Qwen/Qwen2.5-7B-Instruct"
    echo "  - meta-llama/Llama-3.1-8B-Instruct"
    echo "  - meta-llama/Llama-3.1-70B-Instruct"
    echo "  - mistralai/Mistral-7B-Instruct-v0.2"
    echo ""
    echo "模型下载: huggingface-cli download <model_name>"
    echo "或访问 https://huggingface.co/models"
    echo "=========================================="
}

# 清理函数
cleanup() {
    if [ -n "$VLLM_PID" ]; then
        echo "正在停止 vLLM 服务 (PID: $VLLM_PID)..."
        kill $VLLM_PID 2>/dev/null
        wait $VLLM_PID 2>/dev/null
        echo -e "${GREEN}✓ vLLM 服务已停止${NC}"
    fi
}

# 设置退出时清理
trap cleanup EXIT

# 检查 vllm 是否安装
check_vllm_installed() {
    if ! python -c "import vllm" 2>/dev/null; then
        echo -e "${RED}错误: vLLM 未安装${NC}"
        echo "请使用以下命令安装 vLLM:"
        echo "  pip install vllm"
        echo ""
        echo "或参考: https://docs.vllm.ai/en/latest/getting_started/installation.html"
        exit 1
    fi
    echo -e "${GREEN}✓ vLLM 已安装${NC}"
    
    # 检查 GPU 可用性
    if command -v nvidia-smi &> /dev/null; then
        echo "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "  GPU 检测成功"
    else
        echo -e "${YELLOW}⚠ 未检测到 NVIDIA GPU，vLLM 需要 GPU 才能运行${NC}"
    fi
}

# 检查 vLLM 服务是否运行
check_vllm_running() {
    if curl -s "${VLLM_API_BASE}/models" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ vLLM 服务正在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ vLLM 服务未运行${NC}"
        return 1
    fi
}

# 启动 vLLM 服务
start_vllm() {
    local model=$1
    local gpus=$2
    local port=$3
    
    echo "正在启动 vLLM 服务..."
    echo "模型: ${model}"
    echo "GPU 数量: ${gpus}"
    echo "端口: ${port}"
    
    # 启动 vLLM 服务# "/home/ubuntu/mnt/lx/model/Qwen3.5-9B" \
    python -m vllm.entrypoints.openai.api_server \
        --model "$model" \ 
        --host "$VLLM_HOST" \
        --port "$port" \
        --gpu-memory-utilization 0.85 \
        --tensor-parallel-size "$gpus" \
        --max-num-seqs 4 \
        > /tmp/vllm.log 2>&1 &
    
    VLLM_PID=$!
    
    # 等待服务启动
    echo "等待 vLLM 服务启动..."
    for i in {1..60}; do
        if curl -s "${VLLM_API_BASE}/models" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ vLLM 服务启动成功 (PID: ${VLLM_PID})${NC}"
            return 0
        fi
        sleep 2
    done
    
    echo -e "${RED}错误: vLLM 服务启动超时${NC}"
    echo "请检查日志: tail -f /tmp/vllm.log"
    exit 1
}

# 测试 vLLM API 连接
test_vllm_api() {
    local model=$1
    echo "测试 vLLM API 连接..."
    
    local response=$(curl -s "${VLLM_API_BASE}/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${VLLM_API_KEY}" \
        -d "{
            \"model\": \"${model}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}],
            \"max_tokens\": 10
        }")
    
    if echo "$response" | grep -q "content"; then
        echo -e "${GREEN}✓ vLLM API 连接成功${NC}"
        return 0
    else
        echo -e "${RED}错误: vLLM API 连接失败${NC}"
        echo "响应: $response"
        exit 1
    fi
}

# 运行 TableFV 任务
run_table_fv() {
    local model=$1
    
    # 提取模型名称的最后一个部分（用于结果目录）
    local model_name=$(basename "$model")
    
    # 构建包含模型名的结果目录
    local thought_results_dir="${BASE_THOUGHT_RESULTS_FV}/${model_name}"
    local refine_results_dir="${BASE_REFINE_RESULTS_FV}/${model_name}"
    
    echo "=========================================="
    echo "开始运行 TableFV 任务"
    echo "=========================================="
    echo "模型: ${model}"
    echo "API 地址: ${VLLM_API_BASE}"
    echo "Thought 结果目录: ${thought_results_dir}"
    echo "Refine 结果目录: ${refine_results_dir}"
    echo "=========================================="
    
    # Thought 阶段
    echo ""
    echo "=========================================="
    echo "TableFV Thought 阶段"
    echo "=========================================="
    
    python thought/TableFV/main.py \
        --thought_results_dir $thought_results_dir \
        --base_url $VLLM_API_BASE \
        --openai_api_key $VLLM_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: thought/TableFV/main.py 执行失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ TableFV Thought 阶段完成${NC}"
    
    # Refine 阶段
    echo ""
    echo "=========================================="
    echo "TableFV Refine 阶段"
    echo "=========================================="
    
    python refine/TableFV/main_tree_based.py \
        --thought_results_dir $thought_results_dir \
        --refine_results_dir $refine_results_dir \
        --base_url $VLLM_API_BASE \
        --openai_api_key $VLLM_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: refine/TableFV/main_tree_based.py 执行失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ TableFV Refine 阶段完成${NC}"
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}TableFV 任务完成！${NC}"
    echo "=========================================="
    echo "结果目录: ${refine_results_dir}"
    echo "=========================================="
}

# 运行 TableQA 任务
run_table_qa() {
    local model=$1
    
    # 提取模型名称的最后一个部分（用于结果目录）
    local model_name=$(basename "$model")
    
    # 构建包含模型名的结果目录
    local thought_results_dir="${BASE_THOUGHT_RESULTS_QA}/${model_name}"
    local refine_results_dir="${BASE_REFINE_RESULTS_QA}/${model_name}"
    
    echo "=========================================="
    echo "开始运行 TableQA 任务"
    echo "=========================================="
    echo "模型: ${model}"
    echo "API 地址: ${VLLM_API_BASE}"
    echo "Thought 结果目录: ${thought_results_dir}"
    echo "Refine 结果目录: ${refine_results_dir}"
    echo "=========================================="
    
    # Thought 阶段
    echo ""
    echo "=========================================="
    echo "TableQA Thought 阶段"
    echo "=========================================="
    
    python thought/TableQA/main.py \
        --thought_results_dir $thought_results_dir \
        --base_url $VLLM_API_BASE \
        --openai_api_key $VLLM_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: thought/TableQA/main.py 执行失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ TableQA Thought 阶段完成${NC}"
    
    # Refine 阶段
    echo ""
    echo "=========================================="
    echo "TableQA Refine 阶段"
    echo "=========================================="
    
    python refine/TableQA/main_tree_based.py \
        --thought_results_dir $thought_results_dir \
        --refine_results_dir $refine_results_dir \
        --base_url $VLLM_API_BASE \
        --openai_api_key $VLLM_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: refine/TableQA/main_tree_based.py 执行失败${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ TableQA Refine 阶段完成${NC}"
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}TableQA 任务完成！${NC}"
    echo "=========================================="
    echo "结果目录: ${refine_results_dir}"
    echo "=========================================="
}

# ========================================
# 主程序
# ========================================

# 解析命令行参数
GPUS=1
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--task)
            TASK_TYPE="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -n|--first_n)
            FIRST_N="$2"
            shift 2
            ;;
        -p|--n_proc)
            N_PROC="$2"
            shift 2
            ;;
        -c|--chunk_size)
            CHUNK_SIZE="$2"
            shift 2
            ;;
        -s|--gpus)
            GPUS="$2"
            shift 2
            ;;
        --port)
            VLLM_PORT="$2"
            VLLM_API_BASE="http://localhost:${VLLM_PORT}/v1"
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}错误: 未知参数 $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# 设置默认模型
if [ -z "$MODEL" ]; then
    MODEL=$DEFAULT_MODEL
fi

# 检查任务类型
if [ -z "$TASK_TYPE" ]; then
    echo -e "${RED}错误: 必须指定任务类型 (-t 或 --task)${NC}"
    print_help
    exit 1
fi

# 转换为大写
TASK_TYPE=$(echo "$TASK_TYPE" | tr '[:lower:]' '[:upper:]')

if [ "$TASK_TYPE" != "FV" ] && [ "$TASK_TYPE" != "QA" ]; then
    echo -e "${RED}错误: 任务类型必须是 FV 或 QA${NC}"
    print_help
    exit 1
fi

# 开始执行
echo ""
echo "=========================================="
echo "Table-Critic vLLM 驱动"
echo "=========================================="
echo "任务类型: ${TASK_TYPE}"
echo "模型: ${MODEL}"
echo "处理样本数: ${FIRST_N}"
echo "进程数: ${N_PROC}"
echo "批次大小: ${CHUNK_SIZE}"
echo "GPU 数量: ${GPUS}"
echo "API 地址: ${VLLM_API_BASE}"
echo "=========================================="
echo ""

# 检查 vLLM
check_vllm_installed

# 检查并启动 vLLM 服务
if ! check_vllm_running; then
    start_vllm "$MODEL" "$GPUS" "$VLLM_PORT"
fi

# 测试 API 连接
test_vllm_api "$MODEL"

# 根据任务类型运行
if [ "$TASK_TYPE" = "FV" ]; then
    run_table_fv "$MODEL"
elif [ "$TASK_TYPE" = "QA" ]; then
    run_table_qa "$MODEL"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "所有任务完成！"
echo "==========================================${NC}"
