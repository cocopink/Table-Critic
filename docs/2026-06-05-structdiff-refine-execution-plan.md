# StructDiff-Refine Accuracy Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前 Refine 从全局重诊断升级为 operation-level evidence 驱动的局部诊断、候选修复与验证选择，以提升最终 post-Refine accuracy，并控制无效 Refine 成本。

**Architecture:** 先在现有 Controller/Refine 链路旁路增加纯函数 trace/evidence/localizer，再用 feature flag 接入 Diff-Critic。局部修复和 Best-of-N 只在证据链路通过 pilot 验证后加入，任何低置信路径都回退到当前 full Refine。

**Tech Stack:** Python, pytest, pickle result files, current `critic.TableQA.tools`, current `refine.TableQA.utils`, current LLM wrapper and token logging.

---

## 0. 执行原则

- 准确率优先：任何 cost-saving 机制都必须证明不降低 final accuracy。
- 增量接入：先做诊断增强，再做局部修复，最后做 adaptive routing。
- 软证据优先：evidence 只能作为 prompt/verifier 信号，不能硬删除表格内容。
- 可回退：所有新路径都必须保留 existing full Controller fallback。
- QA 先行：先只实现 TableQA/WikiTQ；TableFV 在 QA 结果稳定后镜像。
- 不包含 git commit：当前计划只定义实现与验证步骤，不安排分支或提交操作。

---

## 1. 当前可复用切入点

### 已有能力

- `critic/TableQA/tools/get_info.py:get_table_log()` 已能重放 chain，并返回 `table_log, thought_log`。
- `refine/TableQA/utils/verifier.py:verify_chain()` 已能做 step-level deterministic verification。
- `refine/TableQA/utils/router.py` 已有 SKIP/LITE/FULL 路由雏形。
- `refine/TableQA/utils/controller.py:controller_main_loop()` 是 controller mode 的主入口。
- `critic/TableQA/tools/multiprocess.py:critic_exec_one_sample()` 是 Critic prompt 的集中入口。
- `refine/TableQA/utils/chain.py:dynamic_chain_exec_one_sample()` 是 chain-level repair 的当前实现。
- `refine/TableQA/operations/final_query.py:simple_query_with_critic()` 是 final query repair 的当前实现。

### 主要缺口

- 当前 Critic 看到的是原始表、reasoning steps 和最终 sub-table，不稳定看到每一步 before/after diff。
- `verify_chain()` 输出偏 verdict，不包含 compact prompt evidence pack。
- `return_incorrect_max_step()` 依赖 LLM 结论，缺少 deterministic suspicious step 排序。
- 当前 repair 是全局或后缀重跑，没有候选生成、候选评分、低置信 fallback 的统一接口。

---

## 2. 文件结构

### 新增文件

- `refine/TableQA/utils/operation_trace.py`
  - 负责把 `get_table_log()` 转成稳定、可测试、JSON 友好的 operation trace。
- `refine/TableQA/utils/evidence_pack.py`
  - 负责把 trace step 转成 row/column/sort/group/answer evidence。
- `refine/TableQA/utils/step_localizer.py`
  - 负责融合 verifier 与 evidence，给出最可疑 step。
- `refine/TableQA/utils/diff_bundle.py`
  - 负责把 trace、evidence、verification、localization 打包为 Critic 可消费对象。
- `refine/TableQA/utils/local_repair.py`
  - Phase 2 新增，负责局部修复候选、suffix replay、fallback 决策。
- `refine/TableQA/utils/candidate_ranker.py`
  - Phase 3 新增，负责 Best-of-N 候选评分与选择。
- `scripts/build_refine_pilot_set.py`
  - 从 thought/refine 结果中构建固定 pilot slice。
- `scripts/summarize_refine_experiment.py`
  - 汇总 accuracy、wrong-case correction、correct-case regression、token/API cost。
- `tests/test_operation_trace.py`
- `tests/test_evidence_pack.py`
- `tests/test_step_localizer.py`
- `tests/test_diff_bundle.py`
- `tests/test_local_repair.py`
- `tests/test_candidate_ranker.py`

### 修改文件

- `critic/TableQA/tools/get_info.py`
  - 增加 `get_cot_for_critic_diff()`。
- `critic/TableQA/tools/__init__.py`
  - 导出 `get_cot_for_critic_diff()`。
- `critic/TableQA/tools/multiprocess.py`
  - 给 `critic_exec_one_sample()` 增加 `use_diff_critic` 与 `diff_bundle` 参数。
- `refine/TableQA/utils/controller.py`
  - 给 `ActionExecutor` 和 `controller_main_loop()` 增加 diff-critic feature flag。
- `refine/TableQA/main_tree_based.py`
  - 增加 CLI 参数：`use_diff_critic`, `diff_critic_mode`, `candidate_n`, `local_repair_min_score`。
- `refine/TableQA/utils/router.py`
  - Phase 4 增加 evidence-aware routing variant。
