# Memory 模块文档

[根目录](../CLAUDE.md) > **memory**

> 最后更新：2026-04-16 00:17:51

---

## 变更记录 (Changelog)

### 2026-04-16
- 初始化 memory 模块文档
- 建立主动遗忘机制文档
- 识别记忆演化流程

---

## 模块职责

Memory 模块是 Table-Critic 的**记忆管理系统**，负责实现基于博弈论的记忆演化机制，包括主动遗忘、案例记录和权重更新。

### 核心功能

1. **案例记录**：记录每个错误案例的完整信息
2. **权重管理**：维护每个案例的置信度分数（confidence_score）
3. **主动遗忘**：淘汰长期低权重的案例，为新错误腾出空间
4. **记忆集成**：协调 Curator 和 Active Forgetting 的交互

---

## 入口与启动

### 模块导入

```python
from memory import (
    CaseRecord,
    ActiveForgettingManager,
    MemoryEvolutionManager
)
```

### 使用示例

```python
from agents import CuratorAgent
from memory import ActiveForgettingManager

# 初始化
forgetting_manager = ActiveForgettingManager(
    max_cases=1000,
    min_confidence=0.3,
    decay_rate=0.05
)

# 记录新案例
case = CaseRecord(
    case_id='sample_001',
    error_route='select_row_errors/condition_error',
    blueprint='模型倾向于使用错误的比较符',
    confidence_score=0.5,
    success_count=0,
    failure_count=0,
    last_seen='2026-04-16'
)
forgetting_manager.add_case(case)

# 更新权重
forgetting_manager.update_weight('sample_001', success=True)

# 触发主动遗忘
forgetting_manager.forget_low_confidence_cases()
```

---

## 数据模型

### CaseRecord（案例记录）

**文件**：`agents/active_forgetting.py`

```python
@dataclass
class CaseRecord:
    """案例记录数据类"""
    case_id: str                      # 案例ID
    error_route: str                  # 错误路由
    blueprint: str                    # Blueprint摘要
    confidence_score: float           # 置信度分数（0-1）
    success_count: int                # 成功引导修正的次数
    failure_count: int                # 未能引导修正的次数
    last_seen: str                    # 最后使用时间
    created_at: str = ""              # 创建时间

    def __post_init__(self):
        """初始化创建时间"""
        if not self.created_at:
            from datetime import datetime
            self.created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @property
    def total_usage(self) -> int:
        """总使用次数"""
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_usage == 0:
            return 0.0
        return self.success_count / self.total_usage
```

---

## 主动遗忘管理器

### ActiveForgettingManager 类

**文件**：`agents/active_forgetting.py`

