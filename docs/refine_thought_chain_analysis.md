# Table-Critic Refine阶段对第一阶段思维链的利用分析与改进方向

> 用于向老师汇报，2026-04-13

---

## 一、现有Refine阶段如何利用思维链

| 环节 | 所在模块 | 核心函数 | 输入内容 | 信息保留情况 |
|------|----------|----------|----------|-------------|
| **Critic诊断** | `critic/*/tools/get_info.py` | `get_cot_for_critic()` | 完整chain（每步的thought + action + 中间表快照） | **完整保留** |
| **Refine修正** | `refine/*/utils/chain.py` | `generate_prompt_for_critic_step()` | 截断后的action链 + 中间表 + critique文本 | **丢失thought** |

> **注意**: `generate_prompt_for_critic_step()` 虽然名字含 "critic"，但它位于 refine 模块，服务于 Refine 阶段。名字中的 "critic_step" 指的是"被Critic指出错误的步骤"，而非"给Critic使用的步骤"。

### 关键代码路径

1. **Critic读取** (`critic/*/tools/get_info.py` → `get_cot_for_critic()`):
   - 调用 `get_table_log()` 重放完整chain，同时返回 `table_log` 和 `thought_log`
   - Prompt包含每步的: `thought_log[idx]` + action + 中间表快照（第146行: `cot += f"Step{step+1}: {thought_log[idx]}\n"`）

2. **Refine读取** (`refine/*/utils/chain.py` → `generate_prompt_for_critic_step()`):
   - 调用 `get_critic_table_info()` 截断chain至incorrect_step-1（**就地修改 `sample['chain']`**，第149行）
   - 构建prompt时仅使用 `critic_act_chain_str`（action字符串拼接）和 `table_info["table_text"]`（中间表）
   - **原始thought完全不传递给Refine阶段的LLM**

3. **Refine执行** (`refine/*/utils/chain.py` → `dynamic_chain_exec_one_sample()`):
   - 第一步用 `generate_prompt_for_critic_step()` 生成参数
   - 后续步骤用 `generate_prompt_for_next_step()` 继续生成，同样不含原始thought
   - 整个Refine过程仅基于action历史和中间表状态，无原始推理上下文

---

## 二、现有方案的主要不足

| 问题 | 具体表现 | 影响 |
|------|----------|------|
| **Thought丢失** | Refine阶段看不到原始chain中每步的推理过程（thought字段）。注意：部分步骤（如add_column）的thought为N/A，但select_row、simple_query等步骤通常有完整推理文本 | LLM不知道原始"为什么这样做"，可能重复犯错 |
| **全量截断** | 从incorrect_step开始截断，丢弃后续所有步骤（即使后续步骤本身正确） | 丢失有效的后续推理，增加不必要的重新生成成本 |
| **Critic信息非结构化** | Critic输出为自然语言文本，Refine仅将其作为prompt的一部分 | 难以程序化地约束修正行为，修正策略完全依赖LLM自由发挥 |
| **无修正策略选择** | 不区分错误类型，一律从incorrect_step重新生成 | 对不同类型错误（计算错误/操作选错/理解偏差）缺乏针对性处理 |

---

## 三、可能的改进方向

### 方向1: 传递原始Thought上下文

- **做法**: Refine prompt中包含incorrect_step之前的thought + action + 中间表，而非仅action
- **预期收益**: LLM理解原始推理逻辑，避免重复相同错误思路
- **风险**: prompt长度增加，token消耗上升
- **状态**: 可直接实现，改动小

### 方向2: 增量修正替代全量截断

- **做法**: 仅替换incorrect_step，保留后续正确步骤；或由LLM判断哪些后续步骤可复用
- **预期收益**: 减少冗余生成，保留有效推理
- **风险**: 后续步骤依赖前面步骤的中间表状态，部分复用可能导致不一致
- **状态**: 需要中间表状态校验机制配合

### 方向3: 结构化Critic输出 + 修正策略路由

- **做法**: Critic输出结构化诊断（错误类型、修正建议、约束条件），Controller根据诊断选择修正策略（CHAIN/QUERY/BOTH/SKIP）
- **预期收益**: 针对不同错误类型采用不同修正方式，提升修正效率
- **风险**: 增加Critic阶段的prompt工程复杂度
- **状态**: Controller已有骨架（`_llm_decide_diagnose`/`_llm_decide_refine`），需合并为单次调用并增强

### 方向4: Critique Consolidation（已确认的大方向）

- **做法**: 构建Consolidated Critique Tree，同时积累成功和失败模板，定期巩固蒸馏
- **预期收益**: 批评知识库更紧凑、更高质量，减少检索噪声
- **风险**: 实现复杂度较高，需要设计consolidation触发机制和蒸馏策略
- **状态**: 大方向已确认(2026-04-10)，细节待定

---

## 四、优先级建议

| 优先级 | 方向 | 理由 |
|--------|------|------|
| **高** | 方向1: 传递Thought上下文 | 改动最小，信息增益明确，可直接验证效果 |
| **高** | 方向3: 结构化Critic + 策略路由 | 与现有Controller架构衔接，是Critique Consolidation的基础 |
| **中** | 方向2: 增量修正 | 需要中间表校验配合，单独收益不确定 |
| **中** | 方向4: Critique Consolidation | 长期大方向，建议在方向1和3验证后再推进 |

---

## 五、与Critique Consolidation大方向的关系

- **方向1** 为 Consolidation 提供更丰富的输入信息（thought-level critique）
- **方向3** 的结构化诊断是 Consolidation 模板的基础数据结构
- **方向4** 是最终整合，依赖前两个方向的实验结果来确定模板格式和巩固策略