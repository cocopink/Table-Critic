"""
阶段一：最小可行 Controller（与现有代码兼容）

该模块实现了 Controller 框架，可以在不修改现有流程的前提下，
通过包装现有函数调用来添加 Controller 层。

功能：
- ControllerState: 状态管理
- ControllerAction: 动作空间定义
- Decision: 决策结果
- MinimalController: 决策逻辑
- ActionExecutor: 动作执行器
- controller_main_loop: 主循环
"""

import re
import json
import copy
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from contextlib import nullcontext

# 调试模式开关
# DEBUG = os.environ.get("CONTROLLER_DEBUG", "false").lower() == "true"
DEBUG = True


# ==================== 1. ControllerState 数据类 ====================

@dataclass
class ControllerState:
    """
    Controller 状态管理类
    
    属性:
        sample: 从现有 sample 提取的完整数据
        question: 问题描述
        chain: 推理链
        conclusion: 结论 ("[Correct]" or "[Incorrect]")
        iteration: 当前迭代次数
        last_action: 上一次执行的动作
        error_route: 错误路由
        retrieved_blueprints: 检索到的蓝图
        diagnosis: 诊断结果
        action_history: 历史动作记录
    """
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
        """判断当前状态是否正确"""
        return "[Correct]" in self.conclusion


# ==================== 2. ControllerAction 枚举 ====================

class ControllerAction(Enum):
    """
    简化动作空间（与现有流程对应）
    
    STOP: 停止（对应现有流程的结束）
    EXECUTE_TREE: 执行 tree_exec_one_sample
    DIAGNOSE_BP: 诊断（blueprint 模式）
    DIAGNOSE_FS: 诊断（few-shot 模式）
    REFINE_CHAIN: 精炼推理链
    REFINE_QUERY: 精炼最终查询
    UPDATE_TREE: 更新错误树
    """
    STOP = "STOP"
    EXECUTE_TREE = "EXECUTE_TREE"
    DIAGNOSE_BP = "DIAGNOSE_BP"
    DIAGNOSE_FS = "DIAGNOSE_FS"
    REFINE_CHAIN = "REFINE_CHAIN"
    REFINE_QUERY = "REFINE_QUERY"
    UPDATE_TREE = "UPDATE_TREE"


# ==================== 3. Decision 数据类 ====================

@dataclass
class Decision:
    """
    决策结果
    
    属性:
        action: 选择的动作
        reason: 决策原因
        confidence: 置信度 (0.0-1.0)
        source: 决策来源 ("rule" | "llm")
    """
    action: ControllerAction
    reason: str
    confidence: float
    source: str  # "rule" | "llm"


# ==================== 4. MinimalController 类 ====================