- `tests/test_verifier.py`
  - 只在必要时补充 verifier 与 evidence 的集成断言。

---

## 3. 里程碑与退出标准

### M0: Baseline 固化

目标：固定评估 slice 与指标脚本，避免后续结果不可比。

退出标准：

- 能在固定 100/300 sample pilot 上复现实验。
- 能输出 accuracy、token usage、route distribution。
- 不改变现有 pipeline 行为。

### M1: Evidence-only Diff-Critic

目标：只增强 Critic prompt，不改变 repair 执行。

退出标准：

- `pytest` 新增纯函数测试通过。
- `use_diff_critic=False` 时输出与当前逻辑一致。
- 100-sample pilot 上 final accuracy 不低于 baseline。
- token 增幅不超过 10%，如果超过，需要压缩 evidence prompt。

### M2: Local Repair

目标：基于 localized step 只修复错误 operation 或 final query。

退出标准：

- 错误样本 correction rate 高于 current full Controller。
- 正确样本 regression rate 不高于 current full Controller。
- 低置信或 repair 后 Judge 仍错时回退 full Controller。

### M3: Best-of-N + Verifier Ranking

目标：在局部修复上生成多个候选，用 deterministic verifier 和 LLM Judge/score 选最终答案。

退出标准：

- hard subset 上 accuracy 高于 M2。
- 平均 API calls 不超过 full Controller 的 1.2 倍。
- 候选命中率与 ranker 选择率均可统计。

### M4: Adaptive Routing

目标：把高成本路径集中到高风险样本。

退出标准：

- full WikiTQ final accuracy 高于 baseline。
- Refine 总 token/API cost 相比 full Controller 降低 20% 以上。
- SKIP/LITE 路由的 regression case 可追踪。

---

## 4. Task 1: 固化 Baseline 与 Pilot Slice

**Files:**

- Create: `scripts/build_refine_pilot_set.py`
- Create: `scripts/summarize_refine_experiment.py`
- Test: 不需要 pytest；通过 CLI smoke test 验证。

- [ ] **Step 1: 创建 pilot set 构建脚本**

脚本职责：

- 输入 current thought `final_result.pkl`。
- 可选输入 baseline refine `final_result.pkl`。
- 输出固定 index 列表 `pilot_indices.json`。
- 优先包含 baseline wrong cases，其次包含 correct cases，用于同时观察 correction 和 regression。

核心接口：

```python
def build_pilot_indices(thought_samples, baseline_samples=None, size=100, seed=42):
    wrong_indices = []
    correct_indices = []
    for idx, sample in enumerate(thought_samples):
        if sample is None:
            continue
        if baseline_samples:
            baseline = baseline_samples[idx]
            is_correct = "[Correct]" in str(baseline.get("judge", ""))
        else:
            is_correct = "[Correct]" in str(sample.get("judge", ""))
        if is_correct:
            correct_indices.append(idx)
        else:
            wrong_indices.append(idx)
    return (wrong_indices + correct_indices)[:size]
```

- [ ] **Step 2: 创建实验汇总脚本**

脚本职责：

- 输入 baseline result pkl、新实验 result pkl、token usage json。
- 输出 markdown/csv 汇总。
- 统计字段固定为 `accuracy`, `changed_count`, `baseline_correct_to_wrong`, `baseline_wrong_to_correct`, `api_calls`, `input_tokens`, `output_tokens`, `total_tokens`。

核心接口：

```python
def summarize_pairwise(base_samples, exp_samples):
    base_correct = [is_correct(s) for s in base_samples]
    exp_correct = [is_correct(s) for s in exp_samples]
    return {
        "baseline_correct": sum(base_correct),
        "experiment_correct": sum(exp_correct),
        "baseline_wrong_to_correct": sum((not b) and e for b, e in zip(base_correct, exp_correct)),
        "baseline_correct_to_wrong": sum(b and (not e) for b, e in zip(base_correct, exp_correct)),
        "changed_count": sum(b != e for b, e in zip(base_correct, exp_correct)),
    }
```

- [ ] **Step 3: smoke test pilot 构建**

Run:

```bash
python "scripts/build_refine_pilot_set.py" \
  --thought-pkl "results/new/thought/wikitq/qwen3:14b/final_result.pkl" \
  --output "results/pilot/wikitq/pilot_indices_100.json" \
  --size 100
```

Expected:

```text
Saved 100 indices to results/pilot/wikitq/pilot_indices_100.json
```

---

## 5. Task 2: Operation Trace Builder

**Files:**

- Create: `refine/TableQA/utils/operation_trace.py`
- Test: `tests/test_operation_trace.py`

- [ ] **Step 1: 写 failing tests**

测试覆盖：

- 跳过 `skip` action。
- step number 与可见 operation 对齐。
- 保存 before/after table。
- query step 保留 answer。

测试样例结构：

