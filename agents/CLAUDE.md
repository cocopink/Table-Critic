# Agents 模块文档

[根目录](../CLAUDE.md) > **agents**

> 最后更新：2026-04-16 00:17:51

---

## 变更记录 (Changelog)

### 2026-04-16
- 初始化 agents 模块文档
- 识别 9 个核心智能体
- 建立 BaseAgent 框架文档

---

## 模块职责

Agents 模块是 Table-Critic 的**多智能体框架核心**，实现了基于博弈论的协作推理系统。

### 核心功能

1. **智能体类型定义**：9 种专业化智能体，覆盖推理全流程
2. **通信协议**：标准化的消息传递机制
3. **状态管理**：AgentState 维护智能体的运行时状态
4. **框架基础**：BaseAgent 提供统一的接口和行为规范

---

## 入口与启动

### 主入口

```python
from agents import (
    ClarifierAgent,
    InitialReasoner,
    JudgeAgent,
    CriticAgent,
    RefinerAgent,
    ValidatorAgent,
    CuratorAgent,
    RetrieverAgent,
    MultiAgentOrchestrator
)
```

### 使用示例

```python
from thought.TableQA.utils.llm import LLM
from agents import ClarifierAgent

# 初始化 LLM
llm = LLM(model_name="qwen3:32b", key="api_key", base="url")

# 创建 Clarifier
clarifier = ClarifierAgent(llm=llm)

# 处理样本
clarified_sample = clarifier.clarify_sample(sample)
```

---

## 对外接口

### BaseAgent 基类

**文件**：`agents/multi_agent_framework.py`

```python
class BaseAgent:
    def __init__(self, agent_type: AgentType, llm=None):
        """
        初始化基础智能体

        Args:
            agent_type: 智能体类型（枚举）
            llm: 语言模型实例
        """

    def process(self, sample: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        处理样本的抽象方法，子类必须实现

        Args:
            sample: 输入样本
            context: 额外上下文

        Returns:
            处理后的样本
        """
        raise NotImplementedError
```

### AgentType 枚举

```python
class AgentType(Enum):
    CLARIFIER = "clarifier"    # 模式锚定提取器
    REASONER = "reasoner"      # 初始推理器
    JUDGE = "judge"            # 最终评判器
    CRITIC = "critic"          # 导师智能体
    REFINER = "refiner"        # 执行者智能体
    VALIDATOR = "validator"    # 审计员智能体
    CURATOR = "curator"        # 档案管理员
    RETRIEVER = "retriever"    # 检索器
```

### MessageType 枚举

```python
class MessageType(Enum):
    REQUEST = "request"              # 请求
    RESPONSE = "response"            # 响应
    CRITIQUE = "critique"            # 批评
    FEEDBACK = "feedback"            # 反馈
    DISPUTE = "dispute"              # 分歧
    RESOLUTION = "resolution"        # 解决方案
    FINAL_JUDGMENT = "final_judgment" # 最终裁决
```

### AgentMessage 数据类

```python
@dataclass
class AgentMessage:
    sender: AgentType                # 发送者
    receiver: AgentType              # 接收者
    message_type: MessageType        # 消息类型
    content: Dict[str, Any]          # 消息内容
    timestamp: float = 0             # 时间戳
    message_id: str = ""             # 消息ID
```

---

## 各智能体详解

### 1. ClarifierAgent（模式锚定提取器）

**文件**：`agents/clarifier_agent.py`

**职责**：从表格中提取轻量化的关键词典作为 Schema 锚点

**提取信息**：
- 列名（Headers）
- 关键实体（Entities）
- 数值单位（Units）
- 关键词（Keywords）

**关键方法**：
```python
def clarify_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
    """处理单个样本，提取 schema 锚点"""

def clarify_batch(self, dataset: List[Dict]) -> List[Dict]:
    """批量处理数据集"""

def extract_headers(self, table_text: List[List[str]]) -> List[str]:
    """提取列名"""

def extract_entities(self, table_text: List[List[str]], question: str) -> Dict[str, List[str]]:
    """提取关键实体"""

def extract_units(self, table_text: List[List[str]]) -> Dict[str, str]:
    """提取数值单位"""
```

**输出格式**：
```python
{
    'headers': ['Name', 'Age', 'Score'],
    'entities': {'Person': ['Alice', 'Bob'], 'Location': ['NYC', 'LA']},
    'units': {'Score': 'points', 'Age': 'years'},
    'keywords': ['average', 'maximum', 'total']
}
```

---

### 2. InitialReasoner（初始推理器）

**文件**：`agents/reasoner_agent.py`

**职责**：执行初始推理链，生成第一版答案

