# Refine 模块文档

[根目录](../CLAUDE.md) > **refine**

> 最后更新：2026-04-16 00:17:51

---

## 变更记录 (Changelog)

### 2026-04-16
- 初始化 refine 模块文档
- 建立 Controller 架构文档
- 识别多智能体协作流程

---

## 模块职责

Refine 模块是 Table-Critic 的**修正阶段**，通过 Controller 驱动的多智能体协作，对 Thought 阶段的错误答案进行迭代修正。

### 核心功能

1. **Controller 决策**：集中式决策中心，动态选择修正策略
2. **多智能体协作**：Critic、Refiner、Validator 等智能体协同工作
3. **分歧处理**：三次分歧处理机制，逐步升级争议解决策略
4. **记忆检索**：Retriever 从错误树检索相关 Blueprint 和案例
5. **约束感知**（可选）：基于约束的推理链优化

---

## 入口与启动

### TableQA 任务入口

**文件**：`refine/TableQA/main_tree_based.py`

```bash
python refine/TableQA/main_tree_based.py \
  --thought_results_dir results/new/thought/wikitq \
  --refine_results_dir results/new/refine/wikitq/qwen3:32b \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --n_proc 1 \
  --chunk_size 1 \
  --use_controller True \
  --use_clarifier True
```

**参数说明**：
- `--thought_results_dir`：Thought 阶段结果目录
- `--refine_results_dir`：Refine 阶段结果输出目录
- `--use_controller`：是否启用 Controller（True = 新架构，False = 原始架构）
- `--use_clarifier`：是否使用 Clarifier 结果

### TableFV 任务入口

**文件**：`refine/TableFV/main_tree_based.py`

```bash
python refine/TableFV/main_tree_based.py \
  --thought_results_dir results/new/thought/tabfact \
  --refine_results_dir results/new/refine/tabfact/qwen3:32b \
  --base_url https://api.example.com/v1 \
  --openai_api_key YOUR_KEY \
  --model_name qwen3:32b \
  --first_n -1 \
  --n_proc 8 \
  --chunk_size 4 \
  --use_controller True \
  --use_clarifier True
```

---

## Controller 架构

### Controller 核心组件

**文件**：`refine/TableQA/utils/controller.py`

#### 1. ControllerState（状态管理）

```python
@dataclass
class ControllerState:
    """Controller 状态管理类"""
    # 从现有 sample 提取
    sample: Dict[str, Any]
    question: str
    chain: List[Dict]
    conclusion: str  # "[Correct]" or "[Incorrect]"

    # Controller 管理的状态
    iteration: int = 0
    last_action: str = "INIT"
    error_route: Optional[str] = None
    retrieved_blueprints: Optional[List[str]] = None
    retrieval_info: str = ""
    retrieved_few_shot_examples: Optional[List[Any]] = None
    diagnosis: Optional[Dict] = None

    # 历史摘要
    action_history: List[str] = field(default_factory=list)

    @property
    def is_correct(self) -> bool:
        """判断当前状态是否正确"""
        return "[Correct]" in self.conclusion
```

#### 2. ControllerAction（动作空间）

```python
class ControllerAction(Enum):
    """简化动作空间（与现有流程对应）"""
    STOP = "STOP"                      # 停止
    EXECUTE_TREE = "EXECUTE_TREE"      # 执行错误树
    DIAGNOSE_BP = "DIAGNOSE_BP"        # 诊断（Blueprint 模式）
    DIAGNOSE_FS = "DIAGNOSE_FS"        # 诊断（Few-shot 模式）
    REFINE_CHAIN = "REFINE_CHAIN"      # 精炼推理链
    REFINE_QUERY = "REFINE_QUERY"      # 精炼最终查询
    UPDATE_TREE = "UPDATE_TREE"        # 更新错误树
```

#### 3. Decision（决策结果）

```python
@dataclass
class Decision:
    """决策结果"""
    action: ControllerAction
    reason: str
    confidence: float
    source: str  # "rule" | "llm"
```

#### 4. MinimalController（决策逻辑）