```python
def test_build_operation_trace_keeps_before_after_tables(monkeypatch):
    sample = {
        "id": "case-1",
        "statement": "Who has score 90?",
        "table_text": [["name", "score"], ["Alice", "90"], ["Bob", "80"]],
        "chain": [
            {"operation_name": "select_row", "parameter_and_conf": [("row 1", 0.9)], "thought": "keep Alice"},
            {"operation_name": "simple_query", "parameter_and_conf": [("Alice", 0.9)], "thought": "answer"},
        ],
    }
    fake_log = [
        {"table_text": sample["table_text"], "act_chain": []},
        {"table_text": [["name", "score"], ["Alice", "90"]], "act_chain": ["f_select_row(row 1)"]},
        {"table_text": [["name", "score"], ["Alice", "90"]], "act_chain": ["f_select_row(row 1)", "simple_query()"], "cotable_result": "Alice"},
    ]
    monkeypatch.setattr("refine.TableQA.utils.operation_trace._load_table_log", lambda s: (fake_log, ["", "keep Alice", "answer"]))
    trace = build_operation_trace(sample)
    assert trace.sample_id == "case-1"
    assert len(trace.steps) == 2
    assert trace.steps[0].before_table == sample["table_text"]
    assert trace.steps[0].after_table == [["name", "score"], ["Alice", "90"]]
    assert trace.steps[1].answer == "Alice"
```

- [ ] **Step 2: 实现最小模块**

核心类型：

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Table = List[List[Any]]

@dataclass
class TraceStep:
    step_num: int
    chain_idx: int
    operation_name: str
    operation: Dict[str, Any]
    action: str
    thought: str
    before_table: Table
    after_table: Table
    before_info: Dict[str, Any] = field(default_factory=dict)
    after_info: Dict[str, Any] = field(default_factory=dict)
    answer: Optional[str] = None

@dataclass
class OperationTrace:
    sample_id: Any
    question: str
    original_table: Table
    steps: List[TraceStep]
```

核心函数：

```python
def _load_table_log(sample):
    from critic.TableQA.tools.get_info import get_table_log
    return get_table_log(sample)

def build_operation_trace(sample):
    table_log, thought_log = _load_table_log(sample)
    steps = []
    visible_step_num = 0
    for chain_idx, operation in enumerate(sample.get("chain", [])):
        if chain_idx + 1 >= len(table_log):
            break
        post_info = table_log[chain_idx + 1]
        action = _last_visible_action(post_info)
        if not action or "skip" in action:
            continue
        visible_step_num += 1
        answer = post_info.get("cotable_result") if "query" in operation.get("operation_name", "") else None
        steps.append(TraceStep(
            step_num=visible_step_num,
            chain_idx=chain_idx,
            operation_name=operation.get("operation_name", ""),
            operation=operation,
            action=str(action),
            thought=thought_log[chain_idx + 1] if chain_idx + 1 < len(thought_log) else operation.get("thought", ""),
            before_table=table_log[chain_idx].get("table_text", []),
            after_table=post_info.get("table_text", []),
            before_info=table_log[chain_idx],
            after_info=post_info,
            answer=str(answer) if answer is not None else None,
        ))
    return OperationTrace(
        sample_id=sample.get("id"),
        question=sample.get("statement", ""),
        original_table=sample.get("table_text", []),
        steps=steps,
    )
```

- [ ] **Step 3: 运行测试**

Run:

```bash
pytest "tests/test_operation_trace.py" -q
```

Expected:

```text
passed
```

---

## 6. Task 3: Evidence Pack Builder

**Files:**

- Create: `refine/TableQA/utils/evidence_pack.py`
- Test: `tests/test_evidence_pack.py`

- [ ] **Step 1: 写 failing tests**

测试覆盖：

- `select_row` 输出 kept/removed row ids。
- `select_column` 输出 kept/dropped headers。
- `sort_column` 输出排序列、数值序列、是否升降序。
- `simple_query` 输出 answer 是否出现在 final table。
- warning 只是 evidence，不直接修改 sample。

核心测试：

```python
def test_select_column_evidence_records_dropped_relevant_header():
    step = TraceStep(
        step_num=1,
        chain_idx=0,
        operation_name="select_column",
        operation={"operation_name": "select_column"},
        action="f_select_column(name)",
        thought="keep name",
        before_table=[["name", "score"], ["Alice", "90"]],
        after_table=[["name"], ["Alice"]],
    )
    evidence = build_step_evidence(step, question="What is Alice's score?")
    assert evidence.kind == "select_column"
    assert evidence.column_diff["kept_headers"] == ["name"]
    assert evidence.column_diff["dropped_headers"] == ["score"]
    assert any("score" in warning.lower() for warning in evidence.warnings)
