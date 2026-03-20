# Table-Critic 移植到 Deep-Searcher 架构设计

## 1. 概述

将 Table-Critic 的表格推理能力移植到 Deep-Searcher 报告生成框架中，在 RAG 流程中增加文本分析步骤。

## 2. 数据类型分析

### 2.1 CSV 表格数据
**路径**: `/home/ubuntu/mnt/lx/deep-searcher0109存档（全）/input_data/processed_split_data_clean/`

**示例**: `a地抗御/ma-1武器拦截命中率/红方拦截成功率/20251203_cleaned_merged.csv`

```csv
样本名称,ma_1弹头_杀伤率_命中率,命中率__百分比_
样本-1,0,50.0
样本-2,50,41.6667
样本-3,100,25.0
```

**特点**:
- 结构化表格数据
- 包含实验条件和结果
- 适合 Table-Critic 的表格推理能力

### 2.2 experiments_data 文本数据
**来源**: `processed_knowledge_base3_cleanedID.json`

**结构**:
```json
{
  "scenario_context": {...},
  "batch_name": "ma-1武器拦截命中率",
  "simulation_data": {
    "file": "20251204_cleaned.csv",
    "vars": ["样本名称", "弹药杀伤因数指标", "ma-1型武器弹头命中率"],
    "samples": [
      {
        "id": 1,
        "cond": {"样本名称": "样本-1", "弹药杀伤因数指标": 50, "ma-1型武器弹头命中率": 0},
        "data": [
          "信息链闭合情况分析|红交战[avg]:0公里1232.00秒...",
          "精度链闭合分析|红发现[avg]:0连发现: 2292.9m > 100m ×",
          "红方拦截成功率|红武器平台->蓝武器平台[avg]:50%",
          ...
        ]
      }
    ]
  }
}
```

**特点**:
- 仿真实验结果的文本描述
- 包含信息链、精度链、时间链等分析
- 适合直接使用 LLM 分析

## 3. 增强的 RAG 流程架构

### 3.1 原始流程
```
检索 (RAG) → 生成报告 → 反馈 → 检索 (RAG) → 生成报告 → 反馈
```

### 3.2 增强流程
```
检索 (RAG) → 文本分析 → 生成报告 → 反馈 → 检索 (RAG) → 文本分析 → 生成报告 → 反馈
```

### 3.3 文本分析模块结构

```
┌─────────────────────────────────────────────────────┐
│              文本分析模块 (TextAnalysisAgent)    │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼                               ▼
┌─────────────────┐              ┌─────────────────┐
│ 表格数据分析    │              │ 文本数据分析    │
│ (Table-Critic) │              │ (LLM Direct)   │
└─────────────────┘              └─────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐              ┌─────────────────┐
│ 表格数据洞察    │              │ 文本数据洞察    │
└─────────────────┘              └─────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         ▼
              ┌─────────────────┐
              │  综合分析结果   │
              └─────────────────┘
```

## 4. 组件设计

### 4.1 TextAnalysisAgent

**位置**: `deepsearcher/agent/text_analysis_agent.py`

**职责**:
- 协调表格分析和文本分析
- 整合两种分析结果
- 提供统一的文本分析接口

**核心方法**:
```python
class TextAnalysisAgent:
    def __init__(self, llm, table_reasoning_agent, enable_table_analysis=True):
        self.llm = llm
        self.table_reasoning_agent = table_reasoning_agent
        self.enable_table_analysis = enable_table_analysis
    
    def analyze(self, scenario_data, csv_files):
        """
        分析场景数据
        
        Args:
            scenario_data: 场景数据（包含 experiments_data）
            csv_files: CSV 表格文件列表
        
        Returns:
            analysis_result: 综合分析结果
        """
        # 1. 表格数据分析（可选）
        table_insights = None
        if self.enable_table_analysis and csv_files:
            table_insights = self._analyze_tables(csv_files)
        
        # 2. 文本数据分析
        text_insights = self._analyze_text_data(scenario_data)
        
        # 3. 整合结果
        return self._merge_insights(table_insights, text_insights)
```

### 4.2 TableReasoningAgent

**位置**: `deepsearcher/agent/table_reasoning_agent.py`

**职责**:
- 封装 Table-Critic 的表格推理能力
- 处理 CSV 表格数据
- 生成表格数据洞察

