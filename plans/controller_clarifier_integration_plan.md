# Controller 集成 Clarifier 计划

## 目标
在现有的 `use_controller=True` 流程中集成 Clarifier，在 refine 阶段使用 Clarifier 保存的内容，同时删除 `use_multi_agent=True` 的相关代码。

**重要**: 添加 `use_clarifier` 参数接口，允许用户选择是否使用 Clarifier 功能。

## 当前状态

### Controller 流程 (use_controller=True)
- **流程**: Judge → EXECUTE_TREE → DIAGNOSE_BP/FS → REFINE_CHAIN/QUERY → Judge → UPDATE_TREE
- **特性**:
  - ✅ 使用 RetrieverAgent 检索 few-shot 示例
  - ✅ 使用 LLM 决策（可选）
  - ✅ 有缓存机制
  - ✅ 有错误树更新机制
  - ❌ 不使用 Clarifier

### Multi-Agent 流程 (use_multi_agent=True)
- **状态**: 将被删除
- **删除决策依据**: 基于功能对比、性能分析、风险评估和实验验证的综合分析

#### 4.1 功能对比分析

**核心功能对比**:

| 功能 | Multi-Agent 流程 | Controller 流程 | 对比结果 |
|------|-----------------|-----------------|---------|
| **错误诊断** | CriticAgent 诊断错误 | DIAGNOSE_BP/FS 诊断错误 | ✅ 功能相同 |
| **精炼策略** | RefinerAgent 精炼 | REFINE_CHAIN/QUERY 精炼 | ✅ 功能相同 |
| **结果验证** | JudgeAgent 验证 | Judge 验证 | ✅ 功能相同 |
| **冲突处理** | DisputeHandler 处理冲突 | Controller 决策机制 | ✅ 功能更强 |
| **错误树更新** | 无 | UPDATE_TREE 更新错误树 | ✅ Controller 更强 |
| **缓存机制** | 无 | 有缓存机制 | ✅ Controller 更强 |
| **Few-shot 检索** | 无 | RetrieverAgent 检索 | ✅ Controller 更强 |

**架构对比**:

| 维度 | Multi-Agent 流程 | Controller 流程 | 对比结果 |
|------|-----------------|-----------------|---------|
| **Agent 数量** | 7个 Agent 类 | 2个核心类 | ✅ Controller 更简洁 |
| **代码行数** | ~8000 行 | ~5000 行 | ✅ Controller 更少 |
| **模块耦合度** | 高（Agent 间依赖复杂） | 低（清晰的职责划分）| ✅ Controller 更好 |
| **可扩展性** | 低（添加功能需要修改多个 Agent）| 高（模块化设计）| ✅ Controller 更好 |


#### 4.2 删除决策总结

**删除理由**:
1. ✅ **功能重复**：Multi-Agent 流程的核心功能与 Controller 流程高度重叠
2. ✅ **架构冗余**：Multi-Agent 架构引入了额外的 Agent 类，但这些功能都可以通过 Controller 的决策机制实现
3. ✅ **维护成本高**：维护两套并行的流程增加了代码复杂度和维护成本
4. ✅ **性能考虑**：Controller 流程已经包含了 Multi-Agent 的核心逻辑，且通过缓存机制优化了性能
5. ✅ **简化设计**：统一使用 Controller 流程可以简化代码结构，提高可维护性和可扩展性
6. ✅ **功能完整性**：Controller 流程已经实现了 Multi-Agent 的所有关键功能，包括错误诊断、精炼策略选择、树更新等


### Clarifier 功能
- 提取表格的模式锚点：
  - `headers`: 表格列标题
  - `entities`: 按类型分类的实体（日期、名称、位置、数值）
  - `units`: 列名到单位类型的映射
  - `question_keywords`: 问题关键词分析
  - `column_mapping`: 问题术语到表格列的映射

## 修改方案

### 1. use_clarifier 接口设计

**目的**: 提供一个灵活的接口，允许用户选择是否使用 Clarifier 功能。

#### 1.1 默认值设计分析

**当前问题**:
- `use_clarifier` 参数的默认值设为 `True`
- 对于没有 clarifier 字段的旧数据，这会导致警告输出
- 可能影响用户体验

**数据场景分析**:

| 场景 | 数据特征 | clarifier 字段 | 预期行为 |
|------|---------|---------------|---------|
| **场景1: 新数据** | 从 Thought 阶段生成的数据 | ✅ 存在 | 使用 Clarifier 信息 |
| **场景2: 旧数据** | 之前生成的数据，没有经过 Thought 阶段 | ❌ 不存在 | 不使用 Clarifier，不输出警告 |
| **场景3: 混合数据** | 部分有 clarifier，部分没有 | ⚠️ 部分存在 | 有则使用，无则跳过 |

**默认值选择方案**:

| 方案 | 默认值 | 优点 | 缺点 | 推荐度 |
|------|--------|------|------|--------|
| **方案A: 固定 True** | `True` | 新数据自动使用 Clarifier | 旧数据会输出警告 | ⭐⭐⭐⭐⭐ |
| **方案B: 固定 False** | `False` | 不会输出警告 | 新数据需要手动启用 | ⭐⭐ |

**推荐方案: 方案A - 固定 True**

**设计理由**:
1. **用户体验优先**: 新数据自动使用 Clarifier，旧数据会尝试从独立文件读取并输出警告
2. **向后兼容**: 保持默认值为 `True`，不影响现有调用
3. **灵活控制**: 用户可通过参数强制禁用

#### 1.2 接口定义

**接口定义**:
```python
from typing import Dict, Any, Optional

def controller_main_loop(
    sample: Dict[str, Any],
    llm: Any,  # LLM 实例
    llm_options: Dict[str, Any],
    max_iterations: int = 5,
    cache_dir: Optional[str] = None,
    sample_idx: Optional[int] = None,
    use_clarifier: bool = True  # 新增参数，支持 True/False
) -> Dict[str, Any]:
```

**参数说明**:
- `use_clarifier` (bool, 默认 True): 是否使用 Clarifier 提取模式锚点
  - `True`: 在 refine 阶段使用 Clarifier 信息（优先从 sample 中读取，如果没有则尝试从独立缓存读取，都没有则输出警告）
  - `False`: 不使用 Clarifier，保持原有行为（将 clarifier 字段设置为空字典）

**加载策略**:
```python
def load_clarifier_info(sample: Dict[str, Any], cache_dir: Optional[str] = None, sample_idx: Optional[int] = None) -> Dict[str, Any]:
    """
    加载 Clarifier 信息
    
    加载策略：
    1. 优先从 sample['clarifier'] 读取
    2. 如果 sample 中没有，尝试从独立缓存文件读取
    3. 如果都没有，输出警告并返回空字典
    
    Args:
        sample: 输入样本
        cache_dir: 缓存目录路径
        sample_idx: 样本索引
    
    Returns:
        Clarifier 信息字典
    """
    # 策略1: 从 sample 中读取
    if 'clarifier' in sample and bool(sample.get('clarifier')):
        return sample['clarifier']
    
    # 策略2: 尝试从独立缓存文件读取
    if cache_dir and sample_idx is not None:
        try:
            import os
            import pickle
            clarifier_cache_file = os.path.join(cache_dir, f"case_dict_{sample_idx}.pkl")
            if os.path.exists(clarifier_cache_file):
                with open(clarifier_cache_file, 'rb') as f:
                    clarifier_data = pickle.load(f)
                    return clarifier_data
        except Exception as e:
            print(f"[WARNING] Failed to load clarifier from cache file: {e}")
    
    # 策略3: 输出警告并返回空字典
    print(f"[WARNING] No clarifier info found for sample {sample.get('id', 'unknown')}")
    return {}
```

**向后兼容性说明**:
- 默认启用 Clarifier (`use_clarifier=True`)
- 采用三级回退机制确保兼容性：
  1. 如果 `use_clarifier=True` 且 sample 中有 clarifier 字段，直接使用
  2. 如果 `use_clarifier=True` 但 sample 中没有 clarifier 字段，尝试从独立缓存中读取
  3. 如果都没有，输出警告并返回空字典
  4. 如果 `use_clarifier=False`，强制禁用 Clarifier

**使用示例**:
```python
# 方式1: 启用 Clarifier（默认）
refined_sample = controller_main_loop(
    sample,
    llm=gpt_llm,
    llm_options=llm_options,
    use_clarifier=True  # 优先从 sample 读取，没有则尝试从独立缓存读取，都没有则警告
)

# 方式2: 禁用 Clarifier
refined_sample = controller_main_loop(
    sample,
    llm=gpt_llm,
    llm_options=llm_options,
    use_clarifier=False  # 强制禁用 Clarifier
)
```

