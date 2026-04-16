# 超级详细的Bad Case分析报告

**生成时间**: 2026-04-16

---

# 汇总统计

## WikiTQ 数据集

- **总错误数**: 43
- **错误类型数**: 7

### 错误类型分布

- 数值统计错误（计数）: 22 (51.2%)
- 实体识别错误: 9 (20.9%)
- 完全不匹配: 4 (9.3%)
- 多答案处理错误: 3 (7.0%)
- 数值计算错误（求和）: 3 (7.0%)
- 条件理解错误: 1 (2.3%)
- 数值计算错误（其他）: 1 (2.3%)

## TabFact 数据集

- **总错误数**: 16
- **错误类型数**: 2

### 错误类型分布

- 完全不匹配: 14 (87.5%)
- 条件理解错误: 2 (12.5%)

---

## 错误案例ID分类表

| 错误类型 | 错误案例ID | 数量 |
|---------|-----------|------|
| TabFact-完全不匹配 | test-42, test-443, test-650, test-915, test-925, test-1040, test-1261, test-1354, test-1392, test-1399, test-1878, test-1895, test-1929, test-1992 | 14 |
| TabFact-条件理解错误 | test-920, test-1218 | 2 |
| WikiTQ-多答案处理错误 | test-332, test-1705, test-3391 | 3 |
| WikiTQ-完全不匹配 | test-1099, test-1448, test-1969, test-2522 | 4 |
| WikiTQ-实体识别错误 | test-320, test-950, test-1121, test-1423, test-1913, test-2194, test-2562, test-2729, test-3192 | 9 |
| WikiTQ-数值统计错误（计数） | test-82, test-122, test-245, test-1014, test-1730, test-1798, test-1867, test-1936, test-1977, test-2026, test-2550, test-2723, test-2724, test-2888, test-2929, test-2974, test-3290, test-3312, test-3550, test-3782, test-4169, test-4300 | 22 |
| WikiTQ-数值计算错误（其他） | test-4062 | 1 |
| WikiTQ-数值计算错误（求和） | test-2467, test-2516, test-3070 | 3 |
| WikiTQ-条件理解错误 | test-1873 | 1 |

---

## WikiTQ 详细案例分析

## 详细错误案例分析

### 多答案处理错误

**案例数量**: 3

#### 案例 1

**UID**: `test-332`

**问题**: what year did poland achieve its highest position?

**正确答案**: `2010`

**预测答案**: `1999|2003`