```python
class MinimalController:
    """最小 Controller"""

    def __init__(self, llm, llm_options, max_iterations: int = 2, retriever=None):
        """
        初始化 Controller

        Args:
            llm: 语言模型实例
            llm_options: LLM 调用选项
            max_iterations: 最大迭代次数
            retriever: RetrieverAgent 实例
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.llm_options = llm_options
        self.retriever = retriever

    def decide(self, state: ControllerState) -> Decision:
        """
        基于当前状态决定下一步动作

        决策逻辑：
        1. 规则层：如果正确，停止
        2. 规则层：达到最大迭代次数，停止
        3. LLM 层：决定下一步动作
        """
        # 规则 1: 如果正确，停止
        if state.is_correct:
            return Decision(
                action=ControllerAction.STOP,
                reason="答案正确",
                confidence=1.0,
                source="rule"
            )

        # 规则 2: 达到最大迭代次数，停止
        if state.iteration >= self.max_iterations:
            return Decision(
                action=ControllerAction.STOP,
                reason=f"达到最大迭代次数 ({self.max_iterations})",
                confidence=1.0,
                source="rule"
            )

        # LLM 层：决定下一步动作
        return self._llm_decide(state)

    def _llm_decide(self, state: ControllerState) -> Decision:
        """使用 LLM 决定下一步动作"""
        # 构建 prompt
        prompt = self._build_decision_prompt(state)

        # 调用 LLM
        response = self.llm.generate(prompt, options=self.llm_options)

        # 解析响应
        return self._parse_decision_response(response)
```

---

## Controller 主循环

### controller_main_loop 函数

**文件**：`refine/TableQA/utils/controller.py`

```python
def controller_main_loop(
    sample: Dict[str, Any],
    llm: LLM,
    llm_options: Dict,
    max_iterations: int = 2,
    cache_dir: str = None,
    sample_idx: int = 0,
    use_clarifier: bool = True,
    thought_results_dir: str = None,
) -> Dict[str, Any]:
    """
    Controller 主循环

    Args:
        sample: 输入样本
        llm: LLM 实例
        llm_options: LLM 调用选项
        max_iterations: 最大迭代次数
        cache_dir: 缓存目录
        sample_idx: 样本索引
        use_clarifier: 是否使用 Clarifier
        thought_results_dir: Thought 结果目录

    Returns:
        修正后的样本
    """
    # 初始化状态
    state = ControllerState(
        sample=sample,
        question=sample['question'],
        chain=sample.get('chain', []),
        conclusion=sample.get('conclusion', '[Incorrect]')
    )

    # 加载 Clarifier 结果
    if use_clarifier and thought_results_dir:
        clarifier_path = os.path.join(
            thought_results_dir,
            "clarifier",
            f'case_dict_{sample.get("id", sample_idx)}.pkl'
        )
        if os.path.exists(clarifier_path):
            with open(clarifier_path, 'rb') as f:
                state.sample['clarifier'] = pickle.load(f)

    # 初始化 Controller
    retriever = RetrieverAgent(llm=llm)
    controller = MinimalController(llm, llm_options, max_iterations, retriever)

    # 主循环
    while state.iteration < max_iterations:
        # 决策
        decision = controller.decide(state)

        if DEBUG:
            print(f"\n[Iteration {state.iteration}]")
            print(f"  Decision: {decision.action.value}")
            print(f"  Reason: {decision.reason}")
            print(f"  Confidence: {decision.confidence}")

        # 执行动作
        state = execute_action(state, decision, llm, llm_options, cache_dir)

        # 检查是否停止
        if decision.action == ControllerAction.STOP:
            break

        state.iteration += 1

    return state.sample
```

---

## 动作执行器

### execute_action 函数

```python
def execute_action(
    state: ControllerState,
    decision: Decision,
    llm: LLM,
    llm_options: Dict,
    cache_dir: str = None
) -> ControllerState:
    """
    执行 Controller 决策的动作

    Args:
        state: 当前状态
        decision: 决策结果
        llm: LLM 实例
        llm_options: LLM 选项
        cache_dir: 缓存目录

    Returns:
        更新后的状态
    """
    action = decision.action

    if action == ControllerAction.STOP:
        return state

    elif action == ControllerAction.EXECUTE_TREE:
        # 执行错误树，获取 error_route
        state.error_route = tree_exec_one_sample(state.sample, llm, llm_options)
        state.last_action = "EXECUTE_TREE"

    elif action == ControllerAction.DIAGNOSE_BP:
        # 使用 Blueprint 模式诊断
        state.retrieved_blueprints = state.retriever.retrieve(
            state.sample,
            error_route=state.error_route,
            k=3
        )['blueprint']
        state.diagnosis = criticize_with_blueprint(state.sample, state.retrieved_blueprints, llm)
        state.last_action = "DIAGNOSE_BP"

    elif action == ControllerAction.DIAGNOSE_FS:
        # 使用 Few-shot 模式诊断
        state.retrieved_few_shot_examples = state.retriever.retrieve(
            state.sample,
            error_route=state.error_route,
            k=3
        )['few_shot_examples']
        state.diagnosis = criticize_with_few_shot(state.sample, state.retrieved_few_shot_examples, llm)
        state.last_action = "DIAGNOSE_FS"

    elif action == ControllerAction.REFINE_CHAIN:
        # 精炼推理链
        state.chain = refine_chain(state.sample, state.diagnosis, llm, llm_options, cache_dir)
        state.last_action = "REFINE_CHAIN"

    elif action == ControllerAction.REFINE_QUERY:
        # 精炼最终查询
        state.sample['pred_answer'] = refine_query(state.sample, state.chain, llm, llm_options, cache_dir)
        state.last_action = "REFINE_QUERY"

    elif action == ControllerAction.UPDATE_TREE:
        # 更新错误树
        update_tree(state.sample, state.error_route, success=state.is_correct)
        state.last_action = "UPDATE_TREE"

    # 记录动作历史
    state.action_history.append(state.last_action)

    return state
```

