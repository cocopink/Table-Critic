# Table-Critic Ollama 驱动使用说明

本脚本使用 Ollama 作为本地 LLM 驱动来运行 Table-Critic 项目。

## 前置要求

### 1. 安装 Ollama

访问 [Ollama 官网](https://ollama.com/download) 下载并安装适合您操作系统的版本。

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 下载 Ollama 模型

在运行脚本之前，需要先下载所需的模型。推荐使用以下模型之一：

```bash
# 下载 Qwen3 14B 模型（推荐）
ollama pull qwen3:14b

# 或者下载其他模型
ollama pull qwen3:7b
ollama pull llama3.1:8b
ollama pull llama3.1:70b
```

查看所有可用模型：
```bash
ollama list
```

## 使用方法

### 基本用法

运行 Table Fact Verification (FV) 任务：
```bash
./run_ollama.sh -t FV -m qwen3:14b
```

运行 Table Question Answering (QA) 任务：
```bash
./run_ollama.sh -t QA -m qwen3:14b
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--task` | `-t` | 任务类型：FV 或 QA | 必需 |
| `--model` | `-m` | Ollama 模型名称 | qwen2.5:14b |
| `--first_n` | `-n` | 处理前 N 个样本（-1 表示全部） | -1 |
| `--n_proc` | `-p` | 进程数 | 1 |
| `--chunk_size` | `-c` | 批次大小 | 1 |
| `--help` | `-h` | 显示帮助信息 | - |

### 使用示例

#### 示例 1：运行 FV 任务，使用默认模型
```bash
./run_ollama.sh -t FV
```

#### 示例 2：运行 QA 任务，指定模型
```bash
./run_ollama.sh -t QA -m llama3.1:8b
```

#### 示例 3：只处理前 10 个样本
```bash
./run_ollama.sh -t FV -m qwen3:14b -n 10
```

#### 示例 4：使用多进程处理
```bash
./run_ollama.sh -t QA -m qwen3:14b -p 4 -c 2
```

## 工作流程

脚本会自动执行以下步骤：

1. **检查 Ollama 安装**：验证 Ollama 是否已安装
2. **启动 Ollama 服务**：如果服务未运行，自动启动
3. **检查模型**：验证指定模型是否存在，不存在则自动下载
4. **测试 API 连接**：验证 Ollama API 是否正常工作
5. **运行任务**：
   - **Thought 阶段**：生成初步推理链
   - **Refine 阶段**：优化推理结果

## 输出结果

### TableFV 任务结果
结果目录会根据使用的模型自动创建子目录，例如：
- Thought 结果：`results/thought/tabfact/<模型名>/`
- Refine 结果：`results/refine/tabfact/<模型名>/`

示例：
- 使用 `qwen2.5:14b` 模型：
  - Thought 结果：`results/thought/tabfact/qwen3:14b/`
  - Refine 结果：`results/refine/tabfact/qwen3:14b/`
- 使用 `llama3.1:8b` 模型：
  - Thought 结果：`results/thought/tabfact/llama3.1:8b/`
  - Refine 结果：`results/refine/tabfact/llama3.1:8b/`

### TableQA 任务结果
结果目录会根据使用的模型自动创建子目录，例如：
- Thought 结果：`results/thought/wikitq/<模型名>/`
- Refine 结果：`results/refine/wikitq/<模型名>/`

示例：
- 使用 `qwen2.5:14b` 模型：
  - Thought 结果：`results/thought/wikitq/qwen3:14b/`
  - Refine 结果：`results/refine/wikitq/qwen3:14b/`
- 使用 `llama3.1:8b` 模型：
  - Thought 结果：`results/thought/wikitq/llama3.1:8b/`
  - Refine 结果：`results/refine/wikitq/llama3.1:8b/`

## 常见问题

### Q: 如何查看 Ollama 中已安装的模型？
```bash
ollama list
```

### Q: 如何下载新的模型？
```bash
ollama pull <model_name>
```

### Q: 如何停止 Ollama 服务？
```bash
pkill -f "ollama serve"
```

### Q: 脚本运行时提示 "Ollama 服务未运行" 怎么办？
脚本会自动尝试启动 Ollama 服务。如果启动失败，请手动运行：
```bash
ollama serve
```

### Q: 如何查看 Ollama 服务日志？
Ollama 服务日志会输出到终端。如果使用脚本启动，可以在后台查看进程日志。

### Q: 推荐使用哪个模型？
- **qwen3:14b**：推荐使用，性能和速度平衡
- **qwen3:7b**：速度更快，适合快速测试
- **llama3.1:8b**：通用性强，适合多种任务
- **llama3.1:70b**：性能最强，但需要更多资源

## 技术说明

### API 配置

脚本使用以下配置：

- **API 地址**：`http://localhost:11434/v1`
- **API Key**：`ollama`
- **Provider**：OpenAI 兼容接口

### Ollama 命令

脚本使用以下 Ollama 命令：

- `ollama serve`：启动 Ollama 服务
- `ollama list`：列出已安装的模型
- `ollama pull <model>`：下载模型
- `ollama run <model>`：运行模型（用于测试）

## 注意事项

1. **内存要求**：使用大模型（如 14B、70B）需要足够的系统内存
2. **GPU 加速**：如果有 NVIDIA GPU，Ollama 会自动使用 CUDA 加速
3. **并发处理**：多进程处理时，请确保系统资源充足
4. **模型下载**：首次运行时会下载模型，需要稳定的网络连接


## 许可证

本脚本遵循 Table-Critic 项目的许可证。