**错误类型**: 多答案处理错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1, row 4])

  参数: [("['1', '4']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([year, venue, position])

  参数: [("['position', 'venue', 'year']", np.float64(1.0))]

步骤 3: sort_column

步骤 4: simple_query
  思考: The rows where the venue is in Poland are:
- 1999 | bydgoszcz, poland | 13th (q)
- 2003 | bydgoszcz, poland | 13th (q)

To find the highest position, compare the rankings. In athletics, a higher position means a better rank, so the smaller number is better. Both Poland entries have the same position, 13th (q), so they are tied for the highest position achieved in Poland.
  参数: [('1999|2003', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-1705`

**问题**: the only location not in france.

**正确答案**: `Middelkerke, Belgium`

**预测答案**: `leffinghe|middelkerke, belgium`

**错误类型**: 多答案处理错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([location])

  参数: [("['location']", np.float64(1.0))]

步骤 2: sort_column

步骤 3: group_column
  思考: f_group_column(location)

  参数: [("('location', [('douai, france', 4), ('leffinghe', 1), ('middelkerke, belgium', 1), ('northeast of

步骤 4: simple_query
  思考: Explanation: From the grouped locations, most entries are explicitly in France: "douai, france", "northeast of bapaume, france", and "sailly, france". "Middelkerke, belgium" is explicitly not in France. "Leffinghe" is listed without a country, but it is not identified as being in France in the table. Therefore, the location not in France is "middelkerke, belgium" and also "leffinghe" if considering the table entries that are not marked as France.
  参数: [('leffinghe|middelkerke, belgium', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 完全不匹配

**案例数量**: 4

#### 案例 1

**UID**: `test-1099`

**问题**: what percent do the top 3 make up?

**正确答案**: `89.17`

**预测答案**: `77.85%`

**错误类型**: 完全不匹配

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 2, row 3, row 4])

  参数: [("['2', '3', '4']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([language, 2001 census[1]\n(total population 1,004.59 million)])

  参数: [("['2001 census[1]\\\\n(total population 1,004.59 million)', 'language']", np.float64(1.0))]

步骤 3: simple_query
  思考: Explanation: The top 3 languages have populations of 422,048,642, 230,000,000, and 130,000,000. Adding them gives 782,048,642. The total population is 1,004.59 million, or 1,004,590,000. Dividing 782,048,642 by 1,004,590,000 and converting to a percentage gives about 77.85%.
  参数: [('77.85%', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-1448`

**问题**: how long in characters is the unicode for tilde?

**正确答案**: `6`

**预测答案**: `cannot be determined`

**错误类型**: 完全不匹配

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([name, unicode])

  参数: [("['name', 'unicode']", np.float64(1.0))]

步骤 3: simple_query
  思考: The selected columns `name` and `unicode` are relevant for this question, because we need the unicode entry for the character named tilde and then determine its length in characters.

However, the provided sub-table only goes up to `left-brace | u+007b` and does not include a row for `tilde`. Since `tilde` does not appear in the shown table, its unicode value cannot be identified from the provided data, so the length in characters also cannot be determined from this sub-table.
  参数: [('cannot be determined', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 实体识别错误

**案例数量**: 9

#### 案例 1

**UID**: `test-320`

**问题**: which is the only tournament with a british runner-up?

**正确答案**: `Tsuruya Open`

**预测答案**: `cannot be determined`

**错误类型**: 实体识别错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([tournament, runner(s)-up])

  参数: [("['runner(s)-up', 'tournament']", np.float64(1.0))]

步骤 3: group_column
  思考: To determine **which tournament is the only one with a British runner-up**, we should group entries by the **runner(s)-up** column, since that column contains the people whose nationality we need to inspect.

**

步骤 4: sort_column
  思考: f_filter(runner(s)-up, contains, british)


步骤 5: simple_query
  思考: The table includes the columns **tournament** and **runner(s)-up**, but it does **not** provide the nationalities of the runners-up. So although names such as **Scott Laycock** appear in the runner-up column, the table alone does not indicate whether any runner-up is British. Therefore, the requested tournament cannot be determined from the table without using outside knowledge.
  参数: [('cannot be determined', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-950`

**问题**: which contestants are below age 18?

**正确答案**: `Isabelle Raisa`

**预测答案**: `isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia maria hausmair`

**错误类型**: 实体识别错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1, row 5, row 8, row 9, row 15, row 16])

  参数: [("['1', '15', '16', '5', '8', '9']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([contestant, age])

  参数: [("['age', 'contestant']", np.float64(1.0))]

步骤 3: simple_query
  思考: All listed contestants are below 18, since their ages are 16 or 17.
  参数: [('isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia mari

步骤 4: simple_query
  思考: Explanation: The extracted sub-table shows six contestants with ages 16 or 17, and both ages are below 18. Therefore, the contestants below age 18 are Isabelle Raisa, Nataša Marić, Teodora-Mădălina Andreica, Yemisi Rieger, Gina Zeneb Adamu, and Antonia Maria Hausmair.
  参数: [('isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia mari
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 数值统计错误（计数）

**案例数量**: 22

#### 案例 1

**UID**: `test-82`

**问题**: how many teams did not score any goals in the 2006 season?

**正确答案**: `1`

**预测答案**: `0`

**错误类型**: 数值统计错误（计数）

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: Select relevant rows.

  参数: [("['3']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([season, team, goals])

  参数: [("['goals', 'season', 'team']", np.float64(1.0))]

步骤 3: group_column
  思考: f_group_column(goals)


步骤 4: simple_query
  思考: Explanation: The resulting sub-table shows the 2006 season for Spartak Nizhny Novgorod, and the number of goals is 1. Since 1 is not 0, there were no teams in the extracted result that did not score any goals in the 2006 season.
  参数: [('0', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-122`

**问题**: how many designers do not have an associated publication?

**正确答案**: `6`

**预测答案**: `10`

**错误类型**: 数值统计错误（计数）

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([designer(s), associated publication])

  参数: [("['associated publication', 'designer(s)']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks for entries where the associated publication is missing, so we should group by the "associated publication" column to identify the blank/non-blank groups.
  参数: [('(\'associated publication\', [(\'\', 6), (\'the sunday times\', 4), (\'the times\', 4), (\'vogue\

步骤 3: simple_query
  思考: To answer “how many designers do not have an associated publication?”, we must count the individual designer entries in rows where the **associated publication** cell is empty, rather than just counting the number of rows.

The rows with empty associated publication are:

- **Row 1**: mary quant; reed crawford (hat); anello & davide (boots) → **3**
- **Row 2**: jean muir for jane & jane; charles jourdan for dior (shoes) → **2**
- **Row 3**: john bates for jean varon; anello & davide (shoes) → **2**
- **Row 44**: prada → **1**
- **Row 45**: giles deacon at giles → **1**
- **Row 48**: vivienne westwood → **1**

Adding these gives **3 + 2 + 2 + 1 + 1 + 1 = 10**.
  参数: [('10', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 数值计算错误（其他）

**案例数量**: 1

#### 案例 1

**UID**: `test-4062`

**问题**: in cycle 4 of austria's next top model, what is the average of all the contestants' ages?

**正确答案**: `18`

**预测答案**: `20.125`

**错误类型**: 数值计算错误（其他）

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([age])

  参数: [("['age']", np.float64(1.0))]

步骤 2: simple_query
  思考: 18.875

  参数: [('18.875', np.float64(1.0))]

步骤 3: simple_query
  思考: Explanation: To find the average age, add all 16 contestants' ages and divide by 16. The ages are 16, 18, 21, 23, 16, 21, 20, 17, 17, 20, 24, 21, 20, 16, 17, and 16. Their sum is 322. Dividing 322 by 16 gives 20.125. Therefore, the average age of all the contestants is 20.125.
  参数: [('20.125', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 数值计算错误（求和）

**案例数量**: 3

#### 案例 1

**UID**: `test-2467`

**问题**: what is the total amount of numbered routes in massachusetts that are located in boston?

**正确答案**: `7`

**预测答案**: `2`

**错误类型**: 数值计算错误（求和）

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_row
  思考: f_select_row([row 7, row 9, row 22])

  参数: [("['22', '7', '9']", np.float64(1.0))]

步骤 3: select_column
  思考: f_select_column([route number(s), location])

  参数: [("['location', 'route number(s)']", np.float64(1.0))]

步骤 4: group_column
  思考: The question asks about routes by where they are located, so we should group the rows using the **location** column.
  参数: [("('location', [('boston', 2), ('braintree to boston', 1)])", np.float64(1.0))]

步骤 5: simple_query
  思考: Explanation: The grouped sub-table shows 2 numbered routes with the location exactly listed as "boston." The row with location "braintree to boston" is a different location entry and is not counted as being located in Boston only. Therefore, the total amount of numbered routes in Massachusetts that are located in Boston is 2.
  参数: [('2', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-2516`

**问题**: what is the total number of games played on hard surfaces for this player?

**正确答案**: `12`

**预测答案**: `11`

**错误类型**: 数值计算错误（求和）

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1, row 3, row 4, row 6, row 7, row 13, row 14, row 15, row 17, row 18, row 20])

  参数: [("['1', '13', '14', '15', '17', '18', '20', '3', '4', '6', '7']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([surface])

  参数: [("['surface']", np.float64(1.0))]

步骤 3: group_column
  思考: To find the total number of games played on hard surfaces, we should group the entries by the **surface** column so we can count how many are labeled **hard**.
  参数: [("('surface', [('hard', 8), ('hard (i)', 3)])", np.float64(1.0))]

步骤 4: simple_query
  思考: The table groups the surfaces into:
- hard: 8
- hard (i): 3

Since the question asks for games played on **hard surfaces**, and **hard (i)** is also a hard surface, we add both counts:

8 + 3 = 11
  参数: [('11', np.float64(1.0))]

步骤 5: simple_query
  思考: Explanation: The grouped sub-table shows 8 games on hard surfaces and 3 games on hard (i) surfaces, which are also hard surfaces. Adding them together gives a total of 11 games played on hard surfaces.
  参数: [('11', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 条件理解错误

**案例数量**: 1

#### 案例 1

**UID**: `test-1873`

**问题**: how many places are listed after sixtieth street?

**正确答案**: `1`

**预测答案**: `cannot be determined`

**错误类型**: 条件理解错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([name of place])

  参数: [("['name of place']", np.float64(1.0))]

步骤 2: sort_column
  思考: To answer this question, we need to find the order of place names alphabetically and identify which places come after "sixtieth street". Since the relevant column is "name of place", which is a string type, we should sort that column in ascending alphabetical order.

步骤 3: simple_query
  思考: The question asks for the number of places listed after **sixtieth street**. In the provided sub-table, the listed place names run from **sabinsville** through **sanatoga park**, and **sixtieth street** does not appear anywhere in the shown rows. Since the necessary reference row for **sixtieth street** is not present in the provided table excerpt, we cannot identify where “after sixtieth street” begins, so the count cannot be computed from the given data.
  参数: [('cannot be determined', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---


---

## TabFact 详细案例分析

## 详细错误案例分析

### 完全不匹配

**案例数量**: 14

#### 案例 1

**UID**: `test-42`

**问题**: kenneth ferrie and geoff ogilvy of australia were the only players to score a + 1 to par

**正确答案**: ``

**预测答案**: `NO`

**错误类型**: 完全不匹配

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([player, country, to par])

  参数: [("['country', 'player', 'to par']", np.float64(1.0))]

步骤 2: group_column
  思考: The statement is about how many players have the value "+ 1" in the "to par" column, so we should group by that column first.
  参数: [("('to par', [('+ 3', 4), ('+ 1', 2), ('+ 2', 2), ('- 1', 1), ('e', 1)])", np.float64(1.0))]

步骤 3: sort_column
  思考: We need to check who had `to par = + 1`, so we should sort the **to par** column.

- Column: `to par`
- Datatype: **Numerical** (golf scores like `-1`, `e`, `+1` can be interpreted in score order)
- To find all players with `+1`, sorting helps place equal values together.

**

步骤 4: simple_query
  思考: Explanation: In the sub-table, the only two players with a to par score of +1 are Kenneth Ferrie and Geoff Ogilvy, so that part is correct. However, the statement says "Kenneth Ferrie and Geoff Ogilvy of Australia," which implies both were from Australia. The table shows Kenneth Ferrie is from England, while Geoff Ogilvy is from Australia. Therefore, the statement is false.
  参数: [('NO', np.float64(1.0))]

步骤 5: simple_query
  思考: Explanation: The grouped table shows exactly 2 players with a score of +1 to par: Kenneth Ferrie and Geoff Ogilvy. However, the statement says “Kenneth Ferrie and Geoff Ogilvy of Australia,” which implies both players are from Australia. In the table, Kenneth Ferrie is from England, while Geoff Ogilvy is from Australia. So the statement is false.
  参数: [('NO', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-443`

**问题**: only two teams (hawthorn and south melbourne) scored less than 10

**正确答案**: ``

**预测答案**: `YES`

**错误类型**: 完全不匹配

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([home team, home team score, away team, away team score])

  参数: [("['away team', 'away team score', 'home team', 'home team score']", np.float64(1.0))]

步骤 3: sort_column
  思考: Explanation: The statement asks whether only two teams, hawthorn and south melbourne, scored less than 10. To check this, we need the score columns and identify scores below 10. The relevant sortable columns are the numeric score columns: home team score and away team score. Since we want teams scoring less than 10, we sort scores from small to large.

步骤 4: group_column
  思考: The statement is about how many teams have scores less than 10, so we should group rows by the score values in the score columns to identify those cases.

步骤 5: simple_query
  思考: Explanation: We check which teams scored less than 10 goals from both the home team score and away team score columns. The scores under 10 are Hawthorn with 6.13 and South Melbourne with 8.8. All other teams scored 10 goals or more, including Collingwood with exactly 10.5, which is not less than 10. Therefore, only two teams—Hawthorn and South Melbourne—scored less than 10.
  参数: [('YES', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

### 条件理解错误

**案例数量**: 2

#### 案例 1

**UID**: `test-920`

**问题**: the blue jays fell to 76 - 86 following their loss to the red sox on september 28

**正确答案**: ``

**预测答案**: `NO`

**错误类型**: 条件理解错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 27])

  参数: [("['27']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([date, opponent, record])

  参数: [("['date', 'opponent', 'record']", np.float64(1.0))]

步骤 3: simple_query
  思考: On september 28, the Blue Jays played the Red Sox and their record became 76 - 86, but the score was 3 - 2, which indicates a win rather than a loss. Therefore, the statement saying they fell to 76 - 86 following their loss to the Red Sox is false.
  参数: [('NO', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

#### 案例 2

**UID**: `test-1218`

**问题**: jonathan legear scored four more goals than matias suarez , the next highest ranked player in the belgian first dvision a league who played in the belgian cup

**正确答案**: ``

**预测答案**: `NO`

**错误类型**: 条件理解错误

**表格数据**:
```
无表格数据
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([player, league])

  参数: [("['league', 'player']", np.float64(1.0))]

步骤 2: sort_column
  思考: f_sort_column(league), the order is "large to small".


步骤 3: simple_query
  思考: Explanation: From the sub-table, Jonathan Legear scored 5 league goals and Matías Suárez scored 1 league goal. The difference is 4 goals. However, the statement says Matías Suárez was “the next highest ranked player,” which is not correct because several players ranked between them have more than 1 goal. Therefore, the statement is false.
  参数: [('NO', np.float64(1.0))]
```

**Clarifier结果**:
```
Clarifier结果为空
```

---

