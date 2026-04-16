# Bad Case 对比分析报告

**生成时间**: 2026-04-16 11:01:10

---

# 项目信息

## 当前项目

- **路径**: `results/refine/wikitq/sota/gpt-5.4`
- **准确率**: Refine Stage Accuracy: 0.8422749251669353
- **错误案例数**: 685

## 参考项目

- **路径**: `/home/ubuntu/mnt/lx/Table-Critic/results/refine/wikitq/gpt-5.4`
- **准确率**: Thought Stage Accuracy: 0.8436564586691228
- **错误案例数**: 679

---

# 当前项目 Bad Case 分析

## 错误案例统计
- **总错误数**: 685
- **错误类型分布**:
  - 完全不匹配: 251 (36.6%)
  - 部分匹配错误: 240 (35.0%)
  - 数值错误: 191 (27.9%)
  - 布尔判断错误: 3 (0.4%)

## 错误案例示例

展示前 10 个错误案例：

### 案例 1

**UID**: `nu-0`

**问题**: which country had the most cyclists finish within the top 10?

**正确答案**: `ESP`

**预测答案**: `Spain|Italy`

**错误类型**: 完全不匹配

**Chain长度**: 3

---

### 案例 2

**UID**: `nu-23`

**问题**: what yacht had the next best time (smaller time is better) than ausmaid?

**正确答案**: `Brindabella`

**预测答案**: `ragamuffin`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 3

**UID**: `nu-25`

**问题**: how many times was amanda on the judging panel?

**正确答案**: `3`

**预测答案**: `8`

**错误类型**: 数值错误

**Chain长度**: 3

---

### 案例 4

**UID**: `nu-42`

**问题**: what building had the least height in germany?

**正确答案**: `Strasbourg Cathedral`

**预测答案**: `st nikolai`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 5

**UID**: `nu-46`

**问题**: what is the total number of models covered in the table?

**正确答案**: `20`

**预测答案**: `12`

**错误类型**: 数值错误

**Chain长度**: 3

---

### 案例 6

**UID**: `nu-49`

**问题**: how many times were consecutive games played against millwall?

**正确答案**: `1`

**预测答案**: `2`

**错误类型**: 数值错误

**Chain长度**: 4

---

### 案例 7

**UID**: `nu-58`

**问题**: who was the top placing competitor?

**正确答案**: `Esther Shahamorov`

**预测答案**: `ze'ev friedman`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 8

**UID**: `nu-66`

**问题**: what date is next listed after june 14, 2010.

**正确答案**: `December 6, 2010`

**预测答案**: `september 6, 2010`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 9

**UID**: `nu-82`

**问题**: how many teams did not score any goals in the 2006 season?

**正确答案**: `1`

**预测答案**: `0`

**错误类型**: 数值错误

**Chain长度**: 4

---

### 案例 10

**UID**: `nu-91`

**问题**: which country has the larger number of circuits?

**正确答案**: `USA`

**预测答案**: `United States`

**错误类型**: 完全不匹配

**Chain长度**: 4

---


---

# 参考项目 Bad Case 分析

## 错误案例统计
- **总错误数**: 679
- **错误类型分布**:
  - 完全不匹配: 250 (36.8%)
  - 部分匹配错误: 237 (34.9%)
  - 数值错误: 189 (27.8%)
  - 布尔判断错误: 3 (0.4%)

## 错误案例示例

展示前 10 个错误案例：

### 案例 1

**UID**: `nu-0`

**问题**: which country had the most cyclists finish within the top 10?

**正确答案**: `ESP`

**预测答案**: `Spain|Italy`

**错误类型**: 完全不匹配

**Chain长度**: 3

---

### 案例 2

**UID**: `nu-23`

**问题**: what yacht had the next best time (smaller time is better) than ausmaid?

**正确答案**: `Brindabella`

**预测答案**: `ragamuffin`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 3

**UID**: `nu-25`

**问题**: how many times was amanda on the judging panel?

**正确答案**: `3`

**预测答案**: `8`

**错误类型**: 数值错误

**Chain长度**: 3

---

### 案例 4

**UID**: `nu-42`

**问题**: what building had the least height in germany?

**正确答案**: `Strasbourg Cathedral`

**预测答案**: `st nikolai`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 5

**UID**: `nu-46`

**问题**: what is the total number of models covered in the table?

**正确答案**: `20`

**预测答案**: `22`

**错误类型**: 数值错误

**Chain长度**: 3

---

### 案例 6

**UID**: `nu-49`

**问题**: how many times were consecutive games played against millwall?

**正确答案**: `1`

**预测答案**: `2`

**错误类型**: 数值错误

**Chain长度**: 4

---

### 案例 7

**UID**: `nu-66`

**问题**: what date is next listed after june 14, 2010.

**正确答案**: `December 6, 2010`

**预测答案**: `september 6, 2010`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 8

**UID**: `nu-91`

**问题**: which country has the larger number of circuits?

**正确答案**: `USA`

**预测答案**: `United States`

**错误类型**: 完全不匹配

**Chain长度**: 4

---

### 案例 9

**UID**: `nu-92`

**问题**: did brazil and the united states have the highest gold count?

**正确答案**: `Yes`