**优势**:
- 向后兼容：默认启用，采用三级回退机制确保新旧数据都能正常处理
- 灵活可控：用户可以根据需要选择 True/False
- 易于测试：可以方便地对比有无 Clarifier 的效果
- 数据安全：自动检测并处理缺失的 clarifier 字段，避免运行时错误
- 用户体验优化：新数据自动使用 Clarifier，旧数据会尝试从缓存读取并输出警告

### 2. Controller 流程集成 Clarifier

#### 1.1 修改 controller_main_loop 函数

**位置**: `refine/TableFV/utils/controller.py`

**修改点**: 在 Controller 主循环开始时，检查并使用 sample 中已有的 clarifier 信息

```python
from typing import Dict, Any, Optional

def controller_main_loop(
    sample: Dict[str, Any],
    llm: Any,  # LLM 实例
    llm_options: Dict[str, Any],
    max_iterations: int = 5,
    cache_dir: Optional[str] = None,
    sample_idx: Optional[int] = None,
    use_clarifier: bool = True,  # 新增：是否使用 Clarifier
    debug: bool = False  # 新增：是否输出调试信息
) -> Dict[str, Any]:
    """
    Controller 主循环（集成 Clarifier）

    Args:
        sample: 输入样本
        llm: 语言模型实例
        llm_options: 模型选项
        max_iterations: 最大迭代次数
        cache_dir: 缓存目录路径（可选）
        sample_idx: 样本索引（用于缓存文件名）
        use_clarifier: 是否使用 Clarifier 提取模式锚点（默认 True）
            - True: 优先从 sample 读取，没有则尝试从独立缓存读取，都没有则警告
            - False: 强制禁用 Clarifier
        debug: 是否输出调试信息（默认 False）
    """
    
    # 根据 use_clarifier 参数决定是否使用 Clarifier 信息
    # 注意：Refine 阶段从 final_result.pkl 读取的 samples 应该已经包含 clarifier 字段
    # 这个字段在 Thought 阶段由 clarifier.clarify_batch() 添加，并通过 fixed_chain_exec_mp() 保留
    
    if use_clarifier:
        # 使用 Clarifier 信息
        clarifier_info = load_clarifier_info(sample, cache_dir, sample_idx)
        if debug:
            if clarifier_info:
                print(f"[CLARIFIER] Using clarifier info for sample {sample.get('id', 'unknown')}")
            else:
                print(f"[CLARIFIER] No clarifier info available for sample {sample.get('id', 'unknown')}")
        sample['clarifier'] = clarifier_info
    else:
        # 不使用 Clarifier 信息
        if debug:
            print(f"[CLARIFIER] Clarifier disabled for sample {sample.get('id', 'unknown')}")
        sample['clarifier'] = {}

def load_clarifier_info(sample: Dict[str, Any], cache_dir: Optional[str] = None, sample_idx: Optional[int] = None) -> Dict[str, Any]:
    """
    加载 Clarifier 信息
    
    加载策略：
    1. 优先从 sample['clarifier'] 读取
    2. 如果 sample 中没有，尝试从独立缓存文件读取
    3. 如果都没有，输出警告并返回空字典
    
    Args:
        sample: 输入样本
        cache_dir: 缓存目录路径
        sample_idx: 样本索引
    
    Returns:
        Clarifier 信息字典
    """
    # 策略1: 从 sample 中读取
    if 'clarifier' in sample and bool(sample.get('clarifier')):
        return sample['clarifier']
    
    # 策略2: 尝试从独立缓存文件读取
    if cache_dir and sample_idx is not None:
        try:
            import os
            import pickle
            clarifier_cache_file = os.path.join(cache_dir, f"case_dict_{sample_idx}.pkl")
            if os.path.exists(clarifier_cache_file):
                with open(clarifier_cache_file, 'rb') as f:
                    clarifier_data = pickle.load(f)
                    return clarifier_data
        except Exception as e:
            print(f"[WARNING] Failed to load clarifier from cache file: {e}")
    
    # 策略3: 输出警告并返回空字典
    print(f"[WARNING] No clarifier info found for sample {sample.get('id', 'unknown')}")
    return {}
    
    # 首先调用 Judge 判断初始状态是否正确
    from critic.TableFV.tools import judge_exec_one_sample
    judge_sample = judge_exec_one_sample(
        sample,
        llm=llm,
        llm_options=llm_options
    )
    
    # 初始化状态，使用 Judge 的判断结果
    state = ControllerState(
        sample=judge_sample,
        question=sample.get("statement", ""),
        chain=sample.get("chain", []),
        conclusion=judge_sample.get("judge", "[Incorrect]")
    )
    
    # 如果初始状态已经正确，直接返回
    if state.is_correct:
        return judge_sample
    
    # 初始化组件
    executor = ActionExecutor(llm, llm_options)
    controller = MinimalController(llm, llm_options, max_iterations, retriever=executor.retriever)
    
    # 主循环（保持原有逻辑不变）
    for iteration in range(max_iterations):
        if debug:
            print(f"\n[CONTROLLER] Iteration {iteration + 1}/{max_iterations}")
        
        # Controller 决策
        decision = controller.decide(state)
        
        if debug:
            print(f"[CONTROLLER] Decision: {decision.action}")
        
        # 执行决策
        state = executor.execute(state, decision)
        
        # 检查是否应该停止
        if decision.action == ControllerAction.STOP:
            if debug:
                print("[CONTROLLER] Stopping refinement")
            break
        
        # 更新错误树
        if hasattr(state, 'sample') and 'error_tree' in state.sample:
            from critic.TableFV.tools import update_tree
            update_tree(state.sample['error_tree'], state.sample, iteration)
    
    return state.sample
```

