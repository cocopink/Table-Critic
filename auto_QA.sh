#!/bin/bash

# ========================================
# Table-Critic 自动运行脚本
# 自动运行 TableFV 和 TableQA 的三个阶段（Thought、Critic、Refine）
# ========================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ollama 配置
OLLAMA_HOST="http://localhost:11434"
OLLAMA_API_BASE="${OLLAMA_HOST}/v1"
OLLAMA_API_KEY="ollama"

# 默认模型（可通过参数修改）
DEFAULT_MODEL="qwen3:14b"

# 数据处理参数
FIRST_N=2
N_PROC=2
CHUNK_SIZE=8

# 结果目录配置（包含模型名）
BASE_THOUGHT_RESULTS_FV='results/thought/tabfact'
BASE_CRITIC_RESULTS_FV='results/critic/tabfact'
BASE_REFINE_RESULTS_FV='results/refine/tabfact'

BASE_THOUGHT_RESULTS_QA='results/thought/wikitq'
BASE_CRITIC_RESULTS_QA='results/critic/wikitq'
BASE_REFINE_RESULTS_QA='results/refine/wikitq'

# ========================================
# 函数定义
# ========================================

# 打印帮助信息
print_help() {
    echo "=========================================="
    echo "Table-Critic 自动运行脚本"
    echo "=========================================="
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -m, --model MODEL    Ollama 模型名称 (默认: ${DEFAULT_MODEL})"
    echo "  -n, --first_n NUM    处理前 N 个样本 (默认: -1, 表示全部)"
    echo "  -p, --n_proc NUM     进程数 (默认: 1)"
    echo "  -c, --chunk_size NUM 批次大小 (默认: 1)"
    echo "  -h, --help           显示此帮助信息"
    echo ""
    echo "说明:"
    echo "  此脚本将自动顺序执行以下任务:"
    echo "  1. TableFV (Thought -> Critic -> Refine)"
    echo "  2. TableQA (Thought -> Critic -> Refine)"
    echo ""
    echo "示例:"
    echo "  $0 -m qwen2.5:14b"
    echo "  $0 -m llama3.1:8b -n 10"
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
        echo -e "${GREEN}✓ Ollama 服务正在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Ollama 服务未运行${NC}"
        return 1
    fi
}

# 启动 ollama 服务
start_ollama() {
    echo "正在启动 Ollama 服务..."
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


# 运行 TableQA 任务（三个阶段）
run_table_qa() {
    local model=$1
    
    # 构建包含模型名的结果目录
    local thought_results_dir="${BASE_THOUGHT_RESULTS_QA}/${model}"
    local critic_results_dir="${BASE_CRITIC_RESULTS_QA}/${model}"
    local refine_results_dir="${BASE_REFINE_RESULTS_QA}/${model}"
    
    echo ""
    echo -e "${BLUE}=========================================="
    echo "开始运行 TableQA 任务"
    echo -e "==========================================${NC}"
    echo "模型: ${model}"
    echo "API 地址: ${OLLAMA_API_BASE}"
    echo "处理样本数: ${FIRST_N}"
    echo "=========================================="
    
    # ==================== 阶段 1: Thought ====================
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "TableQA 阶段 1: Thought"
    echo -e "==========================================${NC}"
    
    python thought/TableQA/main.py \
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
    
    # # ==================== 阶段 2: Critic ====================
    # echo ""
    # echo -e "${YELLOW}=========================================="
    # echo "TableQA 阶段 2: Critic"
    # echo -e "==========================================${NC}"
    
    # python critic/TableQA/main.py \
    #     --thought_results_dir $thought_results_dir \
    #     --critic_results_dir $critic_results_dir \
    #     --base_url $OLLAMA_API_BASE \
    #     --openai_api_key $OLLAMA_API_KEY \
    #     --model_name $model \
    #     --first_n $FIRST_N \
    #     --n_proc $N_PROC \
    #     --chunk_size $CHUNK_SIZE
    
    # if [ $? -ne 0 ]; then
    #     echo -e "${RED}错误: critic/TableQA/main.py 执行失败${NC}"
    #     exit 1
    # fi
    
    echo -e "${GREEN}✓ TableQA Critic 阶段完成${NC}"
    
    # ==================== 阶段 2-3: Refine ====================
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "TableQA 阶段 3: Refine"
    echo -e "==========================================${NC}"
    
    python refine/TableQA/main_tree_based.py \
        --thought_results_dir $thought_results_dir \
        --refine_results_dir $refine_results_dir \
        --base_url $OLLAMA_API_BASE \
        --openai_api_key $OLLAMA_API_KEY \
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
    echo -e "${GREEN}=========================================="
    echo "TableQA 任务完成！"
    echo "==========================================${NC}"
    echo "结果目录:"
    echo "  - Thought: ${thought_results_dir}"
    echo "  - Critic:  ${critic_results_dir}"
    echo "  - Refine:  ${refine_results_dir}"
    echo "=========================================="
}

# ========================================
# 主程序
# ========================================

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
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

# 开始执行
echo ""
echo -e "${BLUE}=========================================="
echo "Table-Critic 自动运行脚本"
echo -e "==========================================${NC}"
echo "模型: ${MODEL}"
echo "处理样本数: ${FIRST_N}"
echo "进程数: ${N_PROC}"
echo "批次大小: ${CHUNK_SIZE}"
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

# 顺序运行 TableQA
run_table_qa "$MODEL"

# 完成
echo ""
echo -e "${GREEN}=========================================="
echo "所有任务完成！"
echo "==========================================${NC}"
echo ""
echo "执行顺序:"
echo "  1. TableFV (Thought -> Critic -> Refine)"
echo "  2. TableQA (Thought -> Critic -> Refine)"
echo ""
echo "结果目录:"
echo "  TableFV:"
echo "    - Thought: ${BASE_THOUGHT_RESULTS_FV}/${MODEL}"
echo "    - Critic:  ${BASE_CRITIC_RESULTS_FV}/${MODEL}"
echo "    - Refine:  ${BASE_REFINE_RESULTS_FV}/${MODEL}"
echo "  TableQA:"
echo "    - Thought: ${BASE_THOUGHT_RESULTS_QA}/${MODEL}"
echo "    - Critic:  ${BASE_CRITIC_RESULTS_QA}/${MODEL}"
echo "    - Refine:  ${BASE_REFINE_RESULTS_QA}/${MODEL}"
echo ""