```

- [ ] **Step 2: 实现 evidence 类型**

```python
@dataclass
class StepEvidence:
    step_num: int
    operation_name: str
    kind: str
    summary: str
    row_diff: Dict[str, Any] = field(default_factory=dict)
    column_diff: Dict[str, Any] = field(default_factory=dict)
    sort_evidence: Dict[str, Any] = field(default_factory=dict)
    group_evidence: Dict[str, Any] = field(default_factory=dict)
    answer_evidence: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_prompt_block(self) -> str:
        lines = [f"Step {self.step_num} ({self.operation_name}) evidence:", f"- Summary: {self.summary}"]
        for warning in self.warnings:
            lines.append(f"- Warning: {warning}")
        for name, value in [
            ("row_diff", self.row_diff),
            ("column_diff", self.column_diff),
            ("sort_evidence", self.sort_evidence),
            ("group_evidence", self.group_evidence),
            ("answer_evidence", self.answer_evidence),
        ]:
            if value:
                lines.append(f"- {name}: {value}")
        return "\n".join(lines)
```

- [ ] **Step 3: 实现 operation-specific evidence**

实现函数：

- `build_step_evidence(step, question)`
- `_build_row_diff(step)`
- `_build_column_diff(step, question)`
- `_build_sort_evidence(step)`
- `_build_group_evidence(step)`
- `_build_answer_evidence(step)`
- `build_evidence_pack(trace)`

实现约束：

- row diff 通过 exact row tuple 匹配，匹配不到时只输出 counts，不猜测语义。
- column diff 只比较 header string。
- sort evidence 优先复用 `verifier._parse_sort_column()` 和 `verifier._safe_float()`。
- question keywords 复用 `verifier._extract_question_keywords()`。
- evidence prompt block 单 step 控制在 1000 字符内。

- [ ] **Step 4: 运行测试**

Run:

```bash
pytest "tests/test_evidence_pack.py" -q
```

Expected:

```text
passed
```

---

## 7. Task 4: Step Localizer

**Files:**

- Create: `refine/TableQA/utils/step_localizer.py`
- Test: `tests/test_step_localizer.py`

- [ ] **Step 1: 写 failing tests**

测试覆盖：

- verifier FAIL 优先。
- evidence warning 在没有 verifier FAIL 时生效。
- final query answer 不在 table 时定位 query step。
- 没有强信号时返回低置信，并允许 fallback。

核心测试：

```python
def test_localizer_prefers_verifier_failed_step():
    report = VerificationReport(
        steps=[
            StepVerification(1, "select_row", "f_select_row(row 1)", Verdict.PASS, [], "ok"),
            StepVerification(2, "sort_column", "f_sort_column(score)", Verdict.FAIL, [], "bad sort"),
        ],
        total_steps=2,
        failed_steps=[2],
    )
    result = localize_suspicious_step(evidence_pack=[], verification_report=report)
    assert result.step_num == 2
    assert result.confidence >= 0.8
```

- [ ] **Step 2: 实现 localizer**

核心类型：

```python
@dataclass
class LocalizationResult:
    step_num: Optional[int]
    operation_name: str
    confidence: float
    reason: str
    source: str
```

打分规则：

- verifier verdict FAIL: `+10`
- verifier verdict WARN: `+3`
- evidence warning 包含 `dropped relevant`: `+4`
- evidence warning 包含 `answer not found`: `+4`
- evidence warning 包含 `sort`: `+3`
- 越早的高分 step 优先，因为后续错误可能是传播结果。
- score >= 10: confidence 0.9
- score >= 5: confidence 0.7
- score >= 3: confidence 0.55
- score < 3: confidence 0.0, step_num None

- [ ] **Step 3: 运行测试**

Run:

```bash
pytest "tests/test_step_localizer.py" -q
```

Expected:

```text
passed
```

---

## 8. Task 5: Diff Bundle

**Files:**

- Create: `refine/TableQA/utils/diff_bundle.py`
- Test: `tests/test_diff_bundle.py`

- [ ] **Step 1: 写集成测试**

测试目标：

- 输入 sample 后能生成 trace、verification、evidence、localization。
- `to_prompt_block()` 只输出 suspected step 附近 evidence，不输出整条长 trace。
- bundle 失败时返回可解释 error，不影响 fallback。

核心接口：

```python
bundle = build_diff_bundle(sample)
assert bundle.trace.steps
assert bundle.localization.step_num is not None
assert "Step" in bundle.to_prompt_block()
```

- [ ] **Step 2: 实现 bundle**

核心类型：

```python
@dataclass
class DiffBundle:
    trace: OperationTrace
    evidence_pack: List[StepEvidence]
    verification_report: VerificationReport
    localization: LocalizationResult

    def suspected_evidence(self) -> Optional[StepEvidence]:
        if self.localization.step_num is None:
            return None
        return next((e for e in self.evidence_pack if e.step_num == self.localization.step_num), None)

    def to_prompt_block(self) -> str:
        evidence = self.suspected_evidence()
        if evidence is None:
            return "[Operation Diff Evidence]\nNo high-confidence suspicious step was found.\n[End Operation Diff Evidence]"
        return "\n".join([
            "[Operation Diff Evidence]",
            f"Suspicious step: {self.localization.step_num}",
            f"Localization confidence: {self.localization.confidence:.2f}",
            f"Localization reason: {self.localization.reason}",
            evidence.to_prompt_block(),
            "[End Operation Diff Evidence]",
        ])