class MinimalController:
    """
    最小 Controller、
    
    决策逻辑：
    1. 规则层：如果正确，停止
    2. 规则层：达到最大迭代次数，停止
    3. LLM 层：决定下一步动作（可选）
    """
    
    def __init__(self, llm,llm_options, max_iterations: int = 2):
        """
        初始化 Controller
        
        Args:
            llm: 语言模型实例
            max_iterations: 最大迭代次数
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.llm_options = llm_options
    
    def decide(self, state: ControllerState) -> Decision:
        """
        基于当前状态决定下一步动作
        
        Args:
            state: 当前状态
            
        Returns:
            Decision: 决策结果
        """
        
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
        """
        使用 LLM 决策（通用版）
        
        根据当前状态决定下一步动作：
        - EXECUTE_TREE 后：决定 DIAGNOSE_BP 还是 DIAGNOSE_FS
        - DIAGNOSE 后：决定 REFINE_CHAIN 还是 REFINE_QUERY
        
        Args:
            state: 当前状态
            
        Returns:
            Decision: 决策结果
        """
        try:
            # 根据上一步动作决定 LLM 决策类型
            if state.last_action == ControllerAction.EXECUTE_TREE.value or state.last_action == "INIT":
                # EXECUTE_TREE 后：决定 DIAGNOSE_BP 还是 DIAGNOSE_FS
                return self._llm_decide_diagnose(state)
            elif state.last_action in [ControllerAction.DIAGNOSE_BP.value, ControllerAction.DIAGNOSE_FS.value]:
                # DIAGNOSE 后：决定 REFINE_CHAIN 还是 REFINE_QUERY
                return self._llm_decide_refine(state)
            else:
                # 默认使用规则决策
                return self._default_decision(state)
        except Exception as e:
            # LLM 决策失败时，直接停止流程
            print(f"LLM decision failed: {e}, stopping flow")
            # return self._default_decision(state)
            return Decision(
                action=ControllerAction.STOP,
                reason=f"LLM decision failed: {e}",
                confidence=0.0,
                source="llm"
            )
    
    def _default_decision(self, state: ControllerState) -> Decision:
        """
        默认决策（模拟现有流程 _judge_critic_refine_with_cache_mp_core）
        
        决策流程：
        1. 初始Judge判断 → 如果正确直接返回
        2. EXECUTE_TREE → 获取 error_route
        3. DIAGNOSE_BP (iteration=1) / DIAGNOSE_FS (iteration=2)
        4. 根据 incorrect_step 决定 REFINE_CHAIN 或 REFINE_QUERY
        5. Judge → 如果正确更新树并返回
        
        Args:
            state: 当前状态
            
        Returns:
            Decision: 决策结果
        """
        # 根据当前状态和迭代次数决定下一步动作
        if state.iteration == 0:
            # 第一次迭代：执行树分类获取 error_route
            return Decision(
                action=ControllerAction.EXECUTE_TREE,
                reason="First iteration: execute tree to get error_route",
                confidence=0.9,
                source="rule"
            )
        elif state.iteration == 1:
            # 第二次迭代：使用 blueprint 模式诊断
            if state.last_action == ControllerAction.EXECUTE_TREE:
                return Decision(
                    action=ControllerAction.DIAGNOSE_BP,
                    reason="Second iteration: diagnose with blueprint_only=True",
                    confidence=0.9,
                    source="rule"
                )
            elif state.last_action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
                # 诊断后，根据 incorrect_step 决定精炼类型
                from refine.TableFV.utils.extract_step import return_incorrect_max_step
                incorrect_step, max_step = return_incorrect_max_step(state.sample)
                if incorrect_step and incorrect_step != max_step:
                    return Decision(
                        action=ControllerAction.REFINE_CHAIN,
                        reason="Error in reasoning chain (incorrect_step != max_step), refine chain",
                        confidence=0.9,
                        source="rule"
                    )
                else:
                    return Decision(
                        action=ControllerAction.REFINE_QUERY,
                        reason="Error in final query (incorrect_step == max_step), refine query",
                        confidence=0.9,
                        source="rule"
                    )
        elif state.iteration == 2:
            # 第三次迭代：使用 full few-shot 模式诊断
            if state.last_action in [ControllerAction.EXECUTE_TREE, ControllerAction.DIAGNOSE_BP]:
                return Decision(
                    action=ControllerAction.DIAGNOSE_FS,
                    reason="Third iteration: diagnose with blueprint_only=False (few-shot)",
                    confidence=0.8,
                    source="rule"
                )
            elif state.last_action in [ControllerAction.DIAGNOSE_FS, ControllerAction.REFINE_CHAIN, ControllerAction.REFINE_QUERY]:
                # 诊断/精炼后，根据 incorrect_step 决定精炼类型
                from refine.TableFV.utils.extract_step import return_incorrect_max_step
                incorrect_step, max_step = return_incorrect_max_step(state.sample)
                if incorrect_step and incorrect_step != max_step:
                    return Decision(
                        action=ControllerAction.REFINE_CHAIN,
                        reason="Error in reasoning chain, refine chain",
                        confidence=0.8,
                        source="rule"
                    )
                else:
                    return Decision(
                        action=ControllerAction.REFINE_QUERY,
                        reason="Error in final query, refine query",
                        confidence=0.8,
                        source="rule"
                    )
        
        # 默认停止
        return Decision(
            action=ControllerAction.STOP,
            reason="No more actions available",
            confidence=0.5,
            source="rule"
        )
    
    def _llm_decide_refine(self, state: ControllerState) -> Decision:
        """
        使用 LLM 决定下一步是 REFINE_CHAIN 还是 REFINE_QUERY
        
        Args:
            state: 当前状态
            
        Returns:
            Decision: 决策结果
        """
        # 获取诊断信息
        from refine.TableFV.utils.extract_step import return_incorrect_max_step
        incorrect_step, max_step = return_incorrect_max_step(state.sample)
        
        # 构建 LLM 决策 prompt
        prompt = f"""Current state:
- Iteration: {state.iteration}
- Last action: {state.last_action}
- Error route: {state.error_route or "N/A"}
- Diagnosis conclusion: {state.diagnosis.get("conclusion", "N/A") if state.diagnosis else "N/A"}
- Incorrect step: {incorrect_step}
- Max step: {max_step}

