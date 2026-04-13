# Table-Critic vLLM 使用指南

## 概述

本指南说明如何使用 vLLM 替代 Ollama 来驱动 Table-Critic 项目。vLLM 是一个高性能的 LLM 推理服务框架，相比 Ollama 具有更高的吞吐量和更低的延迟。

## 兼容性分析

### ✅ 完全兼容

经过分析，`run_ollama_model.sh` 脚本可以成功迁移到 vLLM：

1. **API 兼容**：Python 代码使用 OpenAI SDK 调用 `client.chat.completions.create()`，vLLM 完全兼容此接口
2. **参数兼容**：脚本传递的参数 (`--base_url`, `--openai_api_key`, `--model_name`) 无需修改
3. **无需修改 Python 代码**：所有 LLM 调用逻辑保持不变

### 主要差异

| 特性 | Ollama | vLLM |
|------|--------|------|
| 默认端口 | 11434 | 8000 |
| 模型管理 | 自动下载 | 需本地模型文件 |
| 启动方式 | `ollama serve` | `python -m vllm.entrypoints.openai.api_server` |
| 性能 | 适合单用户 | 高吞吐量，支持张量并行 |
| API Key | `ollama` | `EMPTY` |

## 安装 vLLM

### 前置要求

- Python 3.8+
- CUDA 11.8+ (需要 NVIDIA GPU)
- 足够的 GPU 显存 (至少 16GB 推荐)

### 安装步骤

```bash
# 创建并激活虚拟环境 (推荐)
conda create -n vllm python=3.10
conda activate vllm

# 安装 vLLM
pip install vllm

# 验证安装
python -c "import vllm; print(vllm.__version__)"
```

### 下载模型

vLLM 需要预先下载模型到本地：

```bash
# 使用 Hugging Face CLI 下载
huggingface-cli download Qwen/Qwen2.5-14B-Instruct --local-dir ./models/Qwen2.5-14B-Instruct

# 或使用 modelscope
modelscope download --model Qwen/Qwen2.5-14B-Instruct --local_dir ./models/Qwen2.5-14B-Instruct
```

## 使用方法

### 基本用法

```bash
# 运行 TableFV 任务 (使用默认模型 Qwen/Qwen2.5-14B-Instruct)
./run_vllm.sh -t FV

# 运行 TableQA 任务
./run_vllm.sh -t QA
```

### 指定模型

```bash
# 使用不同的模型
./run_vllm.sh -t FV -m Qwen/Qwen2.5-7B-Instruct

# 使用 Llama 模型
./run_vllm.sh -t QA -m meta-llama/Llama-3.1-8B-Instruct
```

### 调整参数

```bash
# 处理前 50 个样本，使用 4 个进程
./run_vllm.sh -t FV -n 50 -p 4

# 使用 2 个 GPU (需要多 GPU 环境)
./run_vllm.sh -t QA -m meta-llama/Llama-3.1-70B-Instruct -s 2

# 自定义端口
./run_vllm.sh -t FV --port 8080
```

### 完整参数列表

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--task` | `-t` | (必需) | 任务类型: FV 或 QA |
| `--model` | `-m` | Qwen/Qwen2.5-14B-Instruct | 模型名称 (HuggingFace 格式) |
| `--first_n` | `-n` | 100 | 处理前 N 个样本 |
| `--n_proc` | `-p` | 1 | 并行进程数 |
| `--chunk_size` | `-c` | 1 | 批次大小 |
| `--gpus` | `-s` | 1 | GPU 数量 |
| `--port` | - | 8000 | vLLM 服务端口 |
| `--help` | `-h` | - | 显示帮助信息 |

## 运行示例

### 示例 1: TableFV 任务

```bash
# 使用 14B 模型运行 TableFV
./run_vllm.sh -t FV -m Qwen/Qwen2.5-14B-Instruct -n 100 -p 2