```

- [ ] **Step 3: 运行测试**

Run:

```bash
pytest "tests/test_diff_bundle.py" -q
```

Expected:

```text
passed
```

---

## 9. Task 6: Diff-Critic Prompt 接入

**Files:**

- Modify: `critic/TableQA/tools/get_info.py`
- Modify: `critic/TableQA/tools/__init__.py`
- Modify: `critic/TableQA/tools/multiprocess.py`
- Test: `tests/test_diff_bundle.py` 增加 prompt 断言，或新增 `tests/test_diff_critic_prompt.py`

- [ ] **Step 1: 增加 `get_cot_for_critic_diff()`**

设计：

- 保留 `get_cot_for_critic()` 的输出格式，避免破坏 Critic parser。
- 在 `Reasoning Steps` 后追加 `[Operation Diff Evidence]`。
- 明确要求 Critic 优先检查 suspected step，但如果证据不足可以指出其他 step。
- 仍然输出 `Conclusion: [Incorrect] Step <NUM>`。

核心接口：

```python
def get_cot_for_critic_diff(sample, diff_bundle=None, verification_report=None):
    cot, max_step = get_cot_for_critic(sample, verification_report=verification_report)
    if diff_bundle is None:
        return cot, max_step
    marker = "Critique:"
    evidence = diff_bundle.to_prompt_block()
    if marker in cot:
        cot = cot.replace(marker, evidence + "\n\nCritique:")
    else:
        cot += "\n\n" + evidence + "\n\nCritique:"
    return cot, max_step
```

- [ ] **Step 2: 导出新函数**

`critic/TableQA/tools/__init__.py` 增加：

```python
from .get_info import get_cot_for_critic_diff
```

- [ ] **Step 3: 修改 `critic_exec_one_sample()`**

新增参数：

```python
def critic_exec_one_sample(
    sample,
    error_route,
    llm,
    llm_options=None,
    blueprint_only=False,
    pre_retrieved_few_shot=None,
    use_verifier=False,
    use_diff_critic=False,
    diff_bundle=None,
):
```

调用逻辑：

```python
if use_diff_critic:
    from .get_info import get_cot_for_critic_diff
    cot, max_step = get_cot_for_critic_diff(
        critic_sample,
        diff_bundle=diff_bundle,
        verification_report=verification_report,
    )
else:
    cot, max_step = get_cot_for_critic(
        critic_sample,
        verification_report=verification_report,
    )
```

- [ ] **Step 4: Prompt 单测**

Run:

```bash
pytest "tests/test_diff_critic_prompt.py" -q
```

Expected:

```text
passed
```

---

## 10. Task 7: Controller Feature Flag 接入

**Files:**

- Modify: `refine/TableQA/utils/controller.py`
- Modify: `refine/TableQA/main_tree_based.py`
- Test: 用 fake LLM 或 monkeypatch 做 controller smoke test。

- [ ] **Step 1: 扩展 ActionExecutor**

新增参数：

```python
class ActionExecutor:
    def __init__(
        self,
        llm,
        llm_options,
        use_verifier=False,
        use_diff_critic=False,
        diff_critic_mode="diagnose_only",
    ):
        self.use_diff_critic = use_diff_critic
        self.diff_critic_mode = diff_critic_mode
```

- [ ] **Step 2: 在 DIAGNOSE action 中构建 diff bundle**

插入位置：`ActionExecutor.execute()` 的 `DIAGNOSE_BP/DIAGNOSE_FS` 分支，在调用 `critic_exec_one_sample()` 前。

核心逻辑：

```python
diff_bundle = None
if self.use_diff_critic:
    try:
        from refine.TableQA.utils.diff_bundle import build_diff_bundle
        diff_bundle = build_diff_bundle(state.sample)
        state.sample["_diff_localization"] = {
            "step_num": diff_bundle.localization.step_num,
            "confidence": diff_bundle.localization.confidence,
            "reason": diff_bundle.localization.reason,
        }
    except Exception as exc:
        print(f"[WARN] Diff bundle failed: {exc}", flush=True)
        diff_bundle = None
