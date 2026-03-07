# 博弈驱动的记忆演化表格推理框架 - TODO 列表

## 概述
基于现有的 Table-Critic 代码库，构建一个基于博弈论的记忆演化多智能体框架，用于解决复杂表格推理（TableQA）中的准确性与鲁棒性问题。

---

## 第一阶段：Thought 阶段（预处理与 Schema 锚定）

### 1.1 创建 ClarifierAgent
- [ ] **新增文件**: `agents/clarifier_agent.py`
- [ ] 实现 ClarifierAgent 类，提取以下信息：
  - [ ] 列名（Header）
  - [ ] 关键实体（Entity）
  - [ ] 数值单位（Unit）
- [ ] 生成轻量化关键词典作为 Schema 锚点
- [ ] 在Thought阶段完成时，保存 Clarifier 结果供后续阶段使用

### 1.2 修改 Thought 阶段保存逻辑
- [ ] 保存 ClarifierAgent 生成的关键词典，每个case对应一个case_dict_xx
- [ ] 其他保存格式不变

---

## 第二阶段：诊断与路由（Diagnosis & Routing）

### 2.1 创建 Initial Reasoner
- [ ] 这部分实现参照Judge的原实现
- [ ] 判断回答是否正确（Correct/Incorrect）
- [ ] 参照 Table-Critic 的 prompt 实现,

### 2.2 修改 Judge Agent逻辑
- [ ] 实现 Judge 作为总判官，在原始基础上，可能还要接受第三阶段的判断，但是回答格式不发生变化


---

## 第三阶段：修正与博弈（Correction & Game-play）

### 3.1 创建多智能体框架基础
- [ ] **新增文件**: `agents/multi_agent_framework.py`
- [ ] 选择并集成 Multi-Agent 框架（推荐 LangChain）
- [ ] 设计智能体间通信协议

### 3.2 创建 Critic Agent（导师）
- [ ] 参考原Critic模块进行修改
- [ ] 基于记忆库检索 Blueprint 下达纠偏指令
- [ ] 实现 Prompt 策略：
  - [ ] 第一次：只引入 Blueprint
  - [ ] 第二次：引入原文作为少样本学习（现有代码的格式）

### 3.3 创建 Refiner Agent（执行者）
- [ ] **新增文件**: `agents/refiner_agent.py`
- [ ] 根据 Critic 指令重构推理路径
- [ ] 实现推理路径修正逻辑

### 3.4 创建 Validator Agent（审计员）
- [ ] **新增文件**: `agents/validator_agent.py`
- [ ] 基于表格事实（由 Clarifier 提供）进行审计
- [ ] 实现数值与单元格定位的硬性审计
- [ ] 实现严格的逻辑校验模版

### 3.5 实现三次分歧处理机制
- [ ] **新增文件**: `agents/dispute_handler.py`
- [ ] 实现第一次分歧：Critic 带 Validator 建议重试
- [ ] 实现第二次分歧：加入少样本案例学习
- [ ] 实现第三次分歧：触发质疑操作，交 Judge 最终裁决
- [ ] 实现"无法修正"标记机制

### 3.6 修改修正阶段保存逻辑
- [ ] **修改文件**: `refine/TableQA/main.py`
- [ ] 保存第一次错误的思维链 + 最终正确的思维链
- [ ] 保存到：`data/results/{model}/refiner/cache/xx.pkl`
- [ ] 保存方式尽可能和原有代码的逻辑保持一致

---

## 第四阶段：学习与演化（Learning & Evolution）

### 4.1 创建 Curator Agent（档案管理员）
- [ ] 将原有的Curator作为基础，在此基础上做修改
- [ ] 实现摘要化（Summarization）：
  - [ ] 提取新的错误模式（扩充方式可以类比现有代码）
  - [ ] 生成 Blueprint（如"模型倾向于忽略日期范围内的最后一行"）
- [ ] 将整个案例作为叶子节点保存（现有代码已经实现，请勿随意修改）

### 4.2 扩展模板树数据结构
- [ ] **修改文件**: `critic/TableQA/tools/update_tree.py`
- [ ] 增加字段：`blueprint`（错误模式摘要）
- [ ] 增加字段：`confidence_score`（用于主动遗忘）
- [ ] 保持原有树状结构（从通用到具体的错误分类）

### 4.3 实现主动遗忘机制
- [ ] **新增文件**: `memory/active_forgetting.py`
- [ ] 为每个 Case 维护 `confidence_score`
- [ ] 成功引导修复 → 权重 +1
- [ ] 长期低权重的 Case 剔除机制
- [ ] 为新错误腾出空间

### 4.4 修改记忆更新逻辑
- [ ] **修改文件**: `critic/TableQA/tools/update_tree.py`
- [ ] 集成 Curator Agent 的 Blueprint 生成
- [ ] 更新 confidence_score
- [ ] 触发主动遗忘机制

---

## 通用修改



### 5.1 Prompt 优化
- [ ] **Clarifier Prompt**：给出可能更需要关注的行列信息、关键词、数值单位
- [ ] **Critic Prompt**：分阶段，第一次只给 Blueprint，第二次给原文
- [ ] **Validator Prompt**：严格的逻辑校验模版，关注数值计算



---

## 优先级说明

### 高优先级（核心功能）
1. 第一阶段：ClarifierAgent + 保存逻辑
2. 第二阶段：Initial Reasoner + Judge Agent
3. 第三阶段：多智能体框架 + 三次分歧处理
4. 第四阶段：Curator Agent + 主动遗忘机制

### 中优先级（架构优化）
1. Multi-Agent 框架集成
2. Prompt 优化
3. 代码重构与模块化

### 低优先级（辅助功能）-暂时不做
1. 配置管理
2. 测试与验证
3. 日志与监控

---

## 注意事项

1. **所有修改都基于 Table-Critic 现有代码**，不要随意创建新的实现
2. **保存路径必须严格按照 README 要求**：`data/results/{model}/thought/` 和 `data/results/{model}/refiner/`
3. **每个阶段完成后都要计算准确率**并保存到 `acc.txt`
4. **三次分歧处理机制**是核心创新点，需要仔细实现
5. **主动遗忘机制**是记忆进化的关键，需要设计合理的权重更新策略
6. **Blueprint 的生成**是连接第三、四阶段的关键，需要保证质量
7. ~~完成后创建一个run_new_QA和run_new_FV.sh~~ ✅ 已完成
8. 使用siliconflow的Qwen/Qwen2.5-72B-Instruct，api key放置在siliconflow.txt文件中