```python
class ActiveForgettingManager:
    """主动遗忘管理器"""

    def __init__(
        self,
        max_cases: int = 1000,
        min_confidence: float = 0.3,
        decay_rate: float = 0.05
    ):
        """
        初始化主动遗忘管理器

        Args:
            max_cases: 最大案例数
            min_confidence: 最低置信度阈值
            decay_rate: 衰减率（每次更新未使用案例的权重时降低的幅度）
        """
        self.max_cases = max_cases
        self.min_confidence = min_confidence
        self.decay_rate = decay_rate
        self.cases: Dict[str, CaseRecord] = {}

    def add_case(self, case: CaseRecord):
        """
        添加新案例

        Args:
            case: 案例记录
        """
        self.cases[case.case_id] = case

        # 如果超过最大容量，触发遗忘
        if len(self.cases) > self.max_cases:
            self.forget_low_confidence_cases()

    def update_weight(self, case_id: str, success: bool):
        """
        更新案例权重

        Args:
            case_id: 案例ID
            success: 是否成功引导修正

        规则：
        - 成功 → confidence_score += 0.1
        - 失败 → confidence_score -= 0.1
        """
        if case_id not in self.cases:
            return

        case = self.cases[case_id]

        if success:
            case.confidence_score = min(1.0, case.confidence_score + 0.1)
            case.success_count += 1
        else:
            case.confidence_score = max(0.0, case.confidence_score - 0.1)
            case.failure_count += 1

        case.last_seen = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def forget_low_confidence_cases(self):
        """
        遗忘低置信度案例

        规则：
        1. 删除 confidence_score < min_confidence 的案例
        2. 如果删除后仍超过容量，删除置信度最低的案例
        """
        # 删除低置信度案例
        to_remove = [
            case_id for case_id, case in self.cases.items()
            if case.confidence_score < self.min_confidence
        ]
        for case_id in to_remove:
            del self.cases[case_id]
            print(f"[Active Forgetting] Forgot case {case_id} (low confidence)")

        # 如果仍超过容量，删除置信度最低的
        if len(self.cases) > self.max_cases:
            sorted_cases = sorted(
                self.cases.items(),
                key=lambda x: x[1].confidence_score
            )
            num_to_remove = len(self.cases) - self.max_cases
            for case_id, _ in sorted_cases[:num_to_remove]:
                del self.cases[case_id]
                print(f"[Active Forgetting] Forgot case {case_id} (capacity limit)")

    def decay_unused_cases(self, days: int = 7):
        """
        衰减未使用的案例权重

        Args:
            days: 多少天未使用视为"未使用"

        规则：
        - 对超过 days 天未使用的案例，confidence_score -= decay_rate
        """
        from datetime import datetime, timedelta

        threshold = datetime.now() - timedelta(days=days)
        threshold_str = threshold.strftime('%Y-%m-%d')

        for case_id, case in self.cases.items():
            if case.last_seen < threshold_str:
                case.confidence_score = max(
                    0.0,
                    case.confidence_score - self.decay_rate
                )
                print(f"[Active Forgetting] Decayed case {case_id} (unused)")

    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        """获取案例"""
        return self.cases.get(case_id)

    def get_top_cases(self, k: int = 10) -> List[CaseRecord]:
        """获取置信度最高的 k 个案例"""
        sorted_cases = sorted(
            self.cases.values(),
            key=lambda x: x.confidence_score,
            reverse=True
        )
        return sorted_cases[:k]

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.cases:
            return {
                'total_cases': 0,
                'avg_confidence': 0.0,
                'high_confidence_cases': 0,
                'low_confidence_cases': 0
            }

        confidences = [case.confidence_score for case in self.cases.values()]
        return {
            'total_cases': len(self.cases),
            'avg_confidence': sum(confidences) / len(confidences),
            'high_confidence_cases': sum(1 for c in confidences if c >= 0.7),
            'low_confidence_cases': sum(1 for c in confidences if c < 0.3),
            'max_confidence': max(confidences),
            'min_confidence': min(confidences)
        }
```

---

## 记忆演化管理器

### MemoryEvolutionManager 类

**文件**：`agents/memory_integration.py`