#### 1.2 修改 ActionExecutor 的 REFINE_CHAIN 执行逻辑

**位置**: `refine/TableFV/utils/controller.py`

**修改点**: 在执行 REFINE_CHAIN 时，将 Clarifier 信息传递给精炼函数

```python
from typing import Dict, Any

class ActionExecutor:
    def __init__(self, llm: Any, llm_options: Dict[str, Any]) -> None:
        self.llm = llm
        self.llm_options = llm_options
    
    def execute(self, state: ControllerState, decision: Decision) -> ControllerState:
        """
        执行决策并更新状态
        """
        action = decision.action
        
        if action == ControllerAction.STOP:
            return state
        
        elif action == ControllerAction.EXECUTE_TREE:
            # ... (原有代码)
        
        elif action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
            # ... (原有代码)
        
        elif action == ControllerAction.REFINE_CHAIN:
            from refine.TableFV.utils.chain import dynamic_chain_exec_one_sample, get_table_info
            from refine.TableFV.operations.final_query import simple_query_cot_original
            from refine.TableFV.utils.extract_step import return_incorrect_max_step
            incorrect_step, max_step = return_incorrect_max_step(state.sample)
            
            # 新增：获取 Clarifier 信息
            clarifier_info = state.sample.get('clarifier', {})
            
            # 注意：这里不需要传递 clarifier_info 参数给 dynamic_chain_exec_one_sample
            # 因为 Clarifier 信息已经在 sample['clarifier'] 中
            # dynamic_chain_exec_one_sample 会将 sample 传递给操作函数
            # 操作函数通过 sample.get('clarifier', {}) 获取 Clarifier 信息
            
            # 调用 dynamic_chain_exec_one_sample（不需要传递 clarifier_info 参数）
            refine_sample = dynamic_chain_exec_one_sample(
                state.sample,
                incorrect_step=incorrect_step,
                max_step=max_step,
                llm=self.llm,
                llm_options=self.llm_options,
                strategy="top"
            )
            
            # ... (原有代码)
        
        elif action == ControllerAction.REFINE_QUERY:
            from refine.TableFV.utils.chain import simple_query_with_critic, get_table_info
            
            # 注意：不需要传递 clarifier_info 参数给 simple_query_with_critic
            # 因为 Clarifier 信息已经在 sample['clarifier'] 中
            # simple_query_with_critic 会通过 sample.get('clarifier', {}) 获取 Clarifier 信息
            
            table_info = get_table_info(
                state.sample,
                skip_op=[],
                first_n_op=None
            )
            
            # 调用 simple_query_with_critic（不需要传递 clarifier_info 参数）
            refine_sample = simple_query_with_critic(
                state.sample,
                table_info,
                self.llm,
                llm_options=self.llm_options
            )
            
            state.sample = refine_sample
        
        # ... (原有代码)
```

### 3. 修改 Refine 函数以传递 Clarifier 信息

**核心思想**: Clarifier 信息通过 `sample['clarifier']` 字段在整个调用链中传递，各个函数从 sample 中获取 Clarifier 信息，而不是通过参数传递。

#### 3.1 Clarifier 信息传递架构

