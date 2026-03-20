Controller 设计分析与优化建议（考虑现有代码兼容性）

一、当前设计合理性分析

✅ 设计优点

1. 状态驱动决策：从被动判断转向主动策略选择
2. 双层决策机制：规则层保证稳定性，LLM层处理复杂情况
3. 结构化输出：decision 包含 action、use_memory、reason、confidence
4. 动作空间定义：覆盖主要场景（STOP、RETRIEVE、DIAGNOSE、REFINE、RETRY）
  
⚠️ 设计问题（结合现有代码）

1. 与现有流程不兼容
  - 现有代码使用固定流程：judge → tree → critic → refine → judge
  - Controller 的动态决策会破坏这个流程
  - 需要大量修改现有代码
    
2. 状态映射不清晰
  - Controller 的 state.thought 对应现有代码的 chain
  - Controller 的 state.error_signal 对应现有代码的 conclusion（[Correct]/[Incorrect]）
  - 但现有代码没有显式的 confidence 字段
    
3. 动作执行器缺失
  - Controller 定义了动作空间，但没有统一的执行器
  - 现有代码中每个动作都是独立的函数调用
  - 需要封装 Retriever、Diagnoser、Refiner 的调用
    
4. Retriever 未独立实现
  - 检索功能集成在 CriticAgent 中
  - 需要提取为独立的 RetrieverAgent
    

---

二、优化设计步骤（渐进式迁移）

阶段 1：最小可行 Controller（与现有代码兼容）

目标：在不修改现有流程的前提下，添加 Controller 层
初始 Judge
    ↓
EXECUTE_TREE (获取 error_route)
    ↓
LLM 决定 → DIAGNOSE_BP 或 DIAGNOSE_FS
    ↓
LLM 决定 → REFINE_CHAIN 或 REFINE_QUERY
    ↓
Judge 检查
    ↓
如果正确 → UPDATE_TREE → 返回
否则 → 继续循环

# 1. 定义 ControllerState（兼容现有数据结构）
@dataclass
class ControllerState:
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
    diagnosis: Optional[Dict] = None
    
    # 历史摘要
    action_history: List[str] = field(default_factory=list)
    
    @property
    def is_correct(self) -> bool:
        return "[Correct]" in self.conclusion

# 2. 定义简化动作空间（与现有流程对应）
class ControllerAction(Enum):
    STOP = "stop"           # 停止（对应现有流程的结束）
    EXECUTE_TREE = "tree"   # 执行 tree_exec_one_sample
    DIAGNOSE_BP = "diagnose_bp"  # 诊断（blueprint 模式）
    DIAGNOSE_FS = "diagnose_fs"  # 诊断（few-shot 模式）
    REFINE_CHAIN = "refine_chain"  # 精炼推理链
    REFINE_QUERY = "refine_query"   # 精炼最终查询
    UPDATE_TREE = "update_tree"  # 更新错误树

# 3. 定义 Decision
@dataclass
class Decision:
    action: ControllerAction
    reason: str
    confidence: float
    source: str  # "rule" | "llm"