**预测答案**: `No`

**错误类型**: 布尔判断错误

**Chain长度**: 3

---

### 案例 10

**UID**: `nu-102`

**问题**: who was the first voted out?

**正确答案**: `Yelena Kondulaynen`

**预测答案**: `yelena kondulaynen 44.the actress`

**错误类型**: 部分匹配错误

**Chain长度**: 3

---


---

## Bad Case 对比分析

### 错误数量对比

- **当前项目错误数**: 685
- **参考项目错误数**: 679
- **共同错误案例**: 663
- **当前项目独有错误**: 22
- **参考项目独有错误**: 16

⚠️ **当前项目相比参考项目增加了 6 个错误案例**

### 共同错误案例示例

#### 共同错误 1

**UID**: `nu-0`

**问题**: which country had the most cyclists finish within the top 10?

**正确答案**: `ESP`

**预测答案**: `Spain|Italy`

**错误类型**: 完全不匹配

---

#### 共同错误 2

**UID**: `nu-23`

**问题**: what yacht had the next best time (smaller time is better) than ausmaid?

**正确答案**: `Brindabella`

**预测答案**: `ragamuffin`

**错误类型**: 完全不匹配

---

#### 共同错误 3

**UID**: `nu-25`

**问题**: how many times was amanda on the judging panel?

**正确答案**: `3`

**预测答案**: `8`

**错误类型**: 数值错误

---

#### 共同错误 4

**UID**: `nu-42`

**问题**: what building had the least height in germany?

**正确答案**: `Strasbourg Cathedral`

**预测答案**: `st nikolai`

**错误类型**: 完全不匹配

---

#### 共同错误 5

**UID**: `nu-46`

**问题**: what is the total number of models covered in the table?

**正确答案**: `20`

**预测答案**: `12`

**错误类型**: 数值错误

---

### 当前项目独有错误案例（需要修复）

#### 独有错误 1

**UID**: `nu-58`

**问题**: who was the top placing competitor?

**正确答案**: `Esther Shahamorov`

**预测答案**: `ze'ev friedman`

**错误类型**: 完全不匹配

---

#### 独有错误 2

**UID**: `nu-82`

**问题**: how many teams did not score any goals in the 2006 season?

**正确答案**: `1`

**预测答案**: `0`

**错误类型**: 数值错误

---

#### 独有错误 3

**UID**: `nu-122`

**问题**: how many designers do not have an associated publication?

**正确答案**: `6`

**预测答案**: `10`

**错误类型**: 数值错误

---

#### 独有错误 4

**UID**: `nu-245`

**问题**: how many singles are only a single and not apart of an album?

**正确答案**: `18`

**预测答案**: `3`

**错误类型**: 数值错误

---

#### 独有错误 5

**UID**: `nu-320`

**问题**: which is the only tournament with a british runner-up?

**正确答案**: `Tsuruya Open`

**预测答案**: `cannot be determined`

**错误类型**: 完全不匹配

---

### 参考项目独有错误案例（当前项目已修复）

#### 已修复错误 1

**UID**: `nu-156`

**问题**: who was the last place driver to complete at least 50 laps?

**正确答案**: `Jacques Villeneuve`

**参考项目预测**: `Narain Karthikeyan`

**错误类型**: 完全不匹配\n
---

#### 已修复错误 2

**UID**: `nu-645`

**问题**: how many u.s. drivers raced?

**正确答案**: `11`

**参考项目预测**: `cannot be determined`

**错误类型**: 完全不匹配\n
---

#### 已修复错误 3

**UID**: `nu-792`

**问题**: what was the first game to score more than 10 apps?

**正确答案**: `2008`

**参考项目预测**: `24`

**错误类型**: 数值错误\n
---

#### 已修复错误 4

**UID**: `nu-1145`

**问题**: what is the only position in the great officers of england that is in commission?

**正确答案**: `Lord High Treasurer`

**参考项目预测**: `3`

**错误类型**: 完全不匹配\n
---

#### 已修复错误 5

**UID**: `nu-1262`

**问题**: do all the symbols come before the numbers?

**正确答案**: `no`

**参考项目预测**: `Yes.`

**错误类型**: 完全不匹配\n
---


---

# 结论与建议

## 主要发现

1. **性能下降**: 当前项目相比参考项目增加了 6 个错误案例（0.9%）

## 错误类型对比

- ⚠️ **完全不匹配**: 当前项目更多（251 vs 250, +1）
- ➖ **布尔判断错误**: 相同（3）
- ⚠️ **数值错误**: 当前项目更多（191 vs 189, +2）
- ⚠️ **部分匹配错误**: 当前项目更多（240 vs 237, +3）


## 改进建议

### 优先修复的错误类型

- **完全不匹配**: 251 个案例 (36.6%)
- **部分匹配错误**: 240 个案例 (35.0%)
- **数值错误**: 191 个案例 (27.9%)


### 具体建议

1. **针对共同错误**: 这些是两个项目都存在的问题，可能是数据质量或任务固有的难度
2. **针对独有错误**: 当前项目的独有错误是优先修复的重点
3. **错误类型分析**: 关注占比最高的错误类型，优化相关的推理逻辑