**关键方法**：
```python
def reason(self, sample: Dict[str, Any], use_clarifier: bool = False) -> Dict[str, Any]:
    """
    执行初始推理

    Args:
        sample: 输入样本
        use_clarifier: 是否使用 clarifier 结果

    Returns:
        包含推理链和初步答案的样本
    """
```

**依赖**：
- `thought/TableQA/utils/chain.py` - 推理链执行
- `thought/TableQA/operations/` - 表格操作

---

### 3. JudgeAgent（最终评判器）

**文件**：`agents/judge_agent.py`

**职责**：判断答案正确性，作为最终仲裁者

**关键方法**：
```python
def judge_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
    """
    判断样本答案的正确性

    Returns:
        添加了 judge_result 和 conclusion 的样本
        conclusion: "[Correct]" or "[Incorrect]"
    """

def build_judge_prompt(
    self,
    sample: Dict[str, Any],
    include_validator_feedback: bool = False,
    include_dispute_context: bool = False
) -> str:
    """构建评判 prompt"""
```

**Prompt 模板**：`critic/TableQA/tools/instruction.py` 中的 `judge_instruction`

**输出格式**：
```python
{
    'judge_result': {
        'explanation': '详细解释',
        'conclusion': '[Correct]'  # or '[Incorrect]'
    },
    'conclusion': '[Correct]'
}
```

---

### 4. CriticAgent（导师智能体）

**文件**：`agents/critic_agent.py`

**职责**：基于记忆库检索 Blueprint，下达纠偏指令

**Prompt 策略**：
- **第一次**：只引入 Blueprint
- **第二次**：引入原文作为少样本学习

**关键方法**：
```python
def process(self, sample: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    处理样本并提供批评

    Args:
        sample: 输入样本
        context: 包含 error_route 的上下文

    Returns:
        添加了 critique 信息的样本
    """

def _build_critique_prompt(self, sample: Dict[str, Any], error_route: str) -> str:
    """构建批评 prompt"""

def _retrieve_blueprint(self, error_route: str) -> str:
    """从记忆库检索 blueprint"""
```

**输出格式**：
```python
{
    'critique': {
        'analysis': '逐步分析',
        'max_step': 3,  # 错误步骤编号
        'conclusion': 'Conclusion: [Incorrect] Step 3'
    }
}
```

---

### 5. RefinerAgent（执行者智能体）

**文件**：`agents/refiner_agent.py`

**职责**：基于 Critic 的反馈修正推理路径

**关键方法**：
```python
def refine(self, sample: Dict[str, Any], critique: Dict) -> Dict[str, Any]:
    """
    修正推理路径

    Args:
        sample: 原始样本
        critique: Critic 的反馈

    Returns:
        修正后的样本
    """

def _build_refine_prompt(self, sample: Dict, critique: Dict) -> str:
    """构建修正 prompt"""

def _execute_refinement(self, prompt: str) -> Dict:
    """执行修正操作"""
```

**修正策略**：
1. 定位错误步骤（基于 critique 的 max_step）
2. 重新执行该步骤及后续步骤
3. 生成新的最终答案

---

### 6. ValidatorAgent（审计员智能体）

**文件**：`agents/validator_agent.py`

**职责**：基于表格事实进行硬性审计，验证数值与逻辑

**关键方法**：
```python
def validate(self, sample: Dict[str, Any], clarifier_result: Dict) -> Dict[str, Any]:
    """
    验证答案的正确性

    Args:
        sample: 包含答案的样本
        clarifier_result: Clarifier 提取的 schema 锚点

    Returns:
        添加了验证结果的样本
    """

def _validate_numerical_calculation(self, sample: Dict) -> bool:
    """验证数值计算"""

def _validate_cell_reference(self, sample: Dict, clarifier: Dict) -> bool:
    """验证单元格引用"""

def _build_validation_prompt(self, sample: Dict, clarifier: Dict) -> str:
    """构建验证 prompt"""
```

**验证类型**：
- 数值计算审计
- 单元格定位审计
- 逻辑一致性校验

**输出格式**：
```python
{
    'validation': {
        'is_valid': True,
        'checks': {
            'numerical': True,
            'cell_reference': True,
            'logic': True
        },
        'feedback': '审计反馈'
    }
}
```

---

### 7. CuratorAgent（档案管理员）

**文件**：`agents/curator_agent.py`

**职责**：管理记忆库，生成 Blueprint，实现摘要化

**关键方法**：
```python
def process(self, sample: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    处理样本并更新记忆

    Args:
        sample: 包含错误信息的样本
        context: 包含 error_route

    Returns:
        添加了 curation 元数据的样本
    """

def _generate_blueprint(self, sample: Dict) -> str:
    """从错误案例生成 blueprint（错误模式摘要）"""

def _update_error_tree(self, error_route: str, blueprint: str, success: bool):
    """更新错误树"""

def _summarize_pattern(self, cases: List[Dict]) -> str:
    """将相似案例摘要化"""
```