```

调用 Critic 时传参：

```python
critic_sample = critic_exec_one_sample(
    state.sample,
    error_route,
    llm=self.llm,
    llm_options=self.llm_options,
    blueprint_only=blueprint_only,
    pre_retrieved_few_shot=pre_retrieved_few_shot,
    use_verifier=self.use_verifier,
    use_diff_critic=self.use_diff_critic,
    diff_bundle=diff_bundle,
)
```

- [ ] **Step 3: 扩展 `controller_main_loop()` 参数**

新增参数：

```python
use_diff_critic: bool = False,
diff_critic_mode: str = "diagnose_only",
```

创建 executor：

```python
executor = ActionExecutor(
    llm,
    llm_options,
    use_verifier=use_verifier,
    use_diff_critic=use_diff_critic,
    diff_critic_mode=diff_critic_mode,
)
```

- [ ] **Step 4: 扩展 CLI**

`refine/TableQA/main_tree_based.py:main()` 增加：

```python
use_diff_critic: bool = False,
diff_critic_mode: str = "diagnose_only",
```

传入 controller：

```python
refined_sample = controller_main_loop(
    sample,
    llm=gpt_llm,
    llm_options=gpt_llm.get_model_options(...),
    max_iterations=2,
    cache_dir=cache_dir,
    sample_idx=idx,
    use_clarifier=use_clarifier,
    thought_results_dir=thought_results_dir,
    use_verifier=use_verifier,
    router_variant=router_variant or None,
    use_diff_critic=use_diff_critic,
    diff_critic_mode=diff_critic_mode,
)
```

- [ ] **Step 5: 回归测试**

Run:

```bash
pytest "tests/test_operation_trace.py" "tests/test_evidence_pack.py" "tests/test_step_localizer.py" "tests/test_diff_bundle.py" -q
```

Expected:

```text
passed
```

---

## 11. Task 8: M1 Pilot 实验

**Files:**

- Modify only if needed: `scripts/summarize_refine_experiment.py`

- [ ] **Step 1: 跑 baseline controller**

Run:

```bash
python "refine/TableQA/main_tree_based.py" \
  --model_name "qwen3:14b" \
  --first_n 100 \
  --n_proc 1 \
  --chunk_size 1 \
  --use_controller True \
  --use_verifier True \
  --use_diff_critic False
```

Expected:

```text
Accuracy: <baseline_acc>
Refine Stage Token Usage:
```

- [ ] **Step 2: 跑 Diff-Critic diagnose-only**

Run:

```bash
python "refine/TableQA/main_tree_based.py" \
  --model_name "qwen3:14b" \
  --first_n 100 \
  --n_proc 1 \
  --chunk_size 1 \
  --use_controller True \
  --use_verifier True \
  --use_diff_critic True \
  --diff_critic_mode "diagnose_only"
```

Expected:

```text
Accuracy: <diff_critic_acc>
Refine Stage Token Usage:
```

- [ ] **Step 3: 汇总比较**

Run:

```bash
python "scripts/summarize_refine_experiment.py" \
  --baseline-pkl "results/new/refine/wikitq/qwen3:14b/final_result.pkl" \
  --experiment-pkl "results/new/refine/wikitq/qwen3:14b/final_result.pkl" \
  --experiment-token-json "results/new/refine/wikitq/qwen3:14b/token_usage.json"
```

判定：

- 如果 final accuracy 高于 baseline，进入 M2。
- 如果 final accuracy 持平但 wrong-to-correct 增加且 correct-to-wrong 也增加，先分析 regression cases，再调整 evidence prompt。
- 如果 final accuracy 下降，保留 trace/evidence 模块，但不进入 local repair。

---

## 12. Task 9: Local Repair Executor

**Files:**

- Create: `refine/TableQA/utils/local_repair.py`
- Modify: `refine/TableQA/utils/controller.py`
- Test: `tests/test_local_repair.py`

- [ ] **Step 1: 定义 repair 数据结构**

```python
@dataclass
class RepairDecision:
    mode: str
    target_step: Optional[int]
    confidence: float
    reason: str

@dataclass
class RepairResult:
    sample: Dict[str, Any]
    decision: RepairDecision
    used_fallback: bool
    candidate_count: int = 1
```

支持 mode：

- `repair_final_query`
- `repair_chain_suffix`
- `fallback_full_refine`

- [ ] **Step 2: 实现 repair mode 选择**

规则：

- localization confidence < `0.7`: fallback。
- suspected operation 是 `simple_query`: `repair_final_query`。
- suspected operation in `select_row`, `select_column`, `sort_column`, `group_column`: `repair_chain_suffix`。
- suspected operation 是 `add_column`: Phase 2 先 fallback，因为 add_column 语义抽取风险高。

核心函数：

```python
def choose_repair_mode(diff_bundle, min_confidence=0.7):
    loc = diff_bundle.localization
    if loc.step_num is None or loc.confidence < min_confidence:
        return RepairDecision("fallback_full_refine", None, loc.confidence, loc.reason)
    evidence = diff_bundle.suspected_evidence()
    op_name = evidence.operation_name if evidence else ""
    if op_name == "simple_query":
        return RepairDecision("repair_final_query", loc.step_num, loc.confidence, loc.reason)
    if op_name in {"select_row", "select_column", "sort_column", "group_column"}:
        return RepairDecision("repair_chain_suffix", loc.step_num, loc.confidence, loc.reason)
    return RepairDecision("fallback_full_refine", loc.step_num, loc.confidence, f"Unsupported local repair op: {op_name}")