Based on the diagnosis, decide next action:
- REFINE_CHAIN: If the error is in the reasoning chain (incorrect_step != max_step)
- REFINE_QUERY: If the error is only in the final query (incorrect_step == max_step)

Output JSON: {{"action": "...", "reason": "...", "confidence": 0.0-1.0}}"""
        
        try:
            response = self.llm.generate(
                prompt,
                options=self.llm_options
            )
            decision_data = json.loads(response)
            
            # 验证决策
            action_str = decision_data.get("action", "")
            if "CHAIN" in action_str.upper():
                action = ControllerAction.REFINE_CHAIN
            elif "QUERY" in action_str.upper():
                action = ControllerAction.REFINE_QUERY
            else:
                # 默认根据 incorrect_step 决定
                if incorrect_step and incorrect_step != max_step:
                    action = ControllerAction.REFINE_CHAIN
                else:
                    action = ControllerAction.REFINE_QUERY
            
            return Decision(
                action=action,
                reason=decision_data.get("reason", ""),
                confidence=decision_data.get("confidence", 0.5),
                source="llm"
            )
        except Exception as e:
            # Fallback: 使用规则
            print(f"LLM refine decision failed: {e}, using rule-based decision")
            if incorrect_step and incorrect_step != max_step:
                return Decision(
                    action=ControllerAction.REFINE_CHAIN,
                    reason="Error in reasoning chain (incorrect_step != max_step), refine chain",
                    confidence=0.9,
                    source="rule"
                )
            else:
                return Decision(
                    action=ControllerAction.REFINE_QUERY,
                    reason="Error in final query (incorrect_step == max_step), refine query",
                    confidence=0.9,
                    source="rule"
                )
    
    def _llm_decide_diagnose(self, state: ControllerState) -> Decision:
        """
        使用 LLM 决定下一步是 DIAGNOSE_BP 还是 DIAGNOSE_FS
        
        Args:
            state: 当前状态
            
        Returns:
            Decision: 决策结果
        """
        # 构建 LLM 决策 prompt
        prompt = f"""Current state:
- Iteration: {state.iteration}
- Last action: {state.last_action}
- Error route: {state.error_route or "N/A"}
- Has been diagnosed with blueprint: {ControllerAction.DIAGNOSE_BP.value in state.action_history}

Decide next action:
- DIAGNOSE_BP: Use blueprint-only mode (faster, less context)
- DIAGNOSE_FS: Use few-shot mode (slower, more context with examples)

Use DIAGNOSE_BP if you haven't tried blueprint mode yet.
Use DIAGNOSE_FS if blueprint mode failed or you need more context.