**核心方法**:
```python
class TableReasoningAgent:
    def __init__(self, llm):
        self.thought_module = ThoughtModule(llm)
        self.critic_module = CriticModule(llm)
        self.refine_module = RefineModule(llm)
    
    def analyze_table(self, table_path, statements):
        """
        分析表格数据
        
        Args:
            table_path: CSV 文件路径
            statements: 分析陈述列表
        
        Returns:
            insights: 表格数据洞察
        """
        # 1. 加载表格
        table = self._load_table(table_path)
        
        # 2. Thought: 生成推理链
        thought_results = []
        for statement in statements:
            result = self.thought_module.reason(table, statement)
            thought_results.append(result)
        
        # 3. Critic: 批评推理
        criticized_results = []
        for result in thought_results:
            criticized = self.critic_module.critic(result)
            criticized_results.append(criticized)
        
        # 4. Refine: 优化推理
        refined_results = []
        for result in criticized_results:
            refined = self.refine_module.refine(result)
            refined_results.append(refined)
        
        # 5. 生成洞察
        return self._generate_insights(refined_results)
```

### 4.3 CSV 到 Table-Critic 格式转换器

**位置**: `deepsearcher/agent/table_format_converter.py`

**职责**:
- 将 CSV 表格转换为 Table-Critic 需要的格式
- 自动生成分析陈述

**核心方法**:
```python
class TableFormatConverter:
    @staticmethod
    def convert_csv_to_table_critic(csv_path):
        """
        将 CSV 转换为 Table-Critic 格式
        
        Args:
            csv_path: CSV 文件路径
        
        Returns:
            table_text: 表格文本格式
            statements: 分析陈述列表
        """
        # 1. 读取 CSV
        df = pd.read_csv(csv_path)
        
        # 2. 转换为表格文本
        table_text = TableFormatConverter._df_to_table_text(df)
        
        # 3. 自动生成分析陈述
        statements = TableFormatConverter._generate_statements(df)
        
        return table_text, statements
    
    @staticmethod
    def _generate_statements(df):
        """
        自动生成分析陈述
        
        Args:
            df: pandas DataFrame
        
        Returns:
            statements: 陈述列表
        """
        statements = []
        
        # 生成相关性分析陈述
        if len(df.columns) >= 2:
            col1, col2 = df.columns[0], df.columns[1]
            statements.append(f"分析 {col1} 对 {col2} 的影响")
        
        # 生成趋势分析陈述
        if len(df) >= 3:
            statements.append(f"分析 {df.columns[0]} 的变化趋势")
        
        # 生成极值分析陈述
        for col in df.select_dtypes(include=[np.number]).columns:
            statements.append(f"找出 {col} 的最大值和最小值")
        
        return statements
```

## 5. 集成到 Deep-Searcher

### 5.1 修改 configuration.py

```python
# 在 init_config 中添加
def init_config(config: Configuration):
    global \
        module_factory, \
        llm, \
        embedding_model, \
        file_loader, \
        vector_db, \
        web_crawler, \
        default_searcher, \
        naive_rag, \
        text_analysis_agent  # 新增
    
    # ... 原有初始化代码 ...
    
    # 新增：初始化文本分析 Agent
    table_reasoning_agent = TableReasoningAgent(llm=llm)
    text_analysis_agent = TextAnalysisAgent(
        llm=llm,
        table_reasoning_agent=table_reasoning_agent,
        enable_table_analysis=True  # 可配置
    )
```

### 5.2 修改 DeepSearch Agent