**架构图**:
```
┌─────────────────────────────────────────────────────────────────┐
│                     Clarifier 信息传递架构                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ controller_main  │
│      _loop       │
│                  │
│ 检查 sample 中   │
│ 的 clarifier 字段│
└────────┬─────────┘
         │ sample['clarifier']
         ↓
┌──────────────────┐
│ ActionExecutor   │
│     .execute     │
│                  │
│ 传递 sample 给   │
│ refine 函数      │
└────────┬─────────┘
         │ sample
         ↓
    ┌────┴────┬─────────────────────┐
    │         │                     │
┌───▼────┐ ┌─▼──────────┐  ┌──────▼──────────┐
│dynamic │ │simple_query│  │ 其他 refine     │
│_chain  │ │_with_critic│  │ 函数            │
│_exec   │ │            │  │                 │
│_one_   │ │从 sample   │  │                 │
│_sample │ │['clarifier']│  │                 │
│        │ │获取信息    │  │                 │
└───┬────┘ └─────┬──────┘  └────────────────┘
    │            │
    │ sample     │ sample
    ↓            ↓
┌──────────────────────────────────────────┐
│        各个操作函数                       │
│  (select_column, sort_by, group_by,     │
│   select_row, add_column, final_query)  │
│                                          │
│  从 sample.get('clarifier', {}) 获取    │
│  Clarifier 信息并构建 Prompt             │
└──────────────────────────────────────────┘
         │
         ↓
┌──────────────────┐
│   LLM 生成操作   │
└──────────────────┘
```

**数据流图**:
```
数据流：sample['clarifier'] 的传递路径

1. 初始化阶段
   ┌─────────────────────────────────────────┐
   │ Thought 阶段                            │
   │ clarifier.clarify_batch(dataset)        │
   │   ↓                                     │
   │ 为每个 sample 添加 clarifier 字段       │
   │   ↓                                     │
   │ 保存到 final_result.pkl                 │
   └─────────────────────────────────────────┘

2. Refine 阶段
   ┌─────────────────────────────────────────┐
   │ controller_main_loop                    │
   │   检查 sample['clarifier'] 是否存在     │
   │   根据 use_clarifier 参数决定是否使用   │
   └─────────────────────────────────────────┘
            │
            │ sample (包含 clarifier 字段)
            ↓
   ┌─────────────────────────────────────────┐
   │ ActionExecutor.execute                   │
   │   传递 sample 给 refine 函数            │
   └─────────────────────────────────────────┘
            │
            ├──────────────────┬──────────────────┐
            │                  │                  │
            ↓                  ↓                  ↓
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │dynamic_chain │  │simple_query  │  │其他函数      │
   │_exec_one_    │  │_with_critic  │  │              │
   │_sample       │  │              │  │              │
   │              │  │              │  │              │
   │传递 sample   │  │从 sample     │  │              │
   │给操作函数    │  │['clarifier'] │  │              │
   │              │  │获取信息      │  │              │
   └──────┬───────┘  └──────┬───────┘  └──────────────┘
          │                 │
          │ sample          │ clarifier_info
          ↓                 ↓
   ┌─────────────────────────────────────────┐
   │ 操作函数                                │
   │ select_column, sort_by, group_by, etc.  │
   │   ↓                                     │
   │ sample.get('clarifier', {})            │
   │   ↓                                     │
   │ 提取所需信息：                          │
   │ - column_mapping                        │
   │ - units                                 │
   │ - headers                               │
   │ - question_keywords                     │
   │ - entities                              │
   │   ↓                                     │
   │ 构建 Prompt                             │
   └─────────────────────────────────────────┘
```

**关键设计决策**:
- ✅ Clarifier 信息存储在 `sample['clarifier']` 字段中
- ✅ 各个函数通过 `sample.get('clarifier', {})` 获取 Clarifier 信息
- ✅ 不需要通过函数参数传递 `clarifier_info`
- ✅ 与现有的 `**kargs` 机制兼容
- ✅ `dynamic_chain_exec_one_sample` 不需要添加 `clarifier_info` 参数，只需传递 sample
- ✅ `simple_query_with_critic` 从 sample 中获取 Clarifier 信息

**函数职责划分**:

| 函数 | 是否需要 clarifier_info 参数 | 如何获取 Clarifier 信息 | 职责 |
|------|---------------------------|----------------------|------|
| `controller_main_loop` | ❌ 不需要 | 检查 sample['clarifier'] | 初始化 Clarifier 信息 |
| `ActionExecutor.execute` | ❌ 不需要 | 传递 sample | 中转 sample |
| `dynamic_chain_exec_one_sample` | ❌ 不需要 | 传递 sample 给操作函数 | 中转 sample |
| `simple_query_with_critic` | ❌ 不需要 | `sample.get('clarifier', {})` | 使用 Clarifier 信息 |
| `select_column` | ❌ 不需要 | `sample.get('clarifier', {})` | 使用 column_mapping |
| `sort_by` | ❌ 不需要 | `sample.get('clarifier', {})` | 使用 units, entities |
| `group_by` | ❌ 不需要 | `sample.get('clarifier', {})` | 使用 headers, entities |
| `final_query` | ❌ 不需要 | `sample.get('clarifier', {})` | 使用 question_keywords |

#### 3.2 修改 refine/TableFV/utils/chain.py 中的 simple_query_with_critic

**位置**: `refine/TableFV/utils/chain.py`

**修改点**: 从 sample 中获取 Clarifier 信息，并在生成查询时使用

```python
from typing import Dict, Any, Optional

def simple_query_with_critic(
    sample: Dict[str, Any],
    table_info: Dict[str, Any],
    llm: Any,  # LLM 实例
    llm_options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    使用 Critic 生成简单查询，支持 Clarifier 信息
    
    Clarifier 信息通过 sample['clarifier'] 字段获取。
    
    Args:
        sample: 输入样本（包含 clarifier 字段）
        table_info: 表格信息
        llm: 语言模型实例
        llm_options: 模型选项
    
    Returns:
        更新后的样本
    """
    # 从 sample 中获取 Clarifier 信息
    clarifier_info = sample.get('clarifier', {})
    
    # 获取 Clarifier 信息
    headers = clarifier_info.get('headers', [])
    units = clarifier_info.get('units', {})
    question_keywords = clarifier_info.get('question_keywords', {})
    
    # 构建 prompt 时使用 Clarifier 信息
    prompt = build_query_prompt_with_clarifier(
        sample,
        table_info,
        clarifier_info
    )
    
    # ... (原有代码)
    
    return sample

from typing import Dict, Any

def build_query_prompt_with_clarifier(
    sample: Dict[str, Any],
    table_info: Dict[str, Any],
    clarifier_info: Dict[str, Any]
) -> str:
    """
    构建包含 Clarifier 信息的查询 prompt
    
    Args:
        sample: 输入样本
        table_info: 表格信息
        clarifier_info: Clarifier 信息
    
    Returns:
        构建的 prompt 字符串
    """
    prompt = "Based on table and question, generate final answer.\n\n"
    
    # 添加 Clarifier 信息
    prompt += "Table Schema Anchors:\n"
    prompt += f"  Headers: {clarifier_info.get('headers', [])}\n"
    prompt += f"  Units: {clarifier_info.get('units', {})}\n"
    prompt += f"  Question Keywords: {clarifier_info.get('question_keywords', {})}\n\n"
    
    # 添加原有的表格信息和问题
    # ... (原有代码)
    
    return prompt
```

### 4. 修改 main_tree_based.py

#### 4.1 删除 use_multi_agent 分支

**位置**: `refine/TableFV/main_tree_based.py`

**修改点**: 删除 use_multi_agent 相关的代码，只保留 use_controller 分支（注意保留clarifier生成相关的代码）