Output JSON: {{"action": "...", "reason": "...", "confidence": 0.0-1.0}}"""
        
        try:
            response = self.llm.generate(
                prompt,
                options=self.llm_options
            )
            decision_data = json.loads(response)
            
            # 验证决策
            action_str = decision_data.get("action", "")
            if "BP" in action_str.upper() and "FS" not in action_str.upper():
                action = ControllerAction.DIAGNOSE_BP
            elif "FS" in action_str.upper():
                action = ControllerAction.DIAGNOSE_FS
            else:
                # 默认：如果之前没有 DIAGNOSE_BP，使用 DIAGNOSE_BP
                if ControllerAction.DIAGNOSE_BP.value not in state.action_history:
                    action = ControllerAction.DIAGNOSE_BP
                else:
                    action = ControllerAction.DIAGNOSE_FS
            
            return Decision(
                action=action,
                reason=decision_data.get("reason", ""),
                confidence=decision_data.get("confidence", 0.5),
                source="llm"
            )
        except Exception as e:
            # Fallback: 使用规则
            print(f"LLM diagnose decision failed: {e}, using rule-based decision")
            if ControllerAction.DIAGNOSE_BP.value not in state.action_history:
                return Decision(
                    action=ControllerAction.DIAGNOSE_BP,
                    reason="First diagnose: use blueprint mode",
                    confidence=0.9,
                    source="rule"
                )
            else:
                return Decision(
                    action=ControllerAction.DIAGNOSE_FS,
                    reason="Blueprint mode done: use few-shot mode",
                    confidence=0.8,
                    source="rule"
                )


# ==================== 5. ActionExecutor 类 ====================

class ActionExecutor:
    """
    动作执行器（包装现有函数）
    
    负责执行 Controller 决策的动作，并更新状态
    """
    
    def __init__(self, llm, llm_options):
        """
        初始化执行器
        
        Args:
            llm: 语言模型实例
            llm_options: 模型选项
        """
        self.llm = llm
        self.llm_options = llm_options
    
    def execute(self, state: ControllerState, decision: Decision) -> ControllerState:
        """
        执行决策并更新状态
        
        Args:
            state: 当前状态
            decision: 决策结果
            
        Returns:
            ControllerState: 更新后的状态
        """
        action = decision.action
        
        if action == ControllerAction.STOP:
            return state
        
        elif action == ControllerAction.EXECUTE_TREE:
            from critic.TableFV.tools import tree_exec_one_sample
            tree_sample = tree_exec_one_sample(
                state.sample, 
                llm=self.llm, 
                llm_options=self.llm_options
            )
            routes = re.findall(r'\((.*?)\)', tree_sample.get('tree', ''))
            # routes = re.findall(r'\((.*?)\)', tree_sample['tree'])
            state.error_route = routes[0] if routes else "random"
            state.sample = tree_sample
        
        elif action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
            from critic.TableFV.tools import critic_exec_one_sample
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
            from refine.TableFV.utils.chain import dynamic_chain_exec_one_sample
            from refine.TableFV.utils.extract_step import return_incorrect_max_step
            incorrect_step, max_step = return_incorrect_max_step(state.sample)
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
            from refine.TableFV.utils.chain import simple_query_with_critic, get_table_info
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
            from critic.TableFV.tools import update_error_tree
            # 调试信息
            print(f"[DEBUG UPDATE_TREE] error_route: {state.error_route}")
            print(f"[DEBUG UPDATE_TREE] sample keys: {list(state.sample.keys())}")
            print(f"[DEBUG UPDATE_TREE] critique exists: {'critique' in state.sample}")
            print(f"[DEBUG UPDATE_TREE] conclusion: {state.sample.get('conclusion', 'N/A')}")
            
            # 使用 nullcontext() 替代 lock=None，支持上下文管理器协议
            update_error_tree(
                state.sample,
                state.error_route or "random",
                error_tree_json="critic/TableFV/tools/few_shot_critic.json",
                llm=self.llm,
                llm_options=self.llm_options,
                lock=nullcontext()
            )
            print(f"[DEBUG UPDATE_TREE] Finished update_error_tree call")
        
        # 更新状态
        state.iteration += 1
        state.last_action = action.value
        state.action_history.append(action.value)
        
        # 更新 conclusion
        state.conclusion = state.sample.get("conclusion", "[Incorrect]")
        
        return state


# ==================== 6. controller_main_loop 函数 ====================

def controller_main_loop(
    sample: Dict[str, Any],
    llm,
    llm_options,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """
    Controller 主循环（兼容现有代码）
    
    这是阶段一的核心函数，它包装了现有的流程，
    通过 Controller 来决定下一步动作。
    
    Args:
        sample: 输入样本
        llm: 语言模型实例
        llm_options: 模型选项
        max_iterations: 最大迭代次数
        
    Returns:
        Dict[str, Any]: 处理后的样本
    """
    
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
        # conclusion=judge_sample.get("judge", "[Incorrect]")
        conclusion="[Incorrect]"
    )
    
    # 如果初始状态已经正确，直接返回
    if state.is_correct:
        return judge_sample
    
    # 初始化组件
    controller = MinimalController(llm, llm_options, max_iterations)
    executor = ActionExecutor(llm, llm_options)
    
    # 主循环说明：
    # 一次迭代执行完整流程：
    # 1. decide() 返回 EXECUTE_TREE
    # 2. 执行 EXECUTE_TREE
    # 3. _llm_decide_diagnose() 决定 DIAGNOSE_BP 或 DIAGNOSE_FS
    # 4. 执行 DIAGNOSE_BP/FS
    # 5. _llm_decide_refine() 决定 REFINE_CHAIN 或 REFINE_QUERY
    # 6. 执行 REFINE_CHAIN/QUERY
    # 7. Judge 检查，如果正确则 UPDATE_TREE 并退出
    
    # 调试模式：打印状态转移
    if DEBUG:
        print("\n" + "="*80)
        print(f"[DEBUG] Starting controller for sample: {sample.get('id', 'unknown')}")
        print("="*80)
    
    for _ in range(max_iterations):
        # 调试打印当前状态
        if DEBUG:
            print(f"\n--- Iteration {state.iteration} ---")
            print(f"Last action: {state.last_action}")
            print(f"Conclusion: {state.conclusion}")
            print(f"Error route: {state.error_route}")
            print(f"Has diagnosis: {state.diagnosis is not None}")
        
        # 决策
        decision = controller.decide(state)
        
        # 调试打印决策
        if DEBUG:
            print(f"\n>>> Decision: {decision.action.value}")
            print(f"    Reason: {decision.reason}")
            print(f"    Confidence: {decision.confidence}")
            print(f"    Source: {decision.source}")
        
        # 执行
        state = executor.execute(state, decision)
        
        # 检查是否停止
        if decision.action == ControllerAction.STOP:
            if DEBUG:
                print(f"\n!!! STOP: {decision.reason}")
            break
        
        # 使用 LLM 决定下一个动作（根据当前状态动态决策）
        if decision.action == ControllerAction.EXECUTE_TREE:
            # EXECUTE_TREE 后：使用 LLM 决定下一步是 DIAGNOSE_BP 还是 DIAGNOSE_FS
            diagnose_decision = controller._llm_decide_diagnose(state)
            decision = diagnose_decision
            
            # 调试打印
            if DEBUG:
                print(f">>> LLM Diagnose Decision: {decision.action.value}")
                print(f"    Reason: {decision.reason}")
            
            # 执行第二次决策
            state = executor.execute(state, decision)
            
            if decision.action == ControllerAction.STOP:
                break
        
        # DIAGNOSE_BP/DIAGNOSE_FS 后：使用 LLM 决定下一步是 REFINE_CHAIN 还是 REFINE_QUERY
        if decision.action in [ControllerAction.DIAGNOSE_BP, ControllerAction.DIAGNOSE_FS]:
            # 使用 LLM 决定下一步
            refine_decision = controller._llm_decide_refine(state)
            decision = refine_decision
            
            # 调试打印
            if DEBUG:
                print(f">>> LLM Refine Decision: {decision.action.value}")
                print(f"    Reason: {decision.reason}")
            
            # 执行精炼决策
            state = executor.execute(state, decision)
            
            if decision.action == ControllerAction.STOP:
                break
        
        # REFINE_CHAIN/REFINE_QUERY 后：使用 Judge 检查
        if decision.action in [ControllerAction.REFINE_CHAIN, ControllerAction.REFINE_QUERY]:
            from critic.TableFV.tools import judge_exec_one_sample
            judge_sample = judge_exec_one_sample(
                state.sample,
                llm=llm,
                llm_options=llm_options
            )
            state.sample = judge_sample
            state.conclusion = judge_sample.get("judge", "[Incorrect]")
            
            # 调试打印
            if DEBUG:
                print(f">>> Judge Result: {state.conclusion}")
            
            # 如果正确，更新树并停止
            if state.is_correct:
                update_decision = Decision(
                    action=ControllerAction.UPDATE_TREE,
                    reason="Correct answer, update tree",
                    confidence=1.0,
                    source="rule"
                )
                state = executor.execute(state, update_decision)
                if DEBUG:
                    print(f">>> UPDATED TREE!")
                break
    
    # 调试模式：打印最终结果
    if DEBUG:
        print("\n" + "="*80)
        print(f"[DEBUG] Final conclusion: {state.conclusion}")
        print("="*80)
    
    return state.sample


# ==================== 7. 便捷函数 ====================

def create_controller_state(sample: Dict[str, Any]) -> ControllerState:
    """
    从样本创建 ControllerState
    
    Args:
        sample: 输入样本
        
    Returns:
        ControllerState: 初始状态
    """
    return ControllerState(
        sample=sample,
        question=sample.get("statement", ""),
        chain=sample.get("chain", []),
        conclusion=sample.get("conclusion", "[Incorrect]") #默认Incorrect
    )


def run_with_controller(
    sample: Dict[str, Any],
    llm,
    llm_options,
    max_iterations: int = 2
) -> Dict[str, Any]:
    """
    使用 Controller 运行样本的便捷函数
    
    Args:
        sample: 输入样本
        llm: 语言模型实例
        llm_options: 模型选项
        max_iterations: 最大迭代次数
        
    Returns:
        Dict[str, Any]: 处理后的样本
    """
    return controller_main_loop(
        sample=sample,
        llm=llm,
        llm_options=llm_options,
        max_iterations=max_iterations
    )
