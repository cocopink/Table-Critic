#!/bin/bash

# ========================================
# Table-Critic Ollama 驱动运行脚本
# 根据 demo0109.py 中的本地 LLM API 调用方式设计
# ========================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========================================
# Ollama 运行参数配置说明
# ========================================
# 以下参数可以通过环境变量或命令行参数设置：
#   OLLAMA_NUM_PARALLEL:    并行请求数（默认: 2）
#   OLLAMA_CONTEXT_LENGTH:  上下文长度（默认: 65536）
#
# 使用方式：
#   1. 环境变量: export OLLAMA_NUM_PARALLEL=2
#   2. 命令行参数: --num_parallel 2
# ========================================

# Ollama 配置
OLLAMA_HOST="http://localhost:11434"
OLLAMA_API_BASE="${OLLAMA_HOST}/v1"
OLLAMA_API_KEY="ollama"

# Ollama 运行参数配置（可通过环境变量或参数修改）
OLLAMA_NUM_PARALLEL=${OLLAMA_NUM_PARALLEL:-1}
OLLAMA_CONTEXT_LENGTH=${OLLAMA_CONTEXT_LENGTH:-64000}

# 默认模型（可通过参数修改）
DEFAULT_MODEL="qwen3:32b"

# 数据处理参数
FIRST_N=10
N_PROC=1
CHUNK_SIZE=1

# 任务类型（FV 或 QA）
TASK_TYPE="QA"

# Controller 参数（默认启用）
USE_CONTROLLER=True

# 添加时间戳用于日志文件命名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Clarifier 参数（默认启用）
USE_CLARIFIER=True

# 结果目录配置（不包含模型名，将在运行时动态添加）
# BASE_THOUGHT_RESULTS_FV='results/thought_100/tabfact'
# BASE_REFINE_RESULTS_FV='results/refine_100/tabfact'
# BASE_THOUGHT_RESULTS_QA='results/thought_100/wikitq'
# BASE_REFINE_RESULTS_QA='results/refine_100/wikitq'
BASE_THOUGHT_RESULTS_FV='results/thought/tabfact'
BASE_REFINE_RESULTS_FV='results/refine_clarifier/tabfact'
BASE_THOUGHT_RESULTS_QA='results/thought/wikitq'
BASE_REFINE_RESULTS_QA='results/refine_clarifier/wikitq'

# ========================================
# 函数定义
# ========================================

# 打印帮助信息
print_help() {
    echo "=========================================="
    echo "Table-Critic Ollama 驱动运行脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -t, --task TYPE      任务类型: FV (Table Fact Verification) 或 QA (Table Question Answering)"
    echo "  -m, --model MODEL    Ollama 模型名称 (默认: ${DEFAULT_MODEL})"
    echo "  -n, --first_n NUM    处理前 N 个样本 (默认: -1, 表示全部)"
    echo "  -p, --n_proc NUM     进程数 (默认: 1)"
    echo "  -c, --chunk_size NUM 批次大小 (默认: 1)"
    echo "  --use_controller BOOL 是否使用 controller (默认: True)"
    echo "  --use_clarifier BOOL 是否使用 clarifier (默认: True)"
    echo "  --num_parallel NUM   Ollama 并行请求数 (默认: ${OLLAMA_NUM_PARALLEL})"
    echo "  --context_length NUM Ollama 上下文长度 (默认: ${OLLAMA_CONTEXT_LENGTH})"
    echo "  -h, --help           显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 -t FV -m qwen2.5:14b"
    echo "  $0 -t QA -m llama3.1:8b"
    echo "  $0 -t QA -m qwen3:32b --num_parallel 2 --context_length 65536"
    echo ""
    echo "常用 Ollama 模型:"
    echo "  - qwen2.5:14b"
    echo "  - qwen2.5:7b"
    echo "  - llama3.1:8b"
    echo "  - llama3.1:70b"
    echo ""
    echo "查看可用模型: ollama list"
    echo "下载模型: ollama pull <model_name>"
    echo "=========================================="
}

# 检查 ollama 是否安装
check_ollama_installed() {
    if ! command -v ollama &> /dev/null; then
        echo -e "${RED}错误: Ollama 未安装${NC}"
        echo "请访问 https://ollama.com/download 安装 Ollama"
        exit 1
    fi
    echo -e "${GREEN}✓ Ollama 已安装${NC}"
}

# 检查 ollama 服务是否运行
check_ollama_running() {
    if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama 服务正在运行${NC}参数未更改"
        return 0
    else
        echo -e "${YELLOW}⚠ Ollama 服务未运行${NC}"
        return 1
    fi
}

# 启动 ollama 服务
start_ollama() {
    echo "正在启动 Ollama 服务..."
    export OLLAMA_NUM_PARALLEL="$OLLAMA_NUM_PARALLEL"
    export OLLAMA_CONTEXT_LENGTH="$OLLAMA_CONTEXT_LENGTH"
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    
    # 等待服务启动
    echo "等待 Ollama 服务启动..."
    for i in {1..30}; do
        if curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama 服务启动成功 (PID: ${OLLAMA_PID})${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}错误: Ollama 服务启动超时${NC}"
    exit 1
}