```

- [ ] **Step 3: 实现 final query local repair**

复用当前函数：

```python
def repair_final_query(sample, llm, llm_options):
    from refine.TableQA.utils.chain import get_table_info
    from refine.TableQA.operations.final_query import simple_query_with_critic
    wo_query_sample = copy.deepcopy(sample)
    if wo_query_sample.get("chain"):
        wo_query_sample["chain"] = wo_query_sample["chain"][:-1]
    table_info = get_table_info(wo_query_sample, skip_op=[], first_n_op=None)
    return simple_query_with_critic(sample, table_info, llm, llm_options=llm_options)
```

- [ ] **Step 4: 实现 chain suffix repair**

Phase 2 先复用 `dynamic_chain_exec_one_sample()`，不自行写 suffix replay。

```python
def repair_chain_suffix(sample, target_step, max_step, llm, llm_options):
    from refine.TableQA.utils.chain import dynamic_chain_exec_one_sample, get_table_info
    from refine.TableQA.operations.final_query import simple_query_cot_original
    repaired = dynamic_chain_exec_one_sample(
        sample,
        incorrect_step=target_step,
        max_step=max_step,
        llm=llm,
        llm_options=llm_options,
        strategy="top",
    )
    table_info = get_table_info(repaired, skip_op=[], first_n_op=None)
    return simple_query_cot_original(repaired, table_info, llm, llm_options=llm_options)
```

- [ ] **Step 5: 接入 controller**

只在 `diff_critic_mode == "local_repair"` 时启用。

流程：

- DIAGNOSE 后仍运行 Critic，得到 critique。
- REFINE action 前读取 `_diff_localization` 和 diff bundle。
- 如果 local repair 决策支持，则调用 `local_repair.repair_sample()`。
- repair 后必须 Judge。
- Judge incorrect 时 fallback 到 existing REFINE_CHAIN/REFINE_QUERY。

- [ ] **Step 6: 单测**

Run:

```bash
pytest "tests/test_local_repair.py" -q
```

Expected:

```text
passed
```

---

## 13. Task 10: Best-of-N Candidate Ranking

**Files:**

- Create: `refine/TableQA/utils/candidate_ranker.py`
- Modify: `refine/TableQA/utils/local_repair.py`
- Test: `tests/test_candidate_ranker.py`

- [ ] **Step 1: 定义候选结构**

```python
@dataclass
class RepairCandidate:
    candidate_id: int
    sample: Dict[str, Any]
    source: str
    verifier_failures: int
    answer_in_table: bool
    judge_correct: Optional[bool] = None
    llm_score: float = 0.0

@dataclass
class RankingResult:
    best: RepairCandidate
    candidates: List[RepairCandidate]
    reason: str
```

- [ ] **Step 2: 实现 deterministic score**

评分规则：

- Judge correct: `+100`
- verifier failures: 每个 `-10`
- answer in final table: `+5`
- answer non-empty: `+3`
- chain length 异常增长超过 2 step: `-3`
- 与原答案相同且原本 Judge incorrect: `-5`

```python
def score_candidate(candidate, original_answer):
    score = 0.0
    if candidate.judge_correct is True:
        score += 100
    score -= 10 * candidate.verifier_failures
    if candidate.answer_in_table:
        score += 5
    answer = extract_answer(candidate.sample)
    if answer:
        score += 3
    if answer and answer == original_answer:
        score -= 5
    candidate.llm_score = score
    return candidate