# 4. 实现最小 Controller（包装现有流程）
class MinimalController:
    def __init__(self, llm):
        self.llm = llm
        self.max_iterations = 2  # 与现有代码一致
    
    def decide(self, state: ControllerState) -> Decision:
        """基于当前状态决定下一步动作"""
        
        # 规则层：如果正确，停止
        if state.is_correct:
            return Decision(
                action=ControllerAction.STOP,
                reason="Already correct",
                confidence=1.0,
                source="rule"
            )
        
        # 规则层：达到最大迭代次数，停止
        if state.iteration >= self.max_iterations:
            return Decision(
                action=ControllerAction.STOP,
                reason=f"Max iterations ({self.max_iterations}) reached",
                confidence=0.8,
                source="rule"
            )
        
        # LLM 层：决定下一步动作
        return self._llm_decide(state)
    
    def _llm_decide(self, state: ControllerState) -> Decision:
        """使用 LLM 决策（简化版）"""
        prompt = f"""Current state:
- Iteration: {state.iteration}
- Last action: {state.last_action}
- Has error_route: {state.error_route is not None}
- Has diagnosis: {state.diagnosis is not None}

Decide next action from:
- EXECUTE_TREE: Run tree_exec_one_sample to get error_route
- DIAGNOSE_BP: Run critic_exec_one_sample with blueprint_only=True
- DIAGNOSE_FS: Run critic_exec_one_sample with blueprint_only=False
- REFINE_CHAIN: Run dynamic_chain_exec_one_sample to refine reasoning chain
- REFINE_QUERY: Run simple_query_with_critic to refine final query
- UPDATE_TREE: Update error tree with successful case
- STOP: Stop iteration

Output JSON: {{"action": "...", "reason": "...", "confidence": 0.0-1.0}"""
        
        try:
            response = self.llm.generate(
                prompt,
                options=self.llm.get_model_options(
                    temperature=0.0,
                    max_tokens=100
                )
            )
            decision_data = json.loads(response)
            
            return Decision(
                action=ControllerAction(decision_data["action"]),
                reason=decision_data.get("reason", ""),
                confidence=decision_data.get("confidence", 0.5),
                source="llm"
            )
        except Exception as e:
            # Fallback: 使用默认流程
            print(f"LLM decision failed: {e}, using default flow")
            return self._default_decision(state)
    
    def _default_decision(self, state: ControllerState) -> Decision:
        """默认决策（模拟现有流程）"""
        if state.iteration == 0:
            return Decision(
                action=ControllerAction.EXECUTE_TREE,
                reason="First iteration: execute tree to get error_route",
                confidence=0.9,
                source="rule"
            )
        elif state.iteration == 1:
            if state.last_action == ControllerAction.EXECUTE_TREE:
                return Decision(
                    action=ControllerAction.DIAGNOSE_BP,
                    reason="Second iteration: diagnose with blueprint",
                    confidence=0.9,
                    source="rule"
                )
            elif state.last_action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
                # 根据 incorrect_step 决定 refine 类型
                incorrect_step, max_step = return_incorrect_max_step(state.sample)
                if incorrect_step and incorrect_step != max_step:
                    return Decision(
                        action=ControllerAction.REFINE_CHAIN,
                        reason="Refine reasoning chain",
                        confidence=0.9,
                        source="rule"
                    )
                else:
                    return Decision(
                        action=ControllerAction.REFINE_QUERY,
                        reason="Refine final query",
                        confidence=0.9,
                        source="rule"
                    )
        return Decision(
            action=ControllerAction.STOP,
            reason="No more actions available",
            confidence=0.5,
            source="rule"
        )

# 5. 动作执行器（包装现有函数）
class ActionExecutor:
    def __init__(self, llm, llm_options):
        self.llm = llm
        self.llm_options = llm_options
    
    def execute(self, state: ControllerState, decision: Decision) -> ControllerState:
        """执行决策并更新状态"""
        action = decision.action
        
        if action == ControllerAction.STOP:
            return state
        
        elif action == ControllerAction.EXECUTE_TREE:
            from tools import tree_exec_one_sample
            tree_sample = tree_exec_one_sample(
                state.sample, 
                llm=self.llm, 
                llm_options=self.llm_options
            )
            routes = re.findall(r'\((.*?)\)', tree_sample['tree'])
            state.error_route = routes[0] if routes else "random"
            state.sample = tree_sample
        
        elif action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
            from tools import critic_exec_one_sample
            blueprint_only = (action == ControllerAction.DIAGNOSE_BP)
            critic_sample = critic_exec_one_sample(
                state.sample,
                state.error_route or "random",
                llm=self.llm,
                llm_options=self.llm_options,
                blueprint_only=blueprint_only
            )
            state.diagnosis = {
                "critique": critic_sample.get("critique", ""),
                "conclusion": critic_sample.get("conclusion", ""),
                "max_step": critic_sample.get("max_step", 0)
            }
            state.sample = critic_sample
        
        elif action == ControllerAction.REFINE_CHAIN:
            from utils.chain import dynamic_chain_exec_one_sample
            incorrect_step = state.diagnosis.get("max_step", 0) if state.diagnosis else 0
            max_step = state.diagnosis.get("max_step", 0) if state.diagnosis else 0
            refine_sample = dynamic_chain_exec_one_sample(
                state.sample,
                incorrect_step=incorrect_step,
                max_step=max_step,
                llm=self.llm,
                llm_options=self.llm_options,
                strategy="top"
            )
            state.sample = refine_sample
        
        elif action == ControllerAction.REFINE_QUERY:
            from utils.chain import simple_query_with_critic, get_table_info
            table_info = get_table_info(
                state.sample,
                skip_op=[],
                first_n_op=None
            )
            refine_sample = simple_query_with_critic(
                state.sample,
                table_info,
                self.llm,
                llm_options=self.llm_options
            )
            state.sample = refine_sample
        
        elif action == ControllerAction.UPDATE_TREE:
            from tools import update_error_tree
            update_error_tree(
                state.sample,
                state.error_route or "random",
                error_tree_json="critic/TableFV/tools/few_shot_critic.json",
                llm=self.llm,
                llm_options=self.llm_options,
                lock=None
            )
        
        # 更新状态
        state.iteration += 1
        state.last_action = action.value
        state.action_history.append(action.value)
        
        # 更新 conclusion
        state.conclusion = state.sample.get("conclusion", "[Incorrect]")
        
        return state