# 检查模型是否存在
check_model() {
    local model=$1
    echo "检查模型: ${model}"
    
    local model_list=$(ollama list 2>&1)
    if echo "$model_list" | grep -q "$model"; then
        echo -e "${GREEN}✓ 模型 ${model} 已存在${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ 模型 ${model} 不存在${NC}"
        echo "正在下载模型 ${model}..."
        if ollama pull "$model"; then
            echo -e "${GREEN}✓ 模型 ${model} 下载成功${NC}"
            return 0
        else
            echo -e "${RED}错误: 模型 ${model} 下载失败${NC}"
            exit 1
        fi
    fi
}

# 测试 Ollama API 连接
test_ollama_api() {
    local model=$1
    echo "测试 Ollama API 连接..."
    
    local response=$(curl -s "${OLLAMA_API_BASE}/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${model}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}],
            \"max_tokens\": 10
        }")
    
    if echo "$response" | grep -q "content"; then
        echo -e "${GREEN}✓ Ollama API 连接成功${NC}"
        return 0
    else
        echo -e "${RED}错误: Ollama API 连接失败${NC}"
        echo "响应: $response"
        exit 1
    fi
}

# 运行 TableFV 任务
run_table_fv() {
    local model=$1
    
    # 构建包含模型名的结果目录
    local thought_results_dir="${BASE_THOUGHT_RESULTS_FV}/${model}"
    local refine_results_dir="${BASE_REFINE_RESULTS_FV}/${model}"
    
    echo "=========================================="
    echo "开始运行 TableFV 任务"
    echo "=========================================="
    echo "模型: ${model}"
    echo "API 地址: ${OLLAMA_API_BASE}"
    echo "Thought 结果目录: ${thought_results_dir}"
    echo "Refine 结果目录: ${refine_results_dir}"
    echo "=========================================="
    
    # Thought 阶段
    echo ""
    echo "=========================================="
    echo "TableFV Thought 阶段"
    echo "=========================================="
    
    python3 thought/TableFV/main.py \
        --thought_results_dir $thought_results_dir \
        --base_url $OLLAMA_API_BASE \
        --openai_api_key $OLLAMA_API_KEY \
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
    
    python3 refine/TableFV/main_tree_based.py \
        --thought_results_dir $thought_results_dir \
        --refine_results_dir $refine_results_dir \
        --base_url $OLLAMA_API_BASE \
        --openai_api_key $OLLAMA_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE \
        --use_controller $USE_CONTROLLER \
        --use_clarifier $USE_CLARIFIER

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
    
    # 构建包含模型名的结果目录
    local thought_results_dir="${BASE_THOUGHT_RESULTS_QA}/${model}"
    local refine_results_dir="${BASE_REFINE_RESULTS_QA}/${model}"
    
    echo "=========================================="
    echo "开始运行 TableQA 任务"
    echo "=========================================="
    echo "模型: ${model}"
    echo "API 地址: ${OLLAMA_API_BASE}"
    echo "Thought 结果目录: ${thought_results_dir}"
    echo "Refine 结果目录: ${refine_results_dir}"
    echo "=========================================="
    
    # Thought 阶段
    echo ""
    echo "=========================================="
    echo "TableQA Thought 阶段"
    echo "=========================================="
    
    python3 thought/TableQA/main.py \
        --thought_results_dir $thought_results_dir \
        --base_url $OLLAMA_API_BASE \
        --openai_api_key $OLLAMA_API_KEY \
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
    
    python3 refine/TableQA/main_tree_based.py \
        --thought_results_dir $thought_results_dir \
        --refine_results_dir $refine_results_dir \
        --base_url $OLLAMA_API_BASE \
        --openai_api_key $OLLAMA_API_KEY \
        --model_name $model \
        --first_n $FIRST_N \
        --n_proc $N_PROC \
        --chunk_size $CHUNK_SIZE \
        --use_controller $USE_CONTROLLER \
        --use_clarifier $USE_CLARIFIER
    
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
        -u|--use_multi_agent)
            USE_MULTI_AGENT="$2"
            shift 2
            ;;
        --use_controller)
            USE_CONTROLLER="$2"
            shift 2
            ;;
        --use_clarifier)
            USE_CLARIFIER="$2"
            shift 2
            ;;
        --num_parallel)
            OLLAMA_NUM_PARALLEL="$2"
            shift 2
            ;;
        --context_length)
            OLLAMA_CONTEXT_LENGTH="$2"
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
echo "Table-Critic Ollama 驱动"
echo "=========================================="
echo "任务类型: ${TASK_TYPE}"
echo "模型: ${MODEL}"
echo "处理样本数: ${FIRST_N}"
echo "进程数: ${N_PROC}"
echo "批次大小: ${CHUNK_SIZE}"
echo "使用 Controller: ${USE_CONTROLLER}"
echo "使用 Clarifier: ${USE_CLARIFIER}"
echo "Ollama 并行数: ${OLLAMA_NUM_PARALLEL}"
echo "Ollama 上下文长度: ${OLLAMA_CONTEXT_LENGTH}"
echo "=========================================="
echo ""

# 检查 Ollama
check_ollama_installed

# 检查并启动 Ollama 服务
if ! check_ollama_running; then
    start_ollama
fi

# 检查模型
check_model "$MODEL"

# 测试 API 连接
test_ollama_api "$MODEL"

source /home/ubuntu/mnt/lx/new_TC/venv_shared_deepsearcher/bin/activate

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