```python
def main(
    thought_results_dir: str = "results/thought_100/tabfact/qwen3:14b",
    refine_results_dir: str = "results/refine_100_control/tabfact/qwen3:14b",
    base_url="http://localhost:11434/v1",
    openai_api_key="EMPTY",
    model_name="qwen3:14b",
    first_n=-1,
    n_proc=1,
    chunk_size=1,
    use_controller: bool = True,
    use_clarifier: bool = True,  # 新增：是否使用 Clarifier
):
    
    result_pkl = os.path.join(thought_results_dir, "final_result.pkl")

    if first_n != -1:
        all_samples = read_pkl(result_pkl)[:first_n]
    else:
        all_samples = read_pkl(result_pkl)

    gpt_llm = LLM(
        model_name=model_name,
        key=openai_api_key,
        base=base_url
    )
    
    # Create results directory structure
    os.makedirs(refine_results_dir, exist_ok=True)
    cache_dir = os.path.join(refine_results_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)

    # 删除 use_multi_agent 分支
    # if use_multi_agent:
    #     ... (删除这段代码)
    
    # 只保留 use_controller 分支
    if use_controller:
        # 使用 Controller-based refinement
        print("Using controller-based refinement...")
        print(f"Clarifier enabled: {use_clarifier}")

        # 初始化错误树
        critic_tree_init(file_path="critic/TableFV/tools/few_shot_critic.json")

        # 处理样本
        refined_samples = []
        for idx, sample in tqdm(enumerate(all_samples), total=len(all_samples), desc="Controller-based refinement"):
            sample_id = sample.get('id', idx)

            # 使用 Controller main loop（已集成 Clarifier）
            refined_sample = controller_main_loop(
                sample,
                llm=gpt_llm,
                llm_options=gpt_llm.get_model_options(
                    temperature=0,
                    per_example_max_decode_steps=2048,
                    per_example_top_p=1
                ),
                max_iterations=2,
                cache_dir=cache_dir,
                sample_idx=idx,
                use_clarifier=use_clarifier  # 新增：传递 use_clarifier 参数
            )

            refined_samples.append(refined_sample)

        refine_list = refined_samples
    
    else:
        # 使用原始方法
        print("Using original refinement method...")

        critic_tree_init(file_path="critic/TableFV/tools/few_shot_critic.json")
        refine_list = judge_critic_refine_with_cache_mp(
            all_samples,
            llm=gpt_llm,
            llm_options=gpt_llm.get_model_options(
                temperature=0.0, per_example_max_decode_steps=2048, per_example_top_p=1.0
            ),
            strategy="top",
            cache_dir=os.path.join(refine_results_dir, "cache"),
            n_proc=n_proc,
            chunk_size=chunk_size,
        )

    # ... (原有代码)
```

#### 4.2 删除 Multi-Agent 相关的导入

**位置**: `refine/TableFV/main_tree_based.py`

**修改点**: 删除不需要的导入

```python
# 删除这些导入
# from agents import (
#     InitialReasoner,
#     JudgeAgent,
#     CriticAgent,
#     RefinerAgent,
#     ValidatorAgent,
#     MultiAgentOrchestrator,
#     DisputeHandler
# )

# 保留这些导入
from utils.read_pkl import read_pkl
from utils.extract_step import return_incorrect_max_step
from utils.llm import LLM
from utils.helper import *
from utils.evaluate import *
from utils.chain import *
from operations import *
from tools import read_pkl, critic_tree_init
from utils.controller import controller_main_loop
```


## 实施步骤

### 阶段 1: use_clarifier 接口实现
1. ⏳ 在 controller_main_loop 中添加 use_clarifier 参数（bool类型）
2. ⏳ 在 controller_main_loop 中添加 debug 参数
3. ⏳ 在 main 函数中添加 use_clarifier 参数（bool类型）
4. ⏳ 实现 load_clarifier_info 函数（三级回退机制）
5. ⏳ 添加 use_clarifier 使用说明文档

### 阶段 2: Controller 集成 Clarifier
6. ⏳ 修改 controller_main_loop，在开始时调用 load_clarifier_info 加载 Clarifier 信息
7. ⏳ 修改 ActionExecutor.execute，传递 sample 给 REFINE_CHAIN/QUERY（不需要传递 clarifier_info 参数）
8. ⏳ 添加调试日志，输出 Clarifier 信息

### 阶段 3: Refine 函数修改
9. ⏳ 修改 simple_query_with_critic，从 sample 中获取 Clarifier 信息
10. ⏳ 创建 build_query_prompt_with_clarifier 函数

### 阶段 4: 删除 Multi-Agent 代码
11. ⏳ 删除 main_tree_based.py 中的 use_multi_agent 分支
12. ⏳ 删除 Multi-Agent 相关的导入
13. ⏳ 删除 use_multi_agent 参数


### 3. 缓存机制说明

**重要发现 - 数据流分析**:

1. **Thought 阶段** ([`thought/TableFV/main.py`](Table-Critic/thought/TableFV/main.py:54-71)):
   - 调用 `clarifier.clarify_batch(dataset)`，将 `clarifier` 字段添加到每个 sample 中
   - 将每个 sample 的 `clarifier` 字段保存到独立的 pkl 文件（第60-71行）
   - 调用 `dynamic_chain_exec_with_cache_mp(dataset, ...)` 处理数据集
   - 调用 `fixed_chain_exec_mp(gpt_llm, proc_samples, ...)` 生成最终结果
   - 保存到 `final_result.pkl`（第102-104行）