# 预期输出:
# ==========================================
# Table-Critic vLLM 驱动
# ==========================================
# 任务类型: FV
# 模型: Qwen/Qwen2.5-14B-Instruct
# ...
# ✓ vLLM 服务启动成功
# ✓ vLLM API 连接成功
# TableFV Thought 阶段
# ...
# ✓ TableFV Thought 阶段完成
# TableFV Refine 阶段
# ...
# ✓ TableFV Refine 阶段完成
```

### 示例 2: TableQA 任务

```bash
# 使用 7B 模型运行 TableQA (适合显存较小的环境)
./run_vllm.sh -t QA -m Qwen/Qwen2.5-7B-Instruct -n 50 -p 1
```

## 性能优化

### 多 GPU 加速

对于 70B 以上的大模型，建议使用多 GPU：

```bash
# 使用 4 个 GPU
./run_vllm.sh -t FV -m meta-llama/Llama-3.1-70B-Instruct -s 4
```

### 调整 GPU 显存利用率

如遇显存不足，可修改脚本中的 `--gpu-memory-utilization` 参数：

```bash
# 降低到 80%
--gpu-memory-utilization 0.8
```

### 批量处理

增加 `chunk_size` 可以提高吞吐量：

```bash
./run_vllm.sh -t FV -c 4 -p 4
```

## 故障排除

### 问题 1: vLLM 启动失败

**症状**: 服务启动超时

**解决方案**:
```bash
# 查看日志
tail -f /tmp/vllm.log

# 检查 GPU 状态
nvidia-smi

# 确认 CUDA 可用
python -c "import torch; print(torch.cuda.is_available())"
```

### 问题 2: 模型下载失败

**解决方案**:
```bash
# 设置 HuggingFace token
export HF_TOKEN="your_token_here"

# 或使用镜像
export HF_ENDPOINT="https://hf-mirror.com"
huggingface-cli download Qwen/Qwen2.5-14B-Instruct
```

### 问题 3: 显存不足

**解决方案**:
1. 使用更小的模型 (7B > 14B > 70B)
2. 降低 `--gpu-memory-utilization`
3. 使用量化模型 (如 AWQ/GPTQ)

### 问题 4: API 连接失败

**检查步骤**:
1. 确认端口未被占用: `netstat -tuln | grep 8000`
2. 确认服务正在运行: `curl http://localhost:8000/v1/models`
3. 检查防火墙设置

## 高级配置

### 使用自定义模型路径

修改脚本中的 `DEFAULT_MODEL` 为本地路径：

```bash
DEFAULT_MODEL="/path/to/your/model"
```

### API 认证

如需启用 API 认证：

```bash
# 在启动参数中添加
--api-key your-secret-key

# 调用时
curl -H "Authorization: Bearer your-secret-key" ...
```

### Docker 部署

```bash
# 使用 vLLM Docker 镜像
docker run --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen2.5-14B-Instruct
```

## 与 Ollama 对比

### 性能对比 (参考值)

| 模型 | Ollama (tokens/s) | vLLM (tokens/s) | 加速比 |
|------|-------------------|------------------|--------|
| Qwen2.5-7B | ~30 | ~60 | 2x |
| Qwen2.5-14B | ~15 | ~40 | 2.5x |
| Llama3.1-70B | ~5 | ~25 | 5x |

### 何时使用 vLLM

- ✅ 生产环境需要高吞吐量
- ✅ 使用大模型 (14B+)
- ✅ 需要多 GPU 加速
- ✅ 需要更低的延迟

### 何时使用 Ollama

- ✅ 快速原型开发
- ✅ 单 GPU 或无 GPU 环境
- ✅ 简单的模型管理
- ✅ 开发和测试阶段

## 常见问题 FAQ

### Q: vLLM 需要多少显存?

A: 建议至少 16GB。7B 模型约需 14GB，14B 模型约需 28GB，70B 模型约需 140GB。

### Q: 可以同时运行多个模型吗?

A: 可以，但需要使用不同端口启动多个 vLLM 实例。

### Q: 如何查看 vLLM 版本?

A: `python -c "import vllm; print(vllm.__version__)"`

### Q: 支持哪些模型?

A: vLLM 支持大多数 HuggingFace 格式的 Transformer 模型，包括 Llama、Qwen、Mistral 等。

## 相关文档

- [vLLM 官方文档](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [HuggingFace 模型库](https://huggingface.co/models)