```python
class MemoryEvolutionManager:
    """记忆演化管理器"""

    def __init__(
        self,
        curator: CuratorAgent,
        forgetting_manager: ActiveForgettingManager,
        consolidation_interval: int = 100
    ):
        """
        初始化记忆演化管理器

        Args:
            curator: Curator 智能体
            forgetting_manager: 主动遗忘管理器
            consolidation_interval: Consolidation 触发间隔（处理多少案例后触发）
        """
        self.curator = curator
        self.forgetting_manager = forgetting_manager
        self.consolidation_interval = consolidation_interval
        self.processed_cases = 0

    def process_case(
        self,
        sample: Dict[str, Any],
        error_route: str,
        success: bool
    ) -> Dict[str, Any]:
        """
        处理一个案例，更新记忆

        Args:
            sample: 样本
            error_route: 错误路由
            success: 是否成功引导修正

        Returns:
            处理结果
        """
        # 1. Curator 生成 Blueprint
        blueprint = self.curator._generate_blueprint(sample)

        # 2. 创建或更新案例记录
        case_id = sample.get('id', 'unknown')
        case = self.forgetting_manager.get_case(case_id)

        if case:
            # 更新现有案例
            self.forgetting_manager.update_weight(case_id, success)
        else:
            # 创建新案例
            case = CaseRecord(
                case_id=case_id,
                error_route=error_route,
                blueprint=blueprint,
                confidence_score=0.5 if success else 0.4,
                success_count=1 if success else 0,
                failure_count=0 if success else 1,
                last_seen=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            self.forgetting_manager.add_case(case)

        # 3. 更新错误树
        self.curator._update_error_tree(error_route, blueprint, success)

        # 4. 检查是否触发 Consolidation
        self.processed_cases += 1
        if self.processed_cases % self.consolidation_interval == 0:
            self.consolidate_memory()

        return {
            'case_id': case_id,
            'blueprint': blueprint,
            'confidence_score': case.confidence_score,
            'action': 'updated' if case else 'created'
        }

    def consolidate_memory(self):
        """
        巩固记忆（Consolidation）

        将相似的 Blueprint 合并为更通用的知识
        """
        print(f"[Memory Evolution] Triggering consolidation (processed {self.processed_cases} cases)")

        # 1. 按错误路由分组
        groups = {}
        for case in self.forgetting_manager.cases.values():
            route = case.error_route
            if route not in groups:
                groups[route] = []
            groups[route].append(case)

        # 2. 对每个组进行 Consolidation
        for error_route, cases in groups.items():
            if len(cases) >= 3:  # 至少3个案例才进行 Consolidation
                consolidated_blueprint = self._consolidate_blueprints(
                    [case.blueprint for case in cases]
                )

                # 更新错误树的 Blueprint
                self.curator._update_blueprint_in_tree(
                    error_route,
                    consolidated_blueprint
                )

                print(f"[Memory Evolution] Consolidated {len(cases)} cases for {error_route}")

        # 3. 衰减未使用的案例
        self.forgetting_manager.decay_unused_cases(days=7)

        # 4. 遗忘低置信度案例
        self.forgetting_manager.forget_low_confidence_cases()

    def _consolidate_blueprints(self, blueprints: List[str]) -> str:
        """
        将多个 Blueprint 合并为一个

        Args:
            blueprints: Blueprint 列表

        Returns:
            合并后的 Blueprint
        """
        # 使用 LLM 进行合并
        prompt = f"""请将以下 {len(blueprints)} 个错误模式摘要合并为一个更通用的错误模式：

{chr(10).join(f'{i+1}. {bp}' for i, bp in enumerate(blueprints))}

要求：
1. 提取共同的错误特征
2. 保留关键的错误描述
3. 生成一个简洁、通用的错误模式摘要

输出格式：
Blueprint: [合并后的错误模式摘要]
"""

        response = self.curator.llm.generate(
            prompt,
            options=self.curator.llm.get_model_options(
                temperature=0.0,
                per_example_max_decode_steps=200
            )
        )

        # 解析响应
        if 'Blueprint:' in response:
            return response.split('Blueprint:')[1].strip()
        else:
            return blueprints[0]  # 如果解析失败，返回第一个
```

---

## 关键依赖与配置

### 依赖项

```python
# 内部依赖
from agents import CuratorAgent

# 外部依赖
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
```

### 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_cases` | 1000 | 最大案例数 |
| `min_confidence` | 0.3 | 最低置信度阈值 |
| `decay_rate` | 0.05 | 衰减率 |
| `consolidation_interval` | 100 | Consolidation 触发间隔 |
| `success_increment` | 0.1 | 成功时权重增量 |
| `failure_decrement` | 0.1 | 失败时权重减量 |

---

## 数据流与处理流程

### 记忆演化流程

```
新错误案例
  ↓
Curator 生成 Blueprint
  ↓
创建/更新 CaseRecord
  ├── case_id
  ├── error_route
  ├── blueprint
  ├── confidence_score
  ├── success_count
  ├── failure_count
  └── last_seen
  ↓
更新错误树
  ├── 添加示例到对应节点
  ├── 更新 Blueprint
  └── 更新 confidence_score
  ↓
检查触发条件
  ├── 是否达到 consolidation_interval？
  └── 是否超过 max_cases？
  ↓ (满足条件)
Consolidation
  ├── 按错误路由分组
  ├── 合并相似 Blueprint
  ├── 衰减未使用案例
  └── 遗忘低置信度案例
  ↓
输出统计信息
```

---

## 测试与质量

### 当前状态

⚠️ **未发现系统化的测试文件**

### 建议的测试

1. **案例记录测试**
   ```python
   # tests/test_case_record.py
   def test_case_record_creation():
       case = CaseRecord(
           case_id='test_001',
           error_route='select_row_errors/condition_error',
           blueprint='测试 Blueprint',
           confidence_score=0.5,
           success_count=0,
           failure_count=0,
           last_seen='2026-04-16'
       )
       assert case.case_id == 'test_001'
       assert case.total_usage == 0
       assert case.success_rate == 0.0
   ```

