

---

# 参考项目（Table-Critic）Bad Case分析

**生成时间**: 2026-04-16

## 汇总统计

- **WikiTQ**: 682 个错误案例
- **TabFact**: 84 个错误案例
- **参考项目准确率（WikiTQ）**: 84.37%

## 错误分类

### WikiTQ

- 其他错误: 81 个
- 多答案处理错误: 139 个
- 实体识别错误: 270 个
- 布尔判断错误: 3 个
- 数值统计错误: 169 个
- 数值计算错误: 5 个
- 数值错误: 15 个

### TabFact

- 布尔判断错误: 84 个

## WikiTQ错误案例示例

### 其他错误

**UID**: `nu-134`

**问题**: is the first reagent for a hydroxyalkyl usually a halogenoalkane or an epoxide?

**正确答案**: `Epoxides`

**预测答案**: `epoxide`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 4, row 5, row 6, row 7, row 8])

  参数: [("['4', '5', '6', '7', '8']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([cellulose ethers, reagent])

  参数: [("['cellulose ethers', 'reagent']", np.float64(1.0))]

步骤 3: simple_query
  思考: The table shows that for **hydroxyalkyl**, the first listed reagent is **epoxides**. Therefore, the first reagent is usually **an epoxide**.
  参数: [('epoxide', np.float64(1.0))]

```

**完整表格**:
```
cellulose ethers | reagent | example | reagent | group r = h or | water solubility | application | e number
alkyl | halogenoalkanes | methylcellulose | chloromethane | -ch3 | cold water soluble |  | e461
 |  | ethylcellulose | chloroethane | -ch2ch3 | water insoluble | a commercial thermoplastic used in coatings, inks, binders, and controlled-release drug tablets | e462
 |  | ethyl methyl cellulose | chloromethane and chloroethane | -ch3 or -ch2ch3 |  |  | e465
hydroxyalkyl | epoxides | hydroxyethyl cellulose | ethylene oxide | -ch2ch2oh | cold/hot water soluble | gelling and thickening agent | 
 |  | hydroxypropyl cellulose (hpc) | propylene oxide | -ch2ch(oh)ch3 | cold water soluble |  | e463
 |  | hydroxyethyl methyl cellulose | chloromethane and ethylene oxide | -ch3 or -ch2ch2oh | cold water soluble | production of cellulose films | 
 |  | hydroxypropyl methyl cellulose (hpmc) | chloromethane and propylene oxide | -ch3 or -ch2ch(oh)ch3 | cold water soluble | viscosity modifier, gelling, foaming and binding agent | e464
 |  | ethyl hydroxyethyl cellulose | chloroethane and ethylene oxide | -ch2ch3 or—ch2ch2oh |  |  | e467
carboxyalkyl | halogenated carboxylic acids | carboxymethyl cellulose (cmc) | chloroacetic acid | -ch2cooh | cold/hot water soluble | often used as its sodium salt, sodium carboxymethyl cellulose (nacmc) | e466
```

---

### 多答案处理错误

**UID**: `nu-0`

**问题**: which country had the most cyclists finish within the top 10?

**正确答案**: `ESP`

**预测答案**: `Spain|Italy`

**完整思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([cyclist])

  参数: [("['cyclist']", np.float64(1.0))]

步骤 3: simple_query
  思考: From the top 10 cyclists:

- ESP: Alejandro Valverde, Samuel Sánchez, Haimar Zubeldia = 3
- ITA: Davide Rebellin, Paolo Bettini, Franco Pellizotti = 3
- RUS: Alexandr Kolobnev, Denis Menchov = 2
- FRA: Stéphane Goubert, David Moncoutié = 2

The countries with the most cyclists in the top 10 are Spain and Italy.
  参数: [('Spain|Italy', np.float64(1.0))]

```

**完整表格**:
```
rank | cyclist | team | time | uci protour\npoints
1 | alejandro valverde (esp) | caisse d'epargne | 5h 29' 10" | 40
2 | alexandr kolobnev (rus) | team csc saxo bank | s.t. | 30
3 | davide rebellin (ita) | gerolsteiner | s.t. | 25
4 | paolo bettini (ita) | quick step | s.t. | 20
5 | franco pellizotti (ita) | liquigas | s.t. | 15
6 | denis menchov (rus) | rabobank | s.t. | 11
7 | samuel sánchez (esp) | euskaltel-euskadi | s.t. | 7
8 | stéphane goubert (fra) | ag2r-la mondiale | + 2" | 5
9 | haimar zubeldia (esp) | euskaltel-euskadi | + 2" | 3
10 | david moncoutié (fra) | cofidis | + 2" | 1
```

---

### 实体识别错误

**UID**: `nu-23`

**问题**: what yacht had the next best time (smaller time is better) than ausmaid?

**正确答案**: `Brindabella`

**预测答案**: `ragamuffin`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 4])f_select_row([row 4])

  参数: [("['4']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([sail number, yacht, elapsed time\nd:hh:mm:ss])

  参数: [("['elapsed time\\\\nd:hh:mm:ss', 'sail number', 'yacht']", np.float64(1.0))]

步骤 3: sort_column

步骤 4: simple_query
  思考: ragamuffin

  参数: [('ragamuffin', np.float64(1.0))]

```

**完整表格**:
```
position | sail number | yacht | state/country | yacht type | loa\n(metres) | skipper | elapsed time\nd:hh:mm:ss
1 | us17 | sayonara | usa | farr ilc maxi | 24.13 | larry ellison | 2:19:03:32
2 | c1 | brindabella | nsw | jutson 79 | 24.07 | george snow | 2:21:55:06
3 | yc1000 | ausmaid | sa | farr 47 | 14.24 | kevan pearce | 3:06:02:29
4 | aus70 | ragamuffin | nsw | farr 50 | 15.15 | syd fischer | 3:06:11:29
5 | cok1 | nokia | ci | farr ketch maxi | 25.20 | david witt | 3:09:19:00
6 | sm1 | fudge | vic | elliot 56 | 17.07 | peter hansen | 3:11:00:26
7 | 6606 | quest | nsw | nelson marek 46 | 14.12 | bob steel | 3:14:41:28
8 | 9090 | industrial quest | qld | nelson marek 43 | 13.11 | kevin miller | 3:14:58:46
9 | 4826 | aspect computing | nsw | radford 16.5 sloop | 16.50 | david pescud | 3:15:28:24
10 | 8338 | afr midnight rambler | nsw | hick 35 | 10.66 | ed psaltis\nbob thomas | 3:16:04:40
```

---

### 布尔判断错误

**UID**: `nu-92`

**问题**: did brazil and the united states have the highest gold count?

**正确答案**: `Yes`

**预测答案**: `No`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([nation, gold])

  参数: [("['gold', 'nation']", np.float64(1.0))]

步骤 2: sort_column
  思考: Yes. Use `f_sort_column(gold)` with order `"large to small"`. The top two are Brazil (21) and United States (9), so they had the highest gold counts.


步骤 3: simple_query
  思考: From the sub-table, Brazil has 21 gold medals, which is the highest gold count. The United States has 9 gold medals, which is lower than Brazil and therefore not the highest. Since the question asks whether Brazil and the United States had the highest gold count, both would need to share the top gold count for the answer to be yes. They do not, so the answer is no.
  参数: [('No', np.float64(1.0))]

```

**完整表格**:
```
rank | nation | gold | silver | bronze | total
1. | brazil | 21 | 9 | 12 | 42
2. | united states | 9 | 3 | 6 | 18
3. | china | 1 | 9 | 8 | 18
4. | australia | 1 | 1 | 1 | 3
4. | netherlands | 1 | 1 | 1 | 3
6. | estonia | 1 | 0 | 0 | 1
7. | germany | 0 | 5 | 1 | 6
8. | russia | 0 | 2 | 3 | 5
9. | argentina | 0 | 2 | 0 | 2
10. | switzerland | 0 | 1 | 1 | 2
11. | norway | 0 | 1 | 0 | 1
12. | austria | 0 | 0 | 1 | 1
```

---

### 数值统计错误

**UID**: `nu-25`

**问题**: how many times was amanda on the judging panel?

**正确答案**: `3`

**预测答案**: `8`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([judging panel])

  参数: [("['judging panel']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks to count occurrences of “amanda” within the values of the **judging panel** column, so we should group based on that column first.
  参数: [("('judging panel', [('simon cowell\\\\namanda holden\\\\npiers morgan', 4), ('simon cowell\\\\namanda holden\\\\nalesha dixon\\\\ndavid walliams', 3), ('simon cowell\\\\namanda holden\\\\ndavid hasselhoff\\\\nmichael mcintyre', 1), ('tba', 1)])", np.float64(1.0))]

步骤 3: simple_query
  思考: Amanda Holden appears on the judging panel in Group 1 (4 times), Group 2 (3 times), and Group 3 (1 time), but not in Group 4 ("tba"). Adding these gives 4 + 3 + 1 = 8.
  参数: [('8', np.float64(1.0))]

```

**完整表格**:
```
series | premiere | finale | winner | runner-up | third place | host(s) | judging panel | guest judge(s)
one | 9 june 2007 | 17 june 2007 | paul potts | damon scott | connie talbot | ant & dec | simon cowell\namanda holden\npiers morgan | n/a
two | 12 april 2008 | 31 may 2008 | george sampson | signature | andrew johnston | ant & dec | simon cowell\namanda holden\npiers morgan | n/a
three | 11 april 2009 | 30 may 2009 | diversity | susan boyle | julian smith | ant & dec | simon cowell\namanda holden\npiers morgan | kelly brook
four | 17 april 2010 | 5 june 2010 | spelbound | twist and pulse | kieran gaffney | ant & dec | simon cowell\namanda holden\npiers morgan | louis walsh
five | 16 april 2011 | 4 june 2011 | jai mcdowall | ronan parke | new bounce | ant & dec | simon cowell\namanda holden\ndavid hasselhoff\nmichael mcintyre | louis walsh
six | 24 march 2012 | 12 may 2012 | ashleigh and pudsey | jonathan and charlotte | only boys aloud | ant & dec | simon cowell\namanda holden\nalesha dixon\ndavid walliams | carmen electra
seven | 13 april 2013 | 8 june 2013 | attraction | jack carroll | richard & adam | ant & dec | simon cowell\namanda holden\nalesha dixon\ndavid walliams | n/a
eight | 12 april 2014 | 31 may 2014 | tba | tba | tba | ant & dec | simon cowell\namanda holden\nalesha dixon\ndavid walliams | ant & dec
nine | 2015 | 2015 | tba | tba | tba | ant & dec | tba | tba
```

---

### 数值计算错误

**UID**: `nu-786`

**问题**: how boats do tane yaku jetfoils operate in total?

**正确答案**: `3`

**预测答案**: `6`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([original operator, 2nd operator, 3rd operator])

  参数: [("['2nd operator', '3rd operator', 'original operator']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks for the total number of boats operated by **tane yaku jetfoils**, and this name may appear in multiple operator columns. So we should group the relevant operator values to count all occurrences.

步骤 3: simple_query
  思考: Count all occurrences of **tane yaku jetfoils** across the 3 operator columns.

- Row 2: 2nd operator
- Row 3: original operator
- Row 6: 3rd operator
- Row 11: 2nd operator
- Row 12: original operator
- Row 13: original operator

That gives **6** total.
  参数: [('6', np.float64(1.0))]

```

**完整表格**:
```
hull | type | original name | original operator | delivery | disposition (2012) | 2nd name | 2nd operator | 3rd name | 3rd operator
№ 1 | 929-117 | tsubasa | sado kisen | mar 1998 | active |  |  |  | 
№ 2 | 929-117 | pegasus | kyusyu shosen co. ltd. | jun 1989 | active | toppy 1 | tane yaku jetfoils |  | 
№ 3 | 929-117 | toppy 1 | tane yaku jetfoils | sep 1989 | active | beetle 3 | jr kyushu jet ferries |  | 
№ 4 | 929-117 | princess dacil | trasmediterranea | mar 1990 | active | pegasus | kyusyu shosen co. ltd. |  | 
№ 5 | 929-117 | nagasaki | jr kyushu jet ferries | apr 1990 | active | beetle 1 | jr kyushu jet ferries |  | 
№ 6 | 929-117 | beetle | jr kyushu jet ferries | jul 1990 | active | rocket | cosmo line | rocket 3 | tane yaku jetfoils
№ 7 | 929-117 | unicorn | kyusyu shosen co. ltd. | oct 1990 | active | pegasus 2 | kyusyu shosen co. ltd. |  | 
№ 8 | 929-117 | beetle 2 | jr kyushu jet ferries | feb 1991 | active |  |  |  | 
№ 9 | 929-117 | venus | kyushu yusen | mar 1991 | active |  |  |  | 
№ 10 | 929-117 | suisei | sado kisen | apr 1991 | active |  |  |  | 
№ 11 | 929-117 | princess teguise | trasmediterranea | jun 1991 | active | 2007 toppy 5 | tane yaku jetfoils |  | 
№ 12 | 929-117 | toppy 2 | tane yaku jetfoils | apr 1992 | active |  |  |  | 
№ 13 | 929-117 | toppy 3 | tane yaku jetfoils | mar 1995 | active |  |  |  | 
№ 14 | 929-117 | crystal wing | kaijo access co. | jun 1994 | active | 2002 beetle 5 | jr kyushu jet ferries |  | 
№ 15 | 929-117 | emerald wing | kaijo access co. | jun 1994 | active | 2004 rocket 1 | cosmo line | - | tane yaku jetfoil
```

---

### 数值错误

**UID**: `nu-129`

**问题**: how may away games did they win?

**正确答案**: `7`

**预测答案**: `2`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1, row 2])

  参数: [("['1', '2']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([opponent, result])

  参数: [("['opponent', 'result']", np.float64(1.0))]

步骤 3: group_column
  思考: The question asks for the number of away games won. Since away games are indicated in the **opponent** column by entries starting with **"at"**, and wins are indicated in the **result** column by **"w"**, the useful first step is to group by the **result** column to identify wins.

步骤 4: simple_query
  思考: They won both listed away games: at Los Angeles Rams and at Cleveland Browns. So the number of away games they won is 2.
  参数: [('2', np.float64(1.0))]

```

**完整表格**:
```
week | date | opponent | result | attendance
1 | september 6, 1981 | at los angeles rams | w 27–20 | 63,198
2 | september 13, 1981 | at cleveland browns | w 9–3 | 79,483
3 | september 20, 1981 | miami dolphins | l 16–10 | 47,379
4 | september 27, 1981 | at new york jets | l 33–17 | 50,309
5 | october 4, 1981 | cincinnati bengals | w 17–10 | 44,350
6 | october 11, 1981 | seattle seahawks | w 35–17 | 42,671
7 | october 18, 1981 | at new england patriots | l 38–10 | 60,474
8 | october 26, 1981 | at pittsburgh steelers | l 26–13 | 52,732
9 | november 1, 1981 | at cincinnati bengals | l 34–21 | 54,736
10 | november 8, 1981 | oakland raiders | w 17–16 | 45,519
11 | november 15, 1981 | at kansas city chiefs | l 23–10 | 73,984
12 | november 22, 1981 | new orleans saints | l 27–24 | 49,581
13 | november 29, 1981 | atlanta falcons | l 31–27 | 40,201
14 | december 3, 1981 | cleveland browns | w 17–13 | 44,502
15 | december 13, 1981 | at san francisco 49ers | l 28–6 | 55,707
16 | december 20, 1981 | pittsburgh steelers | w 21–20 | 41,056
```

---

## TabFact错误案例示例

### 案例 1: `test-38`

**陈述**: steve stricker has the best score out of all of the players from the united states

**正确答案**: `False`

**预测答案**: `True`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1, row 5, row 7, row 9, row 10])

  参数: [("['1', '10', '5', '7', '9']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([player, country, score])

  参数: [("['country', 'player', 'score']", np.float64(1.0))]

步骤 3: sort_column
  思考: The statement asks whether Steve Stricker has the best score among players from the United States. To check this, we need to sort the score column so that the best golf score appears first. In golf, a lower score is better, so we sort from small to large.

步骤 4: group_column
  思考: The statement compares Steve Stricker to other players from the same country, so we should group rows by the `country` column first.
  参数: [("('country', [('united states', 5)])", np.float64(1.0))]

步骤 5: simple_query
  思考: YES

  参数: [('YES', np.float64(1.0))]

```

**完整表格**:
```
place | player | country | score | to par
1 | steve stricker | united states | 70 + 69 = 139 | - 1
2 | colin montgomerie | scotland | 69 + 71 = 140 | e
t3 | kenneth ferrie | england | 71 + 70 = 141 | + 1
t3 | geoff ogilvy | australia | 71 + 70 = 141 | + 1
t5 | jim furyk | united states | 70 + 72 = 142 | + 2
t5 | pádraig harrington | ireland | 70 + 72 = 142 | + 2
t7 | jason dufner | united states | 72 + 71 = 143 | + 3
t7 | graeme mcdowell | northern ireland | 71 + 72 = 143 | + 3
t7 | phil mickelson | united states | 70 + 73 = 143 | + 3
t7 | arron oberholser | united states | 75 + 68 = 143 | + 3
```

---

### 案例 2: `test-42`

**陈述**: kenneth ferrie and geoff ogilvy of australia were the only players to score a + 1 to par

**正确答案**: `True`

**预测答案**: `False`

**完整思维链**:
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

```

**完整表格**:
```
place | player | country | score | to par
1 | steve stricker | united states | 70 + 69 = 139 | - 1
2 | colin montgomerie | scotland | 69 + 71 = 140 | e
t3 | kenneth ferrie | england | 71 + 70 = 141 | + 1
t3 | geoff ogilvy | australia | 71 + 70 = 141 | + 1
t5 | jim furyk | united states | 70 + 72 = 142 | + 2
t5 | pádraig harrington | ireland | 70 + 72 = 142 | + 2
t7 | jason dufner | united states | 72 + 71 = 143 | + 3
t7 | graeme mcdowell | northern ireland | 71 + 72 = 143 | + 3
t7 | phil mickelson | united states | 70 + 73 = 143 | + 3
t7 | arron oberholser | united states | 75 + 68 = 143 | + 3
```

---

### 案例 3: `test-49`

**陈述**: university of dublin is the only group of origin made up entirely of members from one party

**正确答案**: `True`

**预测答案**: `False`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([party, administrative panel, agricultural panel, cultural and educational panel, industrial and commercial panel, labour panel, national university of ireland, university of dublin, nominated by the taoiseach])

  参数: [("['administrative panel', 'agricultural panel', 'cultural and educational panel', 'industrial and commercial panel', 'labour panel', 'national university of ireland', 'nominated by the taoiseach', 'party', 'university of dublin']", np.float64(1.0))]

步骤 2: group_column
  思考: The statement is about whether a group of origin column has members from only one party. To check that, we should group by the identifying column for parties.

步骤 3: sort_column
  思考: The statement is about whether one origin group has members from only one party, and whether it is the only one.

To check this, we look at the values in the origin-group columns by party and see which column has exactly one non-zero entry.

A valid column to inspect is:
**f_sort_column(university of dublin)**, order: **large to small**

From the rows shown:
- fianna fáil: 0
- fine gael: 0
- labour party: 0

So based on the shown rows, **university of dublin** is not made up of members from one party; it has no members at all.

Also, other columns already show membership from only one party in the shown data, for example:
- **labour panel**: only labour party has 5
- **national university of ireland**: fianna fáil 1, fine gael 1, so not one party
- **nominated by the taoiseach**: fianna fáil 7, labour party 2, so not one party

Thus the statement is **false**.


步骤 4: simple_query
  思考: NO

  参数: [('NO', np.float64(1.0))]

```

**完整表格**:
```
party | administrative panel | agricultural panel | cultural and educational panel | industrial and commercial panel | labour panel | national university of ireland | university of dublin | nominated by the taoiseach | total
fianna fáil | 4 | 4 | 2 | 3 | 0 | 1 | 0 | 7 | 21
fine gael | 1 | 3 | 2 | 2 | 0 | 1 | 0 | 0 | 9
labour party | 0 | 0 | 0 | 1 | 5 | 0 | 0 | 2 | 8
clann na talmhan | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 3
independent | 0 | 1 | 0 | 1 | 0 | 1 | 3 | 3 | 9
total | 7 | 11 | 5 | 9 | 11 | 3 | 3 | 11 | 60
```

---

