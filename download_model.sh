#!/bin/bash

# ========================================
# vLLM 模型下载脚本
# 用于预先下载模型到本地
# ========================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 模型名称
MODEL="${1:-Qwen/Qwen3-14B-Instruct}"

# 下载目录 (默认当前目录的 models 子目录)
DOWNLOAD_DIR="${2:-./models}"

echo "=========================================="
echo "vLLM 模型下载脚本"
echo "=========================================="
echo "模型: ${MODEL}"
echo "下载目录: ${DOWNLOAD_DIR}"
echo "=========================================="

# 创建下载目录
mkdir -p "$DOWNLOAD_DIR"

# 检查是否安装了必要的工具
echo ""
echo "检查依赖..."

# 检查 Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误: Python 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 已安装${NC}"

# 检查 CUDA
python -c "import torch; assert torch.cuda.is_available(), 'CUDA不可用'" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CUDA 可用${NC}"
else
    echo -e "${YELLOW}⚠ CUDA 不可用，下载可能无法使用 GPU 加速${NC}"
fi

# 检查并安装必要的库
echo ""
echo "检查 Python 依赖..."

# 检查 huggingface-hub
python -c "import huggingface_hub" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装 huggingface-hub..."
    pip install huggingface-hub -q
fi
echo -e "${GREEN}✓ huggingface-hub 已安装${NC}"

# 检查并安装 transformers (用于验证模型)
python -c "import transformers" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装 transformers..."
    pip install transformers -q
fi
echo -e "${GREEN}✓ transformers 已安装${NC}"

# 检查并安装 vllm
python -c "import vllm" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ vLLM 未安装，如需运行推理需要安装${NC}"
fi

echo ""
echo "=========================================="
echo "开始下载模型: ${MODEL}"
echo "=========================================="
echo ""

# 方法 1: 使用 huggingface-cli (推荐)
echo "方法 1: 使用 huggingface-cli..."
if command -v huggingface-cli &> /dev/null; then
    huggingface-cli download "$MODEL" --local-dir "$DOWNLOAD_DIR/$(basename "$MODEL")"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 模型下载成功！${NC}"
        echo "模型路径: $DOWNLOAD_DIR/$(basename "$MODEL")"
        exit 0
    fi
fi

# 方法 2: 使用 Python 代码
echo ""
echo "方法 2: 使用 Python 下载..."
python << EOF
from huggingface_hub import snapshot_download
import os

try:
    local_dir = "$DOWNLOAD_DIR/$(basename('$MODEL'))"
    snapshot_download(
        repo_id="$MODEL",
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    print(f"模型已下载到: {local_dir}")
except Exception as e:
    print(f"下载失败: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ 模型下载成功！${NC}"
    echo "模型路径: $DOWNLOAD_DIR/$(basename "$MODEL")"
else
    echo -e "${RED}✗ 模型下载失败${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "下载完成！"
echo "=========================================="
echo ""
echo "使用示例:"
echo "  # 直接使用模型名称运行 (vLLM 会自动下载)"
echo "  ./run_vllm.sh -t FV -m ${MODEL}"
echo ""
echo "  # 或使用本地路径"
echo "  ./run_vllm.sh -t FV -m $DOWNLOAD_DIR/$(basename "$MODEL")"
echo "=========================================="
