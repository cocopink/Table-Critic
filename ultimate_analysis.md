# 综合Bad Case分析报告（简洁版）

**生成时间**: 2026-04-16

## 汇总统计

- **WikiTQ**: 689 个错误案例
- **TabFact**: 78 个错误案例

## WikiTQ错误分类

- **其他错误**: 84 个案例
- **多答案处理错误**: 141 个案例
- **实体识别错误**: 270 个案例
- **布尔判断错误**: 3 个案例
- **数值统计错误**: 172 个案例
- **数值计算错误**: 5 个案例
- **数值错误**: 14 个案例

## TabFact错误分类

- **布尔判断错误**: 78 个案例

## 错误案例ID分类表

| 数据集 | 类型 | ID列表 |
|-------|------|--------|
| WikiTQ | 其他错误 | nu-134, nu-138, nu-215, nu-267, nu-369, nu-393, nu-422, nu-423, nu-443, nu-534... |
| WikiTQ | 多答案处理错误 | nu-0, nu-123, nu-153, nu-190, nu-228, nu-277, nu-279, nu-288, nu-327, nu-332... |
| WikiTQ | 实体识别错误 | nu-23, nu-42, nu-58, nu-66, nu-91, nu-102, nu-117, nu-144, nu-183, nu-213... |
| WikiTQ | 布尔判断错误 | nu-92, nu-116, nu-3033 |
| WikiTQ | 数值统计错误 | nu-25, nu-46, nu-49, nu-82, nu-122, nu-124, nu-209, nu-216, nu-238, nu-245... |
| WikiTQ | 数值计算错误 | nu-786, nu-2467, nu-3070, nu-3834, nu-3984 |
| WikiTQ | 数值错误 | nu-129, nu-159, nu-293, nu-310, nu-321, nu-328, nu-931, nu-1374, nu-2099, nu-2148... |
| TabFact | 布尔判断错误 | test-38, test-42, test-80, test-91, test-127, test-151, test-178, test-188, test-198, test-199... |

## WikiTQ错误案例示例

### 其他错误

**UID**: `nu-134`

**问题**: is the first reagent for a hydroxyalkyl usually a halogenoalkane or an epoxide?

**正确答案**: `Epoxides`

**预测答案**: `epoxide`

**思维链**:
```
1. select_row: f_select_row([row 4, row 5, row 6, row 7, row 8])

2. select_column: f_select_column([cellulose ethers, reagent])

3. simple_query: The table shows that for **hydroxyalkyl**, the first listed reagent is **epoxide...
```

**表格（前5行）**:
```
cellulose ethers | reagent | example | reagent | group r = h or | water solubility | application | e number
alkyl | halogenoalkanes | methylcellulose | chloromethane | -ch3 | cold water soluble |  | e461
 |  | ethylcellulose | chloroethane | -ch2ch3 | water insoluble | a commercial thermop | e462
 |  | ethyl methyl cellulo | chloromethane and ch | -ch3 or -ch2ch3 |  |  | e465
hydroxyalkyl | epoxides | hydroxyethyl cellulo | ethylene oxide | -ch2ch2oh | cold/hot water solub | gelling and thickeni | 
...
```

---

### 多答案处理错误

**UID**: `nu-0`

**问题**: which country had the most cyclists finish within the top 10?

**正确答案**: `ESP`

**预测答案**: `Spain|Italy`

**思维链**:
```
1. add_column
2. select_column: f_select_column([cyclist])

3. simple_query: From the top 10 cyclists:

- ESP: Alejandro Valverde, Samuel Sánchez, Haimar Zub...
```

**表格（前5行）**:
```
rank | cyclist | team | time | uci protour\npoints
1 | alejandro valverde ( | caisse d'epargne | 5h 29' 10" | 40
2 | alexandr kolobnev (r | team csc saxo bank | s.t. | 30
3 | davide rebellin (ita | gerolsteiner | s.t. | 25
4 | paolo bettini (ita) | quick step | s.t. | 20
...
```

---

### 实体识别错误

**UID**: `nu-23`

**问题**: what yacht had the next best time (smaller time is better) than ausmaid?

**正确答案**: `Brindabella`

**预测答案**: `ragamuffin`

**思维链**:
```
1. select_row: f_select_row([row 4])f_select_row([row 4])

2. select_column: f_select_column([sail number, yacht, elapsed time\nd:hh:mm:ss])

3. sort_column
4. simple_query: ragamuffin

```

**表格（前5行）**:
```
position | sail number | yacht | state/country | yacht type | loa\n(metres) | skipper | elapsed time\nd:hh:m
1 | us17 | sayonara | usa | farr ilc maxi | 24.13 | larry ellison | 2:19:03:32
2 | c1 | brindabella | nsw | jutson 79 | 24.07 | george snow | 2:21:55:06
3 | yc1000 | ausmaid | sa | farr 47 | 14.24 | kevan pearce | 3:06:02:29
4 | aus70 | ragamuffin | nsw | farr 50 | 15.15 | syd fischer | 3:06:11:29
...
```

---

### 布尔判断错误

**UID**: `nu-92`

**问题**: did brazil and the united states have the highest gold count?

**正确答案**: `Yes`

**预测答案**: `No`