**记忆结构**：
- 错误树（JSON）：`critic/TableQA/tools/few_shot_critic.json`
- 树节点：包含 `blueprint`、`confidence_score`、案例列表

---

### 8. RetrieverAgent（检索器）

**文件**：`agents/retriever_agent.py`

**职责**：从错误树中检索相关的 Blueprint 和 Few-shot 案例

**关键方法**：
```python
def retrieve(self, sample: Dict, error_route: str = None, k: int = 3) -> Dict[str, Any]:
    """
    检索相关蓝图和案例

    Args:
        sample: 当前样本
        error_route: 错误路由（可选）
        k: 检索数量

    Returns:
        包含 blueprint 和 few_shot_examples 的字典
    """

def _search_by_error_route(self, error_route: str) -> List[Dict]:
    """根据错误路由搜索"""

def _semantic_search(self, query: str, k: int) -> List[Dict]:
    """语义搜索（可选）"""
```

**输出格式**：
```python
{
    'blueprint': '模型倾向于忽略日期范围内的最后一行',
    'few_shot_examples': [
        {'question': '...', 'chain': '...', 'critique': '...'},
        ...
    ]
}
```

---

### 9. DisputeHandler（分歧处理器）

**文件**：`agents/dispute_handler.py`

**职责**：处理 Critic、Validator、Refiner 三方的分歧

**三次分歧处理机制**：

1. **第一次分歧**：Critic 带 Validator 建议重试
2. **第二次分歧**：加入少样本案例学习
3. **第三次分歧**：触发 Refiner 质疑操作，交 Judge 最终裁决

**关键方法**：
```python
def handle_dispute(
    self,
    sample: Dict,
    critic_opinion: Dict,
    validator_opinion: Dict,
    refiner_opinion: Dict,
    iteration: int
) -> Dict[str, Any]:
    """
    处理分歧

    Args:
        sample: 原始样本
        critic_opinion: Critic 的意见
        validator_opinion: Validator 的意见
        refiner_opinion: Refiner 的意见
        iteration: 当前迭代次数

    Returns:
        解决方案和下一步行动
    """

def _first_dispute_resolution(self, sample: Dict, critic: Dict, validator: Dict) -> Dict:
    """第一次分歧解决"""

def _second_dispute_resolution(self, sample: Dict, few_shot_examples: List) -> Dict:
    """第二次分歧解决"""

def _third_dispute_resolution(self, sample: Dict, refiner: Dict) -> Dict:
    """第三次分歧解决"""
```

**输出格式**：
```python
{
    'resolution': 'retry_with_validator_feedback',  # 或其他策略
    'next_action': 'REFINE_CHAIN',
    'context': {
        'validator_feedback': '...',
        'few_shot_examples': [...]
    }
}
```

---

## 关键依赖与配置

### 依赖项

```python
# 内部依赖
from thought.TableQA.utils.llm import LLM
from thought.TableQA.utils.helper import table2string
from critic.TableQA.tools.instruction import judge_instruction, critic_instruction
from critic.TableQA.tools.get_info import get_judge_few_shot, get_cot_for_judge

# 外部依赖
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import copy
```

### 配置文件

1. **错误树 JSON**：`critic/TableQA/tools/few_shot_critic.json`
2. **Prompt 模板**：`critic/TableQA/tools/instruction.py`
3. **Few-shot 案例**：动态从错误树加载

---

## 数据模型

### AgentState

```python
@dataclass
class AgentState:
    agent_type: AgentType              # 智能体类型
    current_sample: Dict[str, Any]     # 当前处理的样本
    iteration: int = 0                 # 迭代次数
    history: List[AgentMessage] = field(default_factory=list)  # 消息历史
    working_memory: Dict[str, Any] = field(default_factory=dict)  # 工作记忆
```

### ControllerState（跨模块使用）

```python
@dataclass
class ControllerState:
    sample: Dict[str, Any]             # 完整样本
    question: str                      # 问题
    chain: List[Dict]                  # 推理链
    conclusion: str                    # 结论
    iteration: int = 0                 # 迭代次数
    last_action: str = "INIT"          # 上一次动作
    error_route: Optional[str] = None  # 错误路由
    retrieved_blueprints: Optional[List[str]] = None  # 检索的蓝图
    diagnosis: Optional[Dict] = None   # 诊断结果
    action_history: List[str] = field(default_factory=list)  # 动作历史

    @property
    def is_correct(self) -> bool:
        return "[Correct]" in self.conclusion
```

---

## 测试与质量

### 当前状态

⚠️ **未发现系统化的测试文件**

### 建议的测试