```

- [ ] **Step 3: 生成候选**

Phase 3 控制复杂度：

- `candidate_n=1` 等价于 Phase 2。
- `candidate_n=3` 时重复 local repair 3 次，使用不同 temperature 或 `n_sample`。
- 每个候选都必须跑 `verify_chain()`。
- 只对 localization confidence >= 0.8 的样本启用 Best-of-N。

- [ ] **Step 4: 单测**

Run:

```bash
pytest "tests/test_candidate_ranker.py" -q
```

Expected:

```text
passed
```

---

## 14. Task 11: Adaptive Routing v2

**Files:**

- Modify: `refine/TableQA/utils/router.py`
- Modify: `refine/TableQA/utils/controller.py`
- Test: `tests/test_router.py`

- [ ] **Step 1: 增加 evidence-aware route**

新增 variant 名称：`diff_v2`。

路由规则：

- Judge correct: `SKIP`。
- verifier FAIL 或 localization confidence >= 0.7: `LITE`，执行 Diff-Critic local repair。
- chain length >= 4 或包含 group/sort/add_column 且 localization confidence < 0.7: `FULL`。
- 小表、短 chain、无复杂 op: `LITE`。

- [ ] **Step 2: 输出 routing telemetry**

每个 sample 保存：

```python
sample["_route"] = route_result.decision.value
sample["_route_signals"] = route_result.signals
sample["_diff_localization"] = localization_dict
sample["_repair_mode"] = repair_decision.mode
sample["_used_fallback"] = repair_result.used_fallback
```

- [ ] **Step 3: 回归测试**

Run:

```bash
pytest "tests/test_router.py" "tests/test_local_repair.py" "tests/test_candidate_ranker.py" -q
```

Expected:

```text
passed
```

---

## 15. Task 12: 实验矩阵

### 必跑实验

| ID | 配置 | 目的 |
| --- | --- | --- |
| E0 | current full Controller | baseline |
| E1 | `use_verifier=True` | 当前 verifier contribution |
| E2 | `use_diff_critic=True`, `diagnose_only` | 测 diff evidence 是否改善 Critic |
| E3 | `local_repair`, `candidate_n=1` | 测局部修复 |
| E4 | `local_repair`, `candidate_n=3` | 测 Best-of-N 上限 |
| E5 | `router_variant=diff_v2`, `candidate_n=1` | 测成本控制 |
| E6 | `router_variant=diff_v2`, `candidate_n=3` | 测最终准确率与成本折中 |

### 指标

| Metric | Definition |
| --- | --- |
| final accuracy | `wikitq_match_func_for_samples(refine_list)` |
| wrong-to-correct | baseline wrong 且 experiment correct |
| correct-to-wrong | baseline correct 且 experiment wrong |
| correction rate | wrong-to-correct / baseline wrong |
| regression rate | correct-to-wrong / baseline correct |
| avg api calls | `token_usage.api_calls / sample_count` |
| avg tokens | `token_usage.total_tokens / sample_count` |
| fallback rate | `_used_fallback=True` 的比例 |
| route distribution | SKIP/LITE/FULL 占比 |

### 决策门槛

- E2 如果 accuracy 下降超过 0.3pp，不进入 E3，先压缩/修正 evidence prompt。
- E3 如果 correction rate 上升但 regression rate 也上升，增加 Judge fallback，不扩大到 full set。
- E4 如果 accuracy 提升小于 0.2pp 且 cost 增加超过 20%，Best-of-N 只保留给 hard subset。
- E5 如果 cost 降低但 accuracy 低于 E0，routing 不进入主实验。

---

## 16. 验证命令

### 单元测试

```bash
pytest "tests/test_operation_trace.py" \
  "tests/test_evidence_pack.py" \
  "tests/test_step_localizer.py" \
  "tests/test_diff_bundle.py" \
  "tests/test_local_repair.py" \
  "tests/test_candidate_ranker.py" -q
```

### 现有测试回归

```bash
pytest "tests/test_verifier.py" \
  "tests/test_column_norm.py" \
  "tests/test_header_tree.py" \
  "tests/test_table_analyzer.py" -q
```

### 100-sample smoke experiment

```bash
python "refine/TableQA/main_tree_based.py" \
  --model_name "qwen3:14b" \
  --first_n 100 \
  --n_proc 1 \
  --chunk_size 1 \
  --use_controller True \
  --use_verifier True \
  --use_diff_critic True \
  --diff_critic_mode "diagnose_only"
```

### full WikiTQ experiment

```bash
python "refine/TableQA/main_tree_based.py" \
  --model_name "qwen3:14b" \
  --first_n -1 \
  --n_proc 1 \
  --chunk_size 1 \
  --use_controller True \
  --use_verifier True \
  --use_diff_critic True \
  --diff_critic_mode "local_repair" \
  --router_variant "diff_v2"
```

---

## 17. 风险与处理

| Risk | Signal | Mitigation |
| --- | --- | --- |
| Diff prompt 太长 | token 增幅超过 10% | 只保留 suspected step evidence；row diff 只展示 id/count |
| localizer 错定位 | correct-to-wrong 增加 | confidence < 0.7 全部 fallback full Refine |
| local repair 破坏正确链 | regression rate 上升 | repair 后强制 Judge，错则回退 full Controller |
| Best-of-N 成本失控 | avg api calls 超过 baseline 1.2 倍 | 只对 hard subset 或 confidence >= 0.8 启用 |
| evidence false positive | warning 与人工分析不一致 | warning 不作为硬约束，只作为 Critic context |
| 与现有 imports 冲突 | `tools` 解析错误 | 新 helper 放 `refine/TableQA/utils`，critic 侧只延迟导入 |

---

## 18. 推荐执行顺序

1. 先完成 M0 到 M1，只做 evidence-only Diff-Critic。
2. 如果 E2 不低于 baseline，再做 M2 local repair。
3. 如果 M2 有准确率提升，再做 M3 Best-of-N。
4. 如果 M3 证明 hard subset 有收益，再做 M4 adaptive routing。
5. 不建议一开始同时做 local repair、Best-of-N 和 routing，否则无法定位收益来源。

---

## 19. 与现有设计文档关系

本执行计划落实 `docs/2026-06-05-structdiff-refine-design.md` 的推荐路线。重点不是替换 Stage 1 或 TableAnalyzer，而是利用已有 operation chain 的 before/after 状态，把 Refine 阶段改造成可诊断、可验证、可回退的调试流程。