---

## 多智能体协作流程

### 标准流程（新架构）

```
┌─────────────────────────────────────────────────────────────┐
│                    初始状态（来自 Thought）                   │
│  - chain: 推理链                                             │
│  - pred_answer: 预测答案                                     │
│  - conclusion: "[Incorrect]"                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Judge：初始评判（检查是否正确）                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (如果不正确)
┌─────────────────────────────────────────────────────────────┐
│          EXECUTE_TREE：执行错误树，获取 error_route           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         Controller 决策：DIAGNOSE_BP 或 DIAGNOSE_FS           │
└─────────────────────────────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  DIAGNOSE_BP         │    │  DIAGNOSE_FS         │
│  (Blueprint 模式)    │    │  (Few-shot 模式)     │
│  - Retriever 检索    │    │  - Retriever 检索    │
│  - Critic 诊断       │    │  - Critic 诊断       │
└──────────────────────┘    └──────────────────────┘
            │                           │
            └─────────────┬─────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            REFINE_CHAIN：Refiner 精炼推理链                   │
│            - 基于 Critic 的诊断                              │
│            - 重新执行错误的步骤                              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            REFINE_QUERY：生成新的最终答案                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Judge：再次评判                                   │
│            - 如果正确 → UPDATE_TREE → 结束                   │
│            - 如果不正确 → 继续下一轮                         │
└─────────────────────────────────────────────────────────────┘
```

### 三次分歧处理机制

**文件**：`agents/dispute_handler.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    第一次分歧处理                            │
│  Critic vs Validator                                        │
│  - Critic: 认为步骤 3 错误                                   │
│  - Validator: 认为数值计算正确                               │
│  → 解决：Critic 带 Validator 的建议重试                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (如果仍不正确)
┌─────────────────────────────────────────────────────────────┐
│                    第二次分歧处理                            │
│  引入 Few-shot 学习                                          │
│  - 检索相似的错误案例                                        │
│  - Critic 提供更详细的指导                                   │
│  → 解决：Refiner 基于案例重试                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (如果仍不正确)
┌─────────────────────────────────────────────────────────────┐
│                    第三次分歧处理                            │
│  Refiner 质疑操作                                            │
│  - Refiner: 认为问题本身无解或描述不清                       │
│  → 交 Judge 最终裁决                                        │
│  - 标记为"无法修正"                                         │
│  → 结束                                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 关键依赖与配置

### 依赖项

```python
# 内部依赖
from agents import (
    JudgeAgent,
    CriticAgent,
    RefinerAgent,
    ValidatorAgent,
    RetrieverAgent,
    DisputeHandler
)
from critic.TableQA.tools import tree_exec_one_sample, update_tree
from thought.TableQA.utils.llm import LLM
from thought.TableQA.utils.chain import refine_chain, refine_query