# 6. 主循环（与现有代码兼容）
def controller_main_loop(
    sample: Dict[str, Any],
    llm,
    llm_options,
    max_iterations: int = 2
) -> Dict[str, Any]:
    """Controller 主循环（兼容现有代码）"""
    
    # 初始化状态
    state = ControllerState(
        sample=sample,
        question=sample.get("statement", ""),
        chain=sample.get("chain", []),
        conclusion=sample.get("conclusion", "[Incorrect]")
    )
    
    # 初始化组件
    controller = MinimalController(llm)
    executor = ActionExecutor(llm, llm_options)
    
    # 主循环
    for _ in range(max_iterations + 1):  # +1 for initial judge
        # 决策
        decision = controller.decide(state)
        
        # 执行
        state = executor.execute(state, decision)
        
        # 检查是否停止
        if decision.action == ControllerAction.STOP:
            break
        
        # Judge 检查（在每次 refine 后）
        if decision.action in [ControllerAction.REFINE_CHAIN, ControllerAction.REFINE_QUERY]:
            from tools import judge_exec_one_sample
            judge_sample = judge_exec_one_sample(
                state.sample,
                llm=llm,
                llm_options=llm_options
            )
            state.sample = judge_sample
            state.conclusion = judge_sample.get("judge", "[Incorrect]")
            
            # 如果正确，更新树并停止
            if state.is_correct:
                update_decision = Decision(
                    action=ControllerAction.UPDATE_TREE,
                    reason="Correct answer, update tree",
                    confidence=1.0,
                    source="rule"
                )
                state = executor.execute(state, update_decision)
                break
    
    return state.sample

集成到现有代码：

# 在 main_tree_based.py 中修改
if use_multi_agent:
    print("Using controller-based refinement...")
    
    refined_samples = []
    for sample in all_samples:
        # 使用 Controller 主循环
        refined_sample = controller_main_loop(
            sample,
            llm=gpt_llm,
            llm_options=gpt_llm.get_model_options(
                temperature=0.0,
                per_example_max_decode_steps=2048,
                per_example_top_p=1.0
            ),
            max_iterations=2
        )
        refined_samples.append(refined_sample)
    
    refine_list = refined_samples
else:
    # 使用原有方法
    print("Using original refinement method...")
    # ... 现有代码


---

阶段 2：提取独立 Retriever

目标：将检索功能从 CriticAgent 中提取出来