**思维链**:
```
1. select_column: f_select_column([nation, gold])

2. sort_column: Yes. Use `f_sort_column(gold)` with order `"large to small"`. The top two are Br...
3. simple_query: From the sub-table, Brazil has 21 gold medals, which is the highest gold count. ...
```

**表格（前5行）**:
```
rank | nation | gold | silver | bronze | total
1. | brazil | 21 | 9 | 12 | 42
2. | united states | 9 | 3 | 6 | 18
3. | china | 1 | 9 | 8 | 18
4. | australia | 1 | 1 | 1 | 3
...
```

---

### 数值统计错误

**UID**: `nu-25`

**问题**: how many times was amanda on the judging panel?

**正确答案**: `3`

**预测答案**: `8`

**思维链**:
```
1. select_column: f_select_column([judging panel])

2. group_column: The question asks to count occurrences of “amanda” within the values of the **ju...
3. simple_query: Amanda Holden appears on the judging panel in Group 1 (4 times), Group 2 (3 time...
```

**表格（前5行）**:
```
series | premiere | finale | winner | runner-up | third place | host(s) | judging panel | guest judge(s)
one | 9 june 2007 | 17 june 2007 | paul potts | damon scott | connie talbot | ant & dec | simon cowell\namanda | n/a
two | 12 april 2008 | 31 may 2008 | george sampson | signature | andrew johnston | ant & dec | simon cowell\namanda | n/a
three | 11 april 2009 | 30 may 2009 | diversity | susan boyle | julian smith | ant & dec | simon cowell\namanda | kelly brook
four | 17 april 2010 | 5 june 2010 | spelbound | twist and pulse | kieran gaffney | ant & dec | simon cowell\namanda | louis walsh
...
```

---

### 数值计算错误

**UID**: `nu-786`

**问题**: how boats do tane yaku jetfoils operate in total?

**正确答案**: `3`

**预测答案**: `6`

**思维链**:
```
1. select_column: f_select_column([original operator, 2nd operator, 3rd operator])

2. group_column: The question asks for the total number of boats operated by **tane yaku jetfoils...
3. simple_query: Count all occurrences of **tane yaku jetfoils** across the 3 operator columns.

...
```

**表格（前5行）**:
```
hull | type | original name | original operator | delivery | disposition (2012) | 2nd name | 2nd operator | 3rd name | 3rd operator
№ 1 | 929-117 | tsubasa | sado kisen | mar 1998 | active |  |  |  | 
№ 2 | 929-117 | pegasus | kyusyu shosen co. lt | jun 1989 | active | toppy 1 | tane yaku jetfoils |  | 
№ 3 | 929-117 | toppy 1 | tane yaku jetfoils | sep 1989 | active | beetle 3 | jr kyushu jet ferrie |  | 
№ 4 | 929-117 | princess dacil | trasmediterranea | mar 1990 | active | pegasus | kyusyu shosen co. lt |  | 
...
```

---

### 数值错误

**UID**: `nu-129`

**问题**: how may away games did they win?

**正确答案**: `7`

**预测答案**: `2`

**思维链**:
```
1. select_row: f_select_row([row 1, row 2])

2. select_column: f_select_column([opponent, result])

3. group_column: The question asks for the number of away games won. Since away games are indicat...
4. simple_query: They won both listed away games: at Los Angeles Rams and at Cleveland Browns. So...
```

**表格（前5行）**:
```
week | date | opponent | result | attendance
1 | september 6, 1981 | at los angeles rams | w 27–20 | 63,198
2 | september 13, 1981 | at cleveland browns | w 9–3 | 79,483
3 | september 20, 1981 | miami dolphins | l 16–10 | 47,379
4 | september 27, 1981 | at new york jets | l 33–17 | 50,309
...
```

---

## TabFact错误案例示例

### 案例 1

**UID**: `test-38`

**陈述**: steve stricker has the best score out of all of the players from the united states

**正确答案**: `False`

**预测答案**: `True`

**思维链**:
```
1. select_row: f_select_row([row 1, row 5, row 7, row 9, row 10])

2. select_column: f_select_column([player, country, score])

3. sort_column: The statement asks whether Steve Stricker has the best score among players from ...
4. group_column: The statement compares Steve Stricker to other players from the same country, so...
5. simple_query: YES

```

---

### 案例 2

**UID**: `test-42`

**陈述**: kenneth ferrie and geoff ogilvy of australia were the only players to score a + 1 to par

**正确答案**: `True`

**预测答案**: `False`

**思维链**:
```
1. select_column: f_select_column([player, country, to par])

2. group_column: The statement is about how many players have the value "+ 1" in the "to par" col...
3. sort_column: We need to check who had `to par = + 1`, so we should sort the **to par** column...
4. simple_query: Explanation: In the sub-table, the only two players with a to par score of +1 ar...
5. simple_query: Explanation: The grouped table shows exactly 2 players with a score of +1 to par...
```

---

### 案例 3

**UID**: `test-80`

**陈述**: the winner of the miyagi tv cup dunlop ladies open had a 3 - stroke margin of victory

**正确答案**: `False`

**预测答案**: `True`

**思维链**:
```
1. select_row: f_select_row([row 13])

2. select_column: f_select_column([tournament, margin of victory])

3. simple_query: YES

```

---