1. **单元测试**（缺失）
   ```python
   # tests/test_agents.py
   def test_clarifier_agent():
       llm = MockLLM()
       clarifier = ClarifierAgent(llm=llm)
       sample = load_test_sample()
       result = clarifier.clarify_sample(sample)
       assert 'headers' in result['clarifier']
       assert 'entities' in result['clarifier']

   def test_judge_agent():
       llm = MockLLM()
       judge = JudgeAgent(llm=llm)
       sample = create_test_sample(answer='42')
       result = judge.judge_sample(sample)
       assert result['conclusion'] in ['[Correct]', '[Incorrect]']
   ```

2. **集成测试**（缺失）
   ```python
   # tests/test_agent_collaboration.py
   def test_critic_refiner_loop():
       """测试 Critic → Refiner 循环"""
       critic = CriticAgent(llm)
       refiner = RefinerAgent(llm)
       sample = create_erroneous_sample()

       critique = critic.process(sample)
       refined = refiner.refine(sample, critique)

       assert refined['conclusion'] == '[Correct]'
   ```

3. **通信协议测试**（缺失）
   ```python
   # tests/test_messaging.py
   def test_agent_message():
       msg = AgentMessage(
           sender=AgentType.CRITIC,
           receiver=AgentType.REFINER,
           message_type=MessageType.CRITIQUE,
           content={'error_step': 3}
       )
       assert msg.message_id != ""
   ```

---

## 常见问题 (FAQ)

### Q1: 如何添加新的智能体？

**A**：
1. 在 `agents/` 目录创建新文件，如 `new_agent.py`
2. 继承 `BaseAgent`：
   ```python
   from agents.multi_agent_framework import BaseAgent, AgentType

   class NewAgent(BaseAgent):
       def __init__(self, llm):
           super().__init__(AgentType.NEW_TYPE, llm)

       def process(self, sample, context=None):
           # 实现处理逻辑
           return updated_sample
   ```
3. 在 `AgentType` 枚举中添加新类型
4. 在 `agents/__init__.py` 中导出

### Q2: 智能体之间如何通信？

**A**：
- **直接调用**：在 Controller 中按顺序调用各智能体的 `process()` 方法
- **消息传递**：使用 `AgentMessage` 数据类，通过 `context` 参数传递
- **共享状态**：通过 `ControllerState` 的字段共享信息

### Q3: 如何修改智能体的 Prompt？

**A**：
1. 找到对应的 `instruction.py` 文件（如 `critic/TableQA/tools/instruction.py`）
2. 修改 prompt 变量（如 `critic_instruction`）
3. 确保输出格式保持一致（如 `[Correct]`/`[Incorrect]`）
4. 更新相应的解析逻辑（如 `_parse_judge_response`）

### Q4: Clarifier 的输出如何传递给后续阶段？

**A**：
1. **保存**：在 Thought 阶段保存到 `{thought_results_dir}/clarifier/case_dict_{id}.pkl`
2. **传递**：在 Refine 阶段通过 `use_clarifier=True` 参数加载
3. **使用**：Validator 和其他智能体通过 `context.get('clarifier_result')` 访问

### Q5: 如何调试智能体的决策过程？

**A**：
1. 在智能体的 `process()` 方法中添加 `print()` 语句
2. 使用 `DEBUG` 模式（如 `controller.py` 中的 `DEBUG = True`）
3. 检查 `AgentState.history` 中的消息历史
4. 使用 `pdb.set_trace()` 进行断点调试

---

## 相关文件清单

### 核心文件

- `agents/__init__.py` - 模块导出
- `agents/multi_agent_framework.py` - 框架基础类
- `agents/clarifier_agent.py` - Clarifier 实现
- `agents/reasoner_agent.py` - Reasoner 实现
- `agents/judge_agent.py` - Judge 实现
- `agents/critic_agent.py` - Critic 实现
- `agents/refiner_agent.py` - Refiner 实现
- `agents/validator_agent.py` - Validator 实现
- `agents/curator_agent.py` - Curator 实现
- `agents/retriever_agent.py` - Retriever 实现
- `agents/dispute_handler.py` - 分歧处理实现
- `agents/memory_integration.py` - 记忆集成
- `agents/active_forgetting.py` - 主动遗忘

### 依赖文件

- `thought/TableQA/utils/llm.py` - LLM 封装
- `critic/TableQA/tools/instruction.py` - Prompt 模板
- `critic/TableQA/tools/get_info.py` - 信息检索工具

### 配置文件

- `critic/TableQA/tools/few_shot_critic.json` - 错误树 JSON

---

**下一步建议**：

1. 为各智能体添加单元测试
2. 补充 `dispute_handler.py` 的详细文档
3. 建立 Prompt 版本管理机制
4. 优化智能体间的通信协议