```python
class DeepSearch(RAGAgent):
    def __init__(self, llm, embedding_model, vector_db, 
                 text_analysis_agent=None,  # 新增参数
                 max_iter=3, ...):
        self.llm = llm
        self.embedding_model = embedding_model
        self.vector_db = vector_db
        self.text_analysis_agent = text_analysis_agent  # 新增
        self.max_iter = max_iter
        # ...
    
    def query(self, query: str, scenario_data=None, csv_files=None, **kwargs):
        """
        查询并生成答案
        
        Args:
            query: 查询文本
            scenario_data: 场景数据（包含 experiments_data）
            csv_files: CSV 文件列表
            **kwargs: 其他参数
        
        Returns:
            answer: 生成的答案
            retrieved_results: 检索结果
            total_tokens: 总 token 消耗
        """
        # 1. 检索
        all_retrieved_results, n_token_retrieval, additional_info = self.retrieve(query, **kwargs)
        
        # 2. 文本分析（新增）
        analysis_context = ""
        if self.text_analysis_agent and scenario_data:
            analysis_result = self.text_analysis_agent.analyze(
                scenario_data=scenario_data,
                csv_files=csv_files
            )
            analysis_context = self._format_analysis_result(analysis_result)
        
        # 3. 生成报告（整合分析结果）
        if not all_retrieved_results or len(all_retrieved_results) == 0:
            return f"No relevant information found for query '{query}'.", [], n_token_retrieval
        
        chunk_texts = self._get_chunk_texts(all_retrieved_results)
        
        # 在 prompt 中加入分析结果
        summary_prompt = SUMMARY_PROMPT.format(
            question=query,
            mini_questions=additional_info["all_sub_queries"],
            mini_chunk_str=self._format_chunk_texts(chunk_texts),
            analysis_context=analysis_context  # 新增
        )
        
        chat_response = self.llm.chat([{"role": "user", "content": summary_prompt}])
        
        return (
            self.llm.remove_think(chat_response.content),
            all_retrieved_results,
            n_token_retrieval + chat_response.total_tokens,
        )
```

### 5.3 修改 demo0109.py

```python
# 在报告生成流程中集成文本分析
for scenario_idx, scenario in enumerate(all_scenarios_data):
    # ... 原有代码 ...
    
    # --- 3. 文本分析（新增）---
    print(f"  [文本分析] 开始分析场景数据...")
    
    # 获取该场景的 CSV 文件
    scenario_csv_files = []
    for merged_file in all_split_merged:
        if s_name in merged_file[0] and b_name in merged_file[0]:
            scenario_csv_files.append(merged_file[2])
    
    # 使用增强的 DeepSearch 进行查询
    result = query(
        Main_prompt,
        scenario_data=scenario,  # 新增
        csv_files=scenario_csv_files,  # 新增
        max_iter=3
    )
    
    # ... 后续代码 ...
```

## 6. 配置选项

### 6.1 启用/禁用表格分析

```python
# 在 configuration.py 中
text_analysis_agent = TextAnalysisAgent(
    llm=llm,
    table_reasoning_agent=table_reasoning_agent,
    enable_table_analysis=True  # True: 启用表格分析, False: 禁用
)
```

### 6.2 在查询时指定

```python
# 在 demo0109.py 中
result = query(
    Main_prompt,
    scenario_data=scenario,
    csv_files=scenario_csv_files if enable_table_analysis else None,
    max_iter=3
)
```

## 7. 文件结构

```
deepsearcher/
├── agent/
│   ├── text_analysis_agent.py          # 新增：文本分析 Agent
│   ├── table_reasoning_agent.py        # 新增：表格推理 Agent
│   ├── table_format_converter.py       # 新增：表格格式转换器
│   ├── deep_search.py                 # 修改：集成文本分析
│   └── ...
├── table_critic/                     # 新增：Table-Critic 模块
│   ├── thought/
│   │   ├── __init__.py
│   │   ├── thought_module.py
│   │   ├── operations/
│   │   └── utils/
│   ├── critic/
│   │   ├── __init__.py
│   │   ├── critic_module.py
│   │   └── tools/
│   ├── refine/
│   │   ├── __init__.py
│   │   ├── refine_module.py
│   │   └── operations/
│   └── utils/
│       └── llm.py
├── configuration.py                   # 修改：初始化文本分析 Agent
└── ...
```

## 8. 实施步骤

1. ✅ 分析 Table-Critic 和 deep-searcher 的核心架构
2. ✅ 调研 experiments_data 和 CSV 表格数据的实际格式
3. ✅ 与用户讨论双轨制移植方案
4. ⏳ 设计增强的 RAG 流程架构（检索→文本分析→生成）
5. ⏸️ 设计 TableReasoningAgent 类结构
6. ⏸️ 实现 CSV 到 Table-Critic 格式的转换器
7. ⏸️ 移植 Table-Critic 的 thought、critic、refine 模块
8. ⏸️ 集成到 deep-searcher 报告生成流程
9. ⏸️ 编写测试用例验证移植效果