# agents/retriever_agent.py
class RetrieverAgent(BaseAgent):
    """独立的检索器 Agent"""
    
    def __init__(self, llm, memory_path: str = "critic/TableFV/tools/few_shot_critic.json"):
        super().__init__(AgentType.RETRIEVER, llm)
        self.memory_path = memory_path
        self.blueprint_cache = {}
    
    def retrieve_by_route(self, error_route: str) -> Dict[str, Any]:
        """根据 error_route 检索 blueprint 和 few-shot 示例"""
        
        if error_route in self.blueprint_cache:
            return self.blueprint_cache[error_route]
        
        try:
            with open(self.memory_path, 'r') as f:
                error_tree = json.load(f)
            
            result = {
                "blueprint": None,
                "few_shot_examples": []
            }
            
            # 查找 blueprint
            if error_route != 'random':
                route_parts = error_route.split('->')
                current = error_tree
                
                for part in route_parts:
                    part = part.strip()
                    if part in current:
                        current = current[part]
                        if isinstance(current, dict) and 'blueprint' in current:
                            result["blueprint"] = current['blueprint']
                            break
                    else:
                        break
                
                # 查找 few-shot 示例
                if isinstance(current, list):
                    result["few_shot_examples"] = current[:3]
            
            self.blueprint_cache[error_route] = result
            return result
            
        except Exception as e:
            print(f"Retriever error: {e}")
            return {"blueprint": None, "few_shot_examples": []}
    
    def retrieve_by_similarity(
        self, 
        query: str, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """基于相似度检索（未来扩展）"""
        # TODO: 实现向量检索
        return []


---

阶段 3：增强 Controller 决策能力

目标：添加更智能的决策逻辑

class EnhancedController(MinimalController):
    """增强版 Controller"""
    
    def __init__(self, llm, retriever: RetrieverAgent):
        super().__init__(llm)
        self.retriever = retriever
    
    def _llm_decide(self, state: ControllerState) -> Decision:
        """增强版 LLM 决策"""
        
        # 构建 prompt（包含更多上下文）
        prompt = self._build_enhanced_prompt(state)
        
        try:
            response = self.llm.generate(
                prompt,
                options=self.llm.get_model_options(
                    temperature=0.0,
                    max_tokens=200
                )
            )
            decision_data = json.loads(response)
            
            # 后处理：检查决策是否合理
            return self._validate_decision(decision_data, state)
            
        except Exception as e:
            print(f"LLM decision failed: {e}, using fallback")
            return self._default_decision(state)
    
    def _build_enhanced_prompt(self, state: ControllerState) -> str:
        """构建增强版 prompt"""
        
        # 获取检索结果
        retrieval_result = None
        if state.error_route:
            retrieval_result = self.retriever.retrieve_by_route(state.error_route)
        
        prompt = f"""You are a reasoning controller. Decide the next action.

Current State:
- Question: {state.question}
- Iteration: {state.iteration}
- Last action: {state.last_action}
- Error route: {state.error_route or "N/A"}
- Has diagnosis: {state.diagnosis is not None}
"""
        
        if retrieval_result:
            if retrieval_result["blueprint"]:
                prompt += f"- Blueprint available: {retrieval_result['blueprint']}\n"
            if retrieval_result["few_shot_examples"]:
                prompt += f"- Few-shot examples: {len(retrieval_result['few_shot_examples'])} available\n"
        
        prompt += f"""
Available Actions:
- EXECUTE_TREE: Run tree_exec_one_sample to classify error type
- DIAGNOSE_BP: Diagnose error using blueprint only
- DIAGNOSE_FS: Diagnose error using blueprint + few-shot examples
- REFINE_CHAIN: Refine reasoning chain from error step
- REFINE_QUERY: Refine only the final query
- UPDATE_TREE: Update error tree with successful case
- STOP: Stop iteration

Decision Guidelines:
1. First iteration: Always start with EXECUTE_TREE to get error_route
2. After EXECUTE_TREE: Use DIAGNOSE_BP (blueprint only)
3. If DIAGNOSE_BP fails: Try DIAGNOSE_FS (with few-shot)
4. After diagnosis: Use REFINE_CHAIN or REFINE_QUERY based on error type
5. If correct after refine: Use UPDATE_TREE then STOP
6. Max iterations: {self.max_iterations}

Output JSON: {{"action": "...", "reason": "...", "confidence": 0.0-1.0}}"""
        
        return prompt
    
    def _validate_decision(
        self, 
        decision_data: Dict, 
        state: ControllerState
    ) -> Decision:
        """验证 LLM 决策的合理性"""
        
        action_str = decision_data.get("action", "")
        
        # 规则验证
        if state.iteration == 0 and action_str != "EXECUTE_TREE":
            # 第一次必须执行 tree
            print(f"Invalid action for iteration 0: {action_str}, forcing EXECUTE_TREE")
            decision_data["action"] = "EXECUTE_TREE"
            decision_data["reason"] = "First iteration must execute tree"
        
        elif state.error_route is None and action_str.startswith("DIAGNOSE"):
            # 没有 error_route 不能诊断
            print(f"Cannot diagnose without error_route, forcing EXECUTE_TREE")
            decision_data["action"] = "EXECUTE_TREE"
            decision_data["reason"] = "Need error_route before diagnosis"
        
        elif state.diagnosis is None and action_str.startswith("REFINE"):
            # 没有诊断不能精炼
            print(f"Cannot refine without diagnosis, forcing DIAGNOSE_BP")
            decision_data["action"] = "DIAGNOSE_BP"
            decision_data["reason"] = "Need diagnosis before refinement"
        
        elif not state.is_correct and action_str == "UPDATE_TREE":
            # 不正确不能更新树
            print(f"Cannot update tree with incorrect answer, forcing STOP")
            decision_data["action"] = "STOP"
            decision_data["reason"] = "Only update tree with correct answers"
        
        return Decision(
            action=ControllerAction(decision_data["action"]),
            reason=decision_data.get("reason", ""),
            confidence=decision_data.get("confidence", 0.5),
            source="llm"
        )


---

阶段 4：添加状态追踪和可视化

目标：提高可调试性和可解释性

class ControllerLogger:
    """Controller 日志记录器"""
    
    def __init__(self):
        self.transitions = []
    
    def log_transition(
        self, 
        state: ControllerState, 
        decision: Decision, 
        new_state: ControllerState
    ):
        """记录状态转换"""
        self.transitions.append({
            "iteration": state.iteration,
            "state_before": {
                "is_correct": state.is_correct,
                "error_route": state.error_route,
                "has_diagnosis": state.diagnosis is not None,
            },
            "decision": {
                "action": decision.action.value,
                "source": decision.source,
                "confidence": decision.confidence,
                "reason": decision.reason,
            },
            "state_after": {
                "is_correct": new_state.is_correct,
                "error_route": new_state.error_route,
                "has_diagnosis": new_state.diagnosis is not None,
            },
        })
    
    def visualize(self) -> str:
        """生成可视化日志"""
        lines = []
        for trans in self.transitions:
            lines.append(f"Iteration {trans['iteration']}:")
            lines.append(f"  State: {trans['state_before']}")
            lines.append(f"  Decision: {trans['decision']['action']} ({trans['decision']['source']})")
            lines.append(f"  Reason: {trans['decision']['reason']}")
            lines.append(f"  New State: {trans['state_after']}")
            lines.append("")
        return "\n".join(lines)
    
    def generate_mermaid(self) -> str:
        """生成 Mermaid 状态机图"""
        lines = ["graph TD"]
        
        for i, trans in enumerate(self.transitions):
            node_id = f"S{i}"
            label = f"Iter {trans['iteration']}\\n{trans['decision']['action']}"
            lines.append(f"  {node_id}[{label}]")
        
        for i in range(len(self.transitions) - 1):
            from_id = f"S{i}"
            to_id = f"S{i+1}"
            decision = self.transitions[i]['decision']
            label = f"{decision['source']}\\nconf={decision['confidence']:.2f}"
            lines.append(f"  {from_id} -->|{label}| {to_id}")
        
        return "\n".join(lines)


---

三、总结

关键改进点

阶段
目标
关键改进
阶段 1
最小可行 Controller
包装现有流程，不破坏兼容性
阶段 2
独立 Retriever
提取检索功能，支持独立调用
阶段 3
增强决策
添加智能决策和验证机制
阶段 4
状态追踪
提高可调试性和可解释性

与现有代码的兼容性

graph LR
    A[现有流程] --> B[judge → tree → critic → refine → judge]
    C[Controller] --> D[包装现有流程]
    D --> B
    E[渐进式迁移] --> F[阶段1: 包装<br>阶段2: Retriever<br>阶段3: 增强决策<br>阶段4: 状态追踪]
    
    style A fill:#fbb,stroke:#333,stroke-width:2px
    style C fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#bfb,stroke:#333,stroke-width:2px

实施建议

1. 先实现阶段 1：包装现有流程，验证 Controller 概念
2. 逐步添加功能：每个阶段完成后测试，确保不破坏现有功能
3. 保持双模式：use_multi_agent=False 使用原有流程，use_multi_agent=True 使用 Controller
4. 充分测试：在每个阶段完成后，对比两种模式的结果，确保一致性
  
这样可以在不破坏现有代码的前提下，逐步引入 Controller 的智能决策能力。