# 外部依赖
import pickle
import os
from tqdm import tqdm
from typing import Dict, List, Any, Optional
```

### 配置文件

1. **错误树 JSON**：`critic/TableQA/tools/few_shot_critic.json`
2. **Prompt 模板**：`critic/TableQA/tools/instruction.py`
3. **Clarifier 结果**：`{thought_results_dir}/clarifier/case_dict_{id}.pkl`

---

## 数据流与处理流程

### 输入格式

```python
{
    'id': 'sample_001',
    'table': [...],
    'question': '...',
    'chain': [...],              # 来自 Thought 阶段
    'pred_answer': '87.5',       # 来自 Thought 阶段
    'clarifier': {...}           # 如果启用 Clarifier
}
```

### 输出格式

```python
{
    'id': 'sample_001',
    'table': [...],
    'question': '...',
    'chain': [...],              # 修正后的推理链
    'pred_answer': '90.0',       # 修正后的答案
    'clarifier': {...},
    'refine_history': [          # 修正历史
        {
            'iteration': 0,
            'error_route': 'select_row/condition_error',
            'diagnosis': '...',
            'action': 'REFINE_CHAIN',
            'conclusion': '[Incorrect]'
        },
        {
            'iteration': 1,
            'error_route': 'final_query/calculation_error',
            'diagnosis': '...',
            'action': 'REFINE_QUERY',
            'conclusion': '[Correct]'
        }
    ]
}
```

---

## 测试与质量

### 当前状态

⚠️ **未发现系统化的测试文件**

### 建议的测试

1. **Controller 决策测试**
   ```python
   # tests/test_controller.py
   def test_controller_stop_on_correct():
       state = ControllerState(
           sample=...,
           question='...',
           chain=[...],
           conclusion='[Correct]'
       )
       controller = MinimalController(llm, llm_options)
       decision = controller.decide(state)
       assert decision.action == ControllerAction.STOP

   def test_controller_max_iterations():
       state = ControllerState(
           sample=...,
           question='...',
           chain=[...],
           conclusion='[Incorrect]',
           iteration=2  # 达到最大迭代次数
       )
       controller = MinimalController(llm, llm_options, max_iterations=2)
       decision = controller.decide(state)
       assert decision.action == ControllerAction.STOP
   ```

2. **集成测试**
   ```python
   # tests/test_refine_pipeline.py
   def test_refine_pipeline():
       # 创建一个错误的样本
       sample = create_erroneous_sample()

       # 运行 Refine 流程
       refined_sample = controller_main_loop(
           sample,
           llm=llm,
           llm_options=llm_options,
           max_iterations=2
       )

       # 验证修正结果
       assert refined_sample['conclusion'] == '[Correct]'
   ```

---

## 常见问题 (FAQ)

### Q1: Controller 与原始流程的区别？

**A**：
- **原始流程**：固定流程（Judge → Tree → Critic → Refine → Judge）
- **Controller 流程**：动态决策，根据当前状态选择下一步动作
- **优势**：更灵活，可以跳过不必要的步骤，提高效率

### Q2: 如何启用/禁用 Controller？

**A**：
在 `run_QA.sh` 或 `run_FV.sh` 中设置：
```bash
use_controller=True   # 启用 Controller（新架构）
use_controller=False  # 禁用 Controller（原始架构）
```

### Q3: Clarifier 的结果如何传递给 Refine 阶段？

**A**：
```python
# 在 main_tree_based.py 中
if use_clarifier and thought_results_dir:
    clarifier_path = os.path.join(
        thought_results_dir,
        "clarifier",
        f'case_dict_{sample.get("id", sample_idx)}.pkl'
    )
    if os.path.exists(clarifier_path):
        with open(clarifier_path, 'rb') as f:
            sample['clarifier'] = pickle.load(f)
```

### Q4: 如何调试 Controller 的决策过程？

**A**：
1. 在 `controller.py` 中设置 `DEBUG = True`
2. 查看控制台输出的决策日志
3. 检查 `action_history` 字段
4. 使用 `pdb.set_trace()` 进行断点调试

### Q5: 三次分歧处理机制是如何实现的？

**A**：
见 `agents/dispute_handler.py`：
- **第一次分歧**：`handle_first_dispute()`
- **第二次分歧**：`handle_second_dispute()`
- **第三次分歧**：`handle_third_dispute()`

---

## 相关文件清单

### TableQA 任务

- `refine/TableQA/main_tree_based.py` - 入口文件
- `refine/TableQA/main_constraint_based.py` - 约束感知版本
- `refine/TableQA/utils/controller.py` - Controller 实现
- `refine/TableQA/utils/constraint_aware_chain.py` - 约束感知链
- `refine/TableQA/utils/constraint_induction.py` - 约束归纳
- `refine/TableQA/utils/constraint_state.py` - 约束状态管理
- `refine/TableQA/operations/` - 操作定义
- `refine/TableQA/utils/chain.py` - 链执行

### TableFV 任务

- `refine/TableFV/main_tree_based.py` - 入口文件
- `refine/TableFV/utils/controller.py` - Controller 实现
- `refine/TableFV/operations/` - 操作定义
- `refine/TableFV/utils/chain.py` - 链执行

---

**下一步建议**：

1. 补充 Controller 的 LLM 决策 prompt 文档
2. 建立约束感知链的详细文档
3. 优化分歧处理逻辑
4. 添加更多测试用例
