"""
测试 EnhancedController 实现

验证阶段3的实现：
1. EnhancedController 类是否存在
2. _build_enhanced_prompt 方法是否正常工作
3. _validate_decision 方法是否正常工作
4. EnhancedController 是否能正确继承 MinimalController
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tableqa_enhanced_controller():
    """测试 TableQA 的 EnhancedController"""
    print("=" * 80)
    print("测试 TableQA 的 EnhancedController")
    print("=" * 80)
    
    try:
        from refine.TableQA.utils.controller import (
            EnhancedController,
            ControllerState,
            ControllerAction,
            Decision
        )
        print("✅ 成功导入 EnhancedController 及相关类")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试 1: 检查 EnhancedController 是否继承自 MinimalController
    try:
        from refine.TableQA.utils.controller import MinimalController
        assert issubclass(EnhancedController, MinimalController)
        print("✅ EnhancedController 正确继承自 MinimalController")
    except Exception as e:
        print(f"❌ 继承检查失败: {e}")
        return False
    
    # 测试 2: 检查方法是否存在
    try:
        assert hasattr(EnhancedController, '_build_enhanced_prompt')
        assert hasattr(EnhancedController, '_validate_decision')
        assert hasattr(EnhancedController, '_llm_decide_diagnose_enhanced')
        assert hasattr(EnhancedController, '_llm_decide_refine_enhanced')
        print("✅ EnhancedController 包含所有必需的方法")
    except Exception as e:
        print(f"❌ 方法检查失败: {e}")
        return False
    
    # 测试 3: 测试 _build_enhanced_prompt 方法
    try:
        # 创建模拟状态
        sample = {
            "statement": "测试问题",
            "chain": [],
            "conclusion": "[Incorrect]"
        }
        state = ControllerState(
            sample=sample,
            question="测试问题",
            chain=[],
            conclusion="[Incorrect]",
            iteration=0,
            last_action="INIT",
            error_route="random"
        )
        
        # 创建模拟的 LLM 和 retriever
        class MockLLM:
            def generate(self, prompt, options=None):
                return '{"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}'
            
            def get_model_options(self, **kwargs):
                return {}
        
        class MockRetriever:
            def retrieve_by_route(self, route):
                return {
                    'blueprint': 'test blueprint',
                    'few_shot_examples': [{'test': 'example'}]
                }
        
        controller = EnhancedController(
            llm=MockLLM(),
            llm_options={},
            max_iterations=2,
            retriever=MockRetriever()
        )
        
        # 测试 _build_enhanced_prompt
        prompt_diagnose = controller._build_enhanced_prompt(state, decision_type="diagnose")
        assert "You are a reasoning controller" in prompt_diagnose
        assert "DIAGNOSE_BP" in prompt_diagnose
        assert "DIAGNOSE_FS" in prompt_diagnose
        print("✅ _build_enhanced_prompt (diagnose) 正常工作")
        
        # 测试 refine prompt
        state.diagnosis = {"conclusion": "[Incorrect]", "max_step": 3}
        prompt_refine = controller._build_enhanced_prompt(state, decision_type="refine")
        assert "You are a reasoning controller" in prompt_refine
        assert "REFINE_CHAIN" in prompt_refine
        assert "REFINE_QUERY" in prompt_refine
        print("✅ _build_enhanced_prompt (refine) 正常工作")
        
    except Exception as e:
        print(f"❌ _build_enhanced_prompt 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试 4: 测试 _validate_decision 方法
    try:
        # 测试 diagnose 决策验证
        decision_data = {"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state, decision_type="diagnose")
        assert decision.action == ControllerAction.DIAGNOSE_BP
        assert decision.source == "llm"
        print("✅ _validate_decision (diagnose) 正常工作")
        
        # 测试 refine 决策验证
        decision_data = {"action": "REFINE_CHAIN", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state, decision_type="refine")
        assert decision.action == ControllerAction.REFINE_CHAIN
        assert decision.source == "llm"
        print("✅ _validate_decision (refine) 正常工作")
        
    except Exception as e:
        print(f"❌ _validate_decision 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试 5: 测试规则验证
    try:
        # 测试没有 error_route 时的验证
        state_no_route = ControllerState(
            sample=sample,
            question="测试问题",
            chain=[],
            conclusion="[Incorrect]",
            iteration=1,
            last_action="EXECUTE_TREE",
            error_route=None
        )
        decision_data = {"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state_no_route, decision_type="diagnose")
        # 应该被修正为 EXECUTE_TREE
        assert decision.action == ControllerAction.EXECUTE_TREE
        print("✅ 规则验证（无 error_route）正常工作")
        
    except Exception as e:
        print(f"❌ 规则验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("TableQA EnhancedController 测试全部通过！")
    print("=" * 80)
    return True


def test_tablefv_enhanced_controller():
    """测试 TableFV 的 EnhancedController"""
    print("\n" + "=" * 80)
    print("测试 TableFV 的 EnhancedController")
    print("=" * 80)
    
    try:
        from refine.TableFV.utils.controller import (
            EnhancedController,
            ControllerState,
            ControllerAction,
            Decision
        )
        print("✅ 成功导入 EnhancedController 及相关类")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试 1: 检查 EnhancedController 是否继承自 MinimalController
    try:
        from refine.TableFV.utils.controller import MinimalController
        assert issubclass(EnhancedController, MinimalController)
        print("✅ EnhancedController 正确继承自 MinimalController")
    except Exception as e:
        print(f"❌ 继承检查失败: {e}")
        return False
    
    # 测试 2: 检查方法是否存在
    try:
        assert hasattr(EnhancedController, '_build_enhanced_prompt')
        assert hasattr(EnhancedController, '_validate_decision')
        assert hasattr(EnhancedController, '_llm_decide_diagnose_enhanced')
        assert hasattr(EnhancedController, '_llm_decide_refine_enhanced')
        print("✅ EnhancedController 包含所有必需的方法")
    except Exception as e:
        print(f"❌ 方法检查失败: {e}")
        return False
    
    # 测试 3: 测试 _build_enhanced_prompt 方法
    try:
        # 创建模拟状态
        sample = {
            "statement": "测试问题",
            "chain": [],
            "conclusion": "[Incorrect]"
        }
        state = ControllerState(
            sample=sample,
            question="测试问题",
            chain=[],
            conclusion="[Incorrect]",
            iteration=0,
            last_action="INIT",
            error_route="random"
        )
        
        # 创建模拟的 LLM 和 retriever
        class MockLLM:
            def generate(self, prompt, options=None):
                return '{"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}'
            
            def get_model_options(self, **kwargs):
                return {}
        
        class MockRetriever:
            def retrieve_by_route(self, route):
                return {
                    'blueprint': 'test blueprint',
                    'few_shot_examples': [{'test': 'example'}]
                }
        
        controller = EnhancedController(
            llm=MockLLM(),
            llm_options={},
            max_iterations=2,
            retriever=MockRetriever()
        )
        
        # 测试 _build_enhanced_prompt
        prompt_diagnose = controller._build_enhanced_prompt(state, decision_type="diagnose")
        assert "You are a reasoning controller" in prompt_diagnose
        assert "DIAGNOSE_BP" in prompt_diagnose
        assert "DIAGNOSE_FS" in prompt_diagnose
        print("✅ _build_enhanced_prompt (diagnose) 正常工作")
        
        # 测试 refine prompt
        state.diagnosis = {"conclusion": "[Incorrect]", "max_step": 3}
        prompt_refine = controller._build_enhanced_prompt(state, decision_type="refine")
        assert "You are a reasoning controller" in prompt_refine
        assert "REFINE_CHAIN" in prompt_refine
        assert "REFINE_QUERY" in prompt_refine
        print("✅ _build_enhanced_prompt (refine) 正常工作")
        
    except Exception as e:
        print(f"❌ _build_enhanced_prompt 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试 4: 测试 _validate_decision 方法
    try:
        # 测试 diagnose 决策验证
        decision_data = {"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state, decision_type="diagnose")
        assert decision.action == ControllerAction.DIAGNOSE_BP
        assert decision.source == "llm"
        print("✅ _validate_decision (diagnose) 正常工作")
        
        # 测试 refine 决策验证
        decision_data = {"action": "REFINE_CHAIN", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state, decision_type="refine")
        assert decision.action == ControllerAction.REFINE_CHAIN
        assert decision.source == "llm"
        print("✅ _validate_decision (refine) 正常工作")
        
    except Exception as e:
        print(f"❌ _validate_decision 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试 5: 测试规则验证
    try:
        # 测试没有 error_route 时的验证
        state_no_route = ControllerState(
            sample=sample,
            question="测试问题",
            chain=[],
            conclusion="[Incorrect]",
            iteration=1,
            last_action="EXECUTE_TREE",
            error_route=None
        )
        decision_data = {"action": "DIAGNOSE_BP", "reason": "Test", "confidence": 0.9}
        decision = controller._validate_decision(decision_data, state_no_route, decision_type="diagnose")
        # 应该被修正为 EXECUTE_TREE
        assert decision.action == ControllerAction.EXECUTE_TREE
        print("✅ 规则验证（无 error_route）正常工作")
        
    except Exception as e:
        print(f"❌ 规则验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 80)
    print("TableFV EnhancedController 测试全部通过！")
    print("=" * 80)
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("开始测试阶段3：EnhancedController 实现")
    print("=" * 80 + "\n")
    
    tableqa_passed = test_tableqa_enhanced_controller()
    tablefv_passed = test_tablefv_enhanced_controller()
    
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"TableQA EnhancedController: {'✅ 通过' if tableqa_passed else '❌ 失败'}")
    print(f"TableFV EnhancedController: {'✅ 通过' if tablefv_passed else '❌ 失败'}")
    print("=" * 80)
    
    if tableqa_passed and tablefv_passed:
        print("\n🎉 所有测试通过！阶段3实现成功！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查实现")
        return 1


if __name__ == "__main__":
    sys.exit(main())