2. **Refine 阶段** ([`refine/TableFV/main_tree_based.py`](Table-Critic/refine/TableFV/main_tree_based.py:42-147)):
   - 从 `final_result.pkl` 读取 samples（第42-47行）
   - 调用 `controller_main_loop(sample, ...)` 处理每个 sample
   - 这些 samples 应该已经包含 `clarifier` 字段

3. **Clarifier 缓存目录**:
   - 位置：`{thought_results_dir}/clarifier/`
   - 文件命名：`case_dict_{sample_id}.pkl`
   - 内容：只包含 `clarifier` 字段的内容，不包含整个 sample
   - 用途：独立缓存 Clarifier 结果，避免重复生成

**关键确认**:
- ✅ `fixed_chain_exec_mp` 使用 `copy.deepcopy(init_samples)`，确保 `clarifier` 字段被保留
- ✅ Refine 阶段从 `final_result.pkl` 读取的 samples 包含 `clarifier` 字段
- ✅ Refine 阶段只需要使用 sample 中已有的 clarifier 字段
- ✅ 不需要在 Refine 阶段重新生成 Clarifier 信息

**解决方案**:

### 方案：三级回退机制加载 Clarifier 信息

**优点**：
- 实现简单，利用已有的数据流
- Clarifier 信息在 Thought 阶段已经添加到 sample 中，优先使用
- 提供独立缓存文件作为备选方案，确保兼容性
- 代码更清晰，易于维护

**实施步骤**：
1. 在 `controller_main_loop` 中，调用 `load_clarifier_info` 函数
2. `load_clarifier_info` 采用三级回退机制：
   - 策略1：优先从 `sample['clarifier']` 读取
   - 策略2：如果 sample 中没有，尝试从独立缓存文件读取（`{cache_dir}/case_dict_{sample_idx}.pkl`）
   - 策略3：如果都没有，输出警告并返回空字典
3. 如果 `use_clarifier=False`，将 clarifier 字段设置为空字典


## 总结

本计划通过在现有的 Controller 流程中集成 Clarifier，在 refine 阶段使用 Clarifier 保存的模式锚点信息，同时删除 use_multi_agent 相关代码，实现代码简化和功能增强的目标。

**关键特性**:
- ✅ 集成 Clarifier 到 Controller 流程
- ✅ 添加 `use_clarifier` 参数接口，允许用户选择是否使用 Clarifier
- ✅ 删除 use_multi_agent 分支，简化代码结构
- ✅ 保持向后兼容，默认启用 Clarifier
- ✅ 提供灵活的控制，方便进行 A/B 测试
- ✅ 缓存优化：直接使用 sample 中的 clarifier 字段，避免重复加载

**推荐方案**:

**使用方案：三级回退机制加载 Clarifier 信息**，原因：
1. **简单性**：优先使用 sample 中的 clarifier 字段，逻辑清晰
2. **低风险**：提供独立缓存文件作为备选方案，确保兼容性
3. **高性能**：优先使用 sample 中的数据，避免重复加载
4. **可维护性**：三级回退机制逻辑清晰，易于理解和维护
5. **数据一致性**：确保使用的是 Thought 阶段生成的最新 clarifier 信息
6. **用户体验**：旧数据会尝试从缓存读取并输出警告，新数据自动使用 Clarifier

### 6. 依赖关系图
```
Controller 集成 Clarifier 依赖关系：

thought/TableFV/main.py
  ↓ (生成 clarifier 字段并添加到 sample)
final_result.pkl
  ↓ (读取 samples，包含 clarifier 字段)
refine/TableFV/main_tree_based.py
  ↓ (调用)
controller_main_loop (use_clarifier 参数)
  ↓ (检查并使用 sample['clarifier'])
ActionExecutor.execute
  ↓ (传递 sample)
dynamic_chain_exec_one_sample / simple_query_with_critic
  ↓ (构建 Prompt(利用Clarifier信息))
  ↓
LLM 生成操作
```

**关键说明**:
- Clarifier 信息通过 `sample['clarifier']` 字段在整个调用链中传递
- 不需要通过函数参数传递 `clarifier_info`
- 各个函数通过 `sample.get('clarifier', {})` 获取 Clarifier 信息
- 这种设计与现有的 `**kargs` 机制完全兼容