2. **主动遗忘测试**
   ```python
   # tests/test_active_forgetting.py
   def test_forget_low_confidence():
       manager = ActiveForgettingManager(
           max_cases=10,
           min_confidence=0.3
       )

       # 添加高置信度案例
       for i in range(5):
           manager.add_case(CaseRecord(
               case_id=f'high_{i}',
               error_route='test',
               blueprint='Test',
               confidence_score=0.8,
               success_count=1,
               failure_count=0,
               last_seen='2026-04-16'
           ))

       # 添加低置信度案例
       for i in range(10):
           manager.add_case(CaseRecord(
               case_id=f'low_{i}',
               error_route='test',
               blueprint='Test',
               confidence_score=0.2,
               success_count=0,
               failure_count=1,
               last_seen='2026-04-16'
           ))

       # 触发遗忘
       manager.forget_low_confidence_cases()

       # 验证：只保留高置信度案例
       assert len(manager.cases) == 5
       assert all(c.confidence_score >= 0.3 for c in manager.cases.values())
   ```

3. **Consolidation 测试**
   ```python
   # tests/test_consolidation.py
   def test_consolidate_blueprints():
       manager = MemoryEvolutionManager(
           curator=curator,
           forgetting_manager=forgetting_manager,
           consolidation_interval=5
       )

       # 添加多个相似案例
       for i in range(5):
           manager.process_case(
               sample=create_test_sample(),
               error_route='select_row_errors/condition_error',
               success=True
           )

       # 验证：触发 Consolidation
       assert manager.processed_cases == 5
       # 验证：Blueprint 已合并
       # (需要检查错误树中的 Blueprint)
   ```

---

## 常见问题 (FAQ)

### Q1: 主动遗忘的触发条件是什么？

**A**：
1. **容量触发**：当案例数超过 `max_cases` 时
2. **定期触发**：通过 `decay_unused_cases()` 定期衰减未使用的案例
3. **低置信度触发**：删除 `confidence_score < min_confidence` 的案例

### Q2: 如何平衡记忆容量和质量？

**A**：
- **调整 `max_cases`**：增加容量以保留更多案例
- **调整 `min_confidence`**：提高阈值以保留更高质量的案例
- **调整 `decay_rate`**：加快衰减以更快淘汰低质量案例
- **调整 `consolidation_interval`**：更频繁地进行 Consolidation

### Q3: Consolidation 的质量如何保证？

**A**：
- **最少案例数**：至少 3 个相似案例才进行 Consolidation
- **LLM 生成**：使用 LLM 合并 Blueprint，保留关键信息
- **人工审核**（可选）：对重要的 Blueprint 进行人工审核
- **反馈循环**：根据 Consolidation 后的效果调整参数

### Q4: 如何评估记忆系统的效果？

**A**：
1. **覆盖率**：错误树是否覆盖了大部分错误类型？
2. **准确性**：高置信度案例是否真的有效？
3. **检索效率**：Few-shot 检索是否返回了相关案例？
4. **修正成功率**：基于记忆的修正是否提高了准确率？

### Q5: 记忆系统是否会过度拟合？

**A**：
- **风险**：如果记忆库过于特定于某些错误模式，可能导致对新错误的泛化能力下降
- **缓解**：
  - 使用 Consolidation 生成更通用的 Blueprint
  - 定期遗忘低质量案例
  - 保持一定的随机性（如偶尔随机选择而非总是选择最高置信度的案例）

---

## 相关文件清单

### 核心文件

- `memory/__init__.py` - 模块导出
- `agents/active_forgetting.py` - 主动遗忘管理器
- `agents/memory_integration.py` - 记忆演化管理器
- `agents/curator_agent.py` - Curator 智能体

### 依赖文件

- `critic/TableQA/tools/few_shot_critic.json` - 错误树
- `critic/TableQA/tools/update_tree.py` - 树更新逻辑

---

**下一步建议**：

1. 实现 Consolidation 的完整逻辑
2. 建立记忆质量评估指标
3. 优化权重更新策略
4. 添加记忆系统的可视化工具
5. 实现记忆导出/导入功能
