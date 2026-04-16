# 最终版综合Bad Case分析报告

**生成时间**: 2026-04-16

---

# 汇总统计

- **WikiTQ错误案例**: 42
- **TabFact错误案例**: 16
- **总错误案例**: 58

# 错误案例ID分类表

| 数据集 | 错误类型 | 错误案例ID | 数量 |
|-------|---------|-----------|------|
| WikiTQ | 多答案处理错误 | test-332, test-950, test-1705, test-1913, test-2194, test-3391 | 6 |
| WikiTQ | 实体识别/理解错误 | test-320, test-1099, test-1121, test-1423, test-1448, test-1873, test-1969, test-2562, test-2729, test-3192, test-4062 | 11 |
| WikiTQ | 数值错误 | test-82, test-122, test-245, test-1014, test-1730, test-1798, test-1867, test-1936, test-1977, test-2026, test-2467, test-2516, test-2550, test-2723, test-2724, test-2888, test-2929, test-2974, test-3070, test-3290, test-3312, test-3550, test-3782, test-4169, test-4300 | 25 |
| TabFact | 布尔判断错误 | test-42, test-443, test-650, test-915, test-920, test-925, test-1040, test-1218, test-1261, test-1354, test-1392, test-1399, test-1878, test-1895, test-1929, test-1992 | 16 |

---

# WikiTQ详细案例分析（前10个案例）

## 案例 1: 数值错误

**UID**: `test-82`

**问题**: how many teams did not score any goals in the 2006 season?

**正确答案**: `1`

**预测答案**: `0`

**表格数据**:
```
season | team | country | division | apps | goals
2004 | cska moscow | russia | 1 | 0 | 0
2005 | cska moscow | russia | 1 | 0 | 0
2006 | spartak nizhny novgorod | russia | 2 | 36 | 1
2006/07 | dnipro dnipropetrovsk | ukraine | 1 | 12 | 0
2007/08 | dnipro dnipropetrovsk | ukraine | 1 | 24 | 0
2008/09 | dnipro dnipropetrovsk | ukraine | 1 | 22 | 1
2009/10 | dnipro dnipropetrovsk | ukraine | 1 | 28 | 0
...
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
  思考: Explanation: The resulting sub-table shows the 2006 season for Spartak Nizhny Novgorod, and the number of goals is 1. Since 1 is not 0, there were no teams in the extracted result that did not score a...
  参数: [('0', np.float64(1.0))]
```

---

## 案例 2: 数值错误

**UID**: `test-122`

**问题**: how many designers do not have an associated publication?

**正确答案**: `6`

**预测答案**: `10`

**表格数据**:
```
year | designer(s) | brief description | selected by: | associated publication
1963 | mary quant\nreed crawford (hat | grey wool 'rex harrison' pinaf | members of the fashion writers | 
1964 | jean muir for jane & jane\ncha | dress in printed liberty silk | members of the fashion writers | 
1965 | john bates for jean varon\nane | printed linen dress with mesh  | members of the fashion writers | 
1966 | michèle rosier of v de v (coat | clear plastic raincoat and boo | ernestine carter | the sunday times
1967 | david bond for slimma\nedward  | woman's trouser suit, hat & bl | felicity green | the daily mirror
1968 | jean muir\nbally (shoes) | black-spotted white cotton voi | ailsa garland | fashion magazine
1969 | ossie clark for quorum\nrayne  | woman's silk chiffon and satin | prudence glynn | the times
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([designer(s), associated publication])

  参数: [("['associated publication', 'designer(s)']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks for entries where the associated publication is missing, so we should group by the "associated publication" column to identify the blank/non-blank groups.
  参数: [('(\'associated publication\', [(\'\', 6), (\'the sunday times\', 4), (\'the times\', 4), (\'vogue\', 4), (\'the daily telegraph\', 3), (\'brides\', ...

步骤 3: simple_query
  思考: To answer “how many designers do not have an associated publication?”, we must count the individual designer entries in rows where the **associated publication** cell is empty, rather than just counti...
  参数: [('10', np.float64(1.0))]
```

---

## 案例 3: 数值错误

**UID**: `test-245`

**问题**: how many singles are only a single and not apart of an album?

**正确答案**: `18`

**预测答案**: `3`

**表格数据**:
```
year | single | peak chart\npositions\nus coun | peak chart\npositions\ncan cou | album
1967 | "forbidden fruit" | — | — | a world called you
1968 | "i'd be your fool again" | 69 | — | a world called you
1968 | "i'm in love with my wife" | 38 | — | a world called you
1968 | "you touched my heart" | 37 | — | a world called you
1969 | "dearly beloved" | 59 | — | single only
1969 | "a world called you" | 23 | — | a world called you
1970 | "so much in love with you" | 46 | — | a world called you
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([single, album])

  参数: [("['album', 'single']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks for singles whose `album` indicates they are not part of an album, i.e. `"single only"`. To analyze that, group by the `album` column.
  参数: [('(\'album\', [(\'singles only\', 15), (\'a world called you\', 6), (\'lovingly\', 4), (\'hey there girl\', 3), (\'single only\', 3), (\'just thank m...

步骤 3: simple_query
  思考: To find how many singles were only a single and not part of an album, look at the `album` column and count the rows labeled **"single only"**. The grouped result shows **"single only" = 3**. Although ...
  参数: [('3', np.float64(1.0))]
```

---

## 案例 4: 实体识别/理解错误

**UID**: `test-320`

**问题**: which is the only tournament with a british runner-up?

**正确答案**: `Tsuruya Open`

**预测答案**: `cannot be determined`

**表格数据**:
```
no. | date | tournament | winning score | margin of\nvictory | runner(s)-up
1 | 3 nov 2002 | philip morris k.k. championshi | −19 (65-67-67-70=269) | 2 strokes | toshimitsu izawa
2 | 10 aug 2003 | sun chlorella classic | −8 (71-73-68-68=280) | 1 stroke | daisuke maruyama, taichi teshi
3 | 25 apr 2004 | tsuruya open | −9 (64-73-69-69=275) | 2 strokes | keiichiro fukabori, scott layc
4 | 26 jun 2004 | gateway to the open mizuno ope | −14 (67-68-70-69=274) | playoff | hiroaki iijima
5 | 23 apr 2006 | tsuruya open | −11 (70-68-66-69=273) | 2 strokes | mamo osanai
6 | 22 apr 2007 | tsuruya open | −16 (67-65-68-68=268) | 2 strokes | masahiro kuramoto, hirofumi mi
7 | 11 nov 2007 | mitsui sumitomo visa taiheiyo  | −13 (67-68-69-70=274) | 5 strokes | toru taniguchi
...
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([tournament, runner(s)-up])

  参数: [("['runner(s)-up', 'tournament']", np.float64(1.0))]

步骤 3: group_column
  思考: To determine **which tournament is the only one with a British runner-up**, we should group entries by the **runner(s)-up** column, since that column contains the people whose nationality we need to i...

步骤 4: sort_column
  思考: f_filter(runner(s)-up, contains, british)


步骤 5: simple_query
  思考: The table includes the columns **tournament** and **runner(s)-up**, but it does **not** provide the nationalities of the runners-up. So although names such as **Scott Laycock** appear in the runner-up...
  参数: [('cannot be determined', np.float64(1.0))]
```

---

## 案例 5: 多答案处理错误

**UID**: `test-332`

**问题**: what year did poland achieve its highest position?

**正确答案**: `2010`

**预测答案**: `1999|2003`

**表格数据**:
```
year | competition | venue | position | notes
1999 | world youth championships | bydgoszcz, poland | 13th (q) | 4.60 m
2001 | european junior championships | grosseto, italy | 7th | 5.15 m
2002 | world junior championships | kingston, jamaica | 8th | 5.30 m
2003 | european u23 championships | bydgoszcz, poland | 13th (q) | 5.20 m
2005 | european u23 championships | erfurt, germany | 7th | 5.50 m
2005 | universiade | izmir, turkey | 5th | 5.50 m
2006 | world indoor championships | moscow, russia | 10th (q) | 5.65 m
...
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

To find the highest position, compare the rankings. In athletics, a higher posit...
  参数: [('1999|2003', np.float64(1.0))]
```

---

## 案例 6: 多答案处理错误

**UID**: `test-950`

**问题**: which contestants are below age 18?

**正确答案**: `Isabelle Raisa`

**预测答案**: `isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia maria hausmair`

**表格数据**:
```
contestant | age | height | home city | rank
isabelle raisa | 16 | 170 cm (5 ft 7 in) | vienna | eliminated in episode 1
alina chlebecek | 18 | 170 cm (5 ft 7 in) | deutsch-wagram | eliminated in episode 1
sabrina angelika rauch † | 21 | 175 cm (5 ft 9 in) | graz | eliminated in episode 2
katharina mihalović | 23 | 179 cm (5 ft 10.5 in) | vienna | eliminated in episode 2
nataša marić | 16 | 175 cm (5 ft 9 in) | liefering (originally from ser | eliminated in episode 3
michaela schopf | 21 | 172 cm (5 ft 7.5 in) | salzburg (originally from germ | quit in episode 4
christine riener | 20 | 181 cm (5 ft 11.25 in) | bludenz | eliminated in episode 4
...
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
  参数: [('isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia maria hausmair', np.float64(1.0))]

步骤 4: simple_query
  思考: Explanation: The extracted sub-table shows six contestants with ages 16 or 17, and both ages are below 18. Therefore, the contestants below age 18 are Isabelle Raisa, Nataša Marić, Teodora-Mădălina An...
  参数: [('isabelle raisa|nataša marić|teodora-mădălina andreica|yemisi rieger|gina zeneb adamu|antonia maria hausmair', np.float64(1.0))]
```

---

## 案例 7: 数值错误

**UID**: `test-1014`

**问题**: how many models utilize diesel as their fuel type?

**正确答案**: `110`

**预测答案**: `64`

**表格数据**:
```
model | fuel type | mpg (us gallons) | l/100 km | nz rating\n(stars)
volkswagen polo 1.4 tdi bluemo | diesel | 62 | 3.8 | 5.5
volkswagen polo 1.4 tdi 5m | diesel | 52 | 4.5 | 5.5
volkswagen polo 1.4 man | petrol | 36.7 | 6.4 | 4.5
volkswagen polo 1.4 6a | petrol | 34 | 6.9 | 4.5
fiat 500 1.3 jtd pop | diesel | 56 | 4.2 | 5.5
fiat 500 1.2 pop | petrol | 46 | 5.1 | 5
fiat 500 1.4 lounge 3d | petrol | 37.3 | 6.3 | 4.5
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([model, fuel type])

  参数: [("['fuel type', 'model']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks to count models with fuel type equal to diesel, so we should group by the fuel type column.
  参数: [("('fuel type', [('diesel', 111), ('petrol', 65)])", np.float64(1.0))]

步骤 3: simple_query
  思考: To answer “how many models utilize diesel as their fuel type?”, look at the `fuel type` column and count the rows labeled `diesel` in the provided sub-table. The critique notes that the grouped count ...
  参数: [('64', np.float64(1.0))]
```

---

## 案例 8: 实体识别/理解错误

**UID**: `test-1099`

**问题**: what percent do the top 3 make up?

**正确答案**: `89.17`

**预测答案**: `77.85%`

**表格数据**:
```
language | 2001 census[1]\n(total populat | 1991 censusindian census [2]\n | 1991 censusindian census [2]\n | 
 | speakers | speakers | percentage | 
hindi | 422,048,642 | 337,272,114 | 40.0% | 336 m
bengali | 230,000,000 | 200,595,738 | 28.30% | 320 m
punjabi | 130,000,000 | 100,017,615 | 20.87% | 113 m
telugu | 70,002,856 | 65,595,738 | 8.30% | 70 m
marathi | 71,936,894 | 62,481,681 | 7.45% | 68.0 m
tamil | 60,793,814 | 53,006,368 | 6.32% | 66.0 m
...
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
  思考: Explanation: The top 3 languages have populations of 422,048,642, 230,000,000, and 130,000,000. Adding them gives 782,048,642. The total population is 1,004.59 million, or 1,004,590,000. Dividing 782,...
  参数: [('77.85%', np.float64(1.0))]
```

---

## 案例 9: 实体识别/理解错误

**UID**: `test-1121`

**问题**: who started directly before canby?

**正确答案**: `Alan C. Kohn`

**预测答案**: `alan c. kohn`

**表格数据**:
```
clerk | started | finished | school (year) | previous clerkship
kenneth w. dam | 1957 | 1958 | chicago (1957) | none
alan c. kohn | 1957 | 1958 | wash u (1955) | none
william c. canby, jr. | 1958 | 1959 | minnesota (1956) | none
heywood h. davis | 1958 | 1959 | kansas (1958) | none
jerome b. libin | 1959 | 1960 | michigan (1959) | none
patrick f. mccartan | 1959 | 1960 | notre dame (1959) | none
d. lawrence gunnels | 1961 | 1962 | wash u (1960) | none
```

**思维链**:
```
步骤 1: select_row
  思考: Select relevant rows.
The question asks for who started directly before William C. Canby, Jr. In the table, Canby is row 3 with started = 1958. The immediately earlier start year is 1957, which corres...
  参数: [("['1', '2']", np.float64(1.0))]

步骤 2: sort_column
  思考: f_sort_column(started), the order is "small to large".


步骤 3: select_column
  思考: f_select_column([clerk, started])

  参数: [("['clerk', 'started']", np.float64(1.0))]

步骤 4: simple_query
  思考: Explanation: The sub-table shows two clerks, Kenneth W. Dam and Alan C. Kohn, and both have the same start year, 1957. Since the question asks who started directly before Canby, the person immediately...
  参数: [('alan c. kohn', np.float64(1.0))]
```

---

## 案例 10: 实体识别/理解错误

**UID**: `test-1423`

**问题**: which country received the most box office revenue from national films in 2013?

**正确答案**: `China`

**预测答案**: `China`

**表格数据**:
```
rank | country | box office | year | box office\nfrom national film
1 | canada/united states | $10.8 billion | 2012 | –
2 | china | $3.6 billion | 2013 | 59% (2013)
3 | japan | $1.88 billion | 2013 | 61% (2013)
4 | united kingdom | $1.7 billion | 2012 | 36.1% (2011)
5 | france | $1.7 billion | 2012 | 33.3% (2013)
6 | south korea | $1.47 billion | 2013 | 59.7% (2013)
7 | india | $1.4 billion | 2012 | –
...
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 2, row 3, row 6, row 11, row 12])

  参数: [("['11', '12', '2', '3', '6']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([country, box office, year, box office\nfrom national films])

  参数: [("['box office', 'box office\\\\nfrom national films', 'country', 'year']", np.float64(1.0))]

步骤 3: sort_column
  思考: To answer this, sort the column **box office from national films** in **large to small** order.

**

步骤 4: simple_query
  思考: Explanation: To find which country received the most box office revenue from national films in 2013, multiply each country's total box office by the percentage from national films.

- China: $3.6 bill...
  参数: [('china', np.float64(1.0))]

步骤 5: group_column
  思考: To answer the question, we need to compare countries based on their box office revenue from national films in 2013. Since the table already includes the year and the percentage of box office from nati...
  参数: [("('year', [('2013', 5)])", np.float64(1.0))]

步骤 6: simple_query
  思考: Explanation: To find which country received the most box office revenue from national films in 2013, multiply each country’s total box office by the percentage from national films. China: $3.6 billion...
  参数: [('China', np.float64(1.0))]
```

---


---

# TabFact详细案例分析（前10个案例）

## 案例 1: 布尔判断错误

**UID**: `test-42`

**陈述**: kenneth ferrie and geoff ogilvy of australia were the only players to score a + 1 to par

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
place | player | country | score | to par
1 | steve stricker | united states | 70 + 69 = 139 | - 1
2 | colin montgomerie | scotland | 69 + 71 = 140 | e
t3 | kenneth ferrie | england | 71 + 70 = 141 | + 1
t3 | geoff ogilvy | australia | 71 + 70 = 141 | + 1
t5 | jim furyk | united states | 70 + 72 = 142 | + 2
t5 | pádraig harrington | ireland | 70 + 72 = 142 | + 2
t7 | jason dufner | united states | 72 + 71 = 143 | + 3
...
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
- T...

步骤 4: simple_query
  思考: Explanation: In the sub-table, the only two players with a to par score of +1 are Kenneth Ferrie and Geoff Ogilvy, so that part is correct. However, the statement says "Kenneth Ferrie and Geoff Ogilvy...
  参数: [('NO', np.float64(1.0))]

步骤 5: simple_query
  思考: Explanation: The grouped table shows exactly 2 players with a score of +1 to par: Kenneth Ferrie and Geoff Ogilvy. However, the statement says “Kenneth Ferrie and Geoff Ogilvy of Australia,” which imp...
  参数: [('NO', np.float64(1.0))]
```

---

## 案例 2: 布尔判断错误

**UID**: `test-443`

**陈述**: only two teams (hawthorn and south melbourne) scored less than 10

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
home team | home team score | away team | away team score | venue | crowd | date
geelong | 11.23 (89) | hawthorn | 6.13 (49) | corio oval | 7000 | 18 june 1938
fitzroy | 16.12 (108) | south melbourne | 8.8 (56) | brunswick street oval | 12000 | 18 june 1938
st kilda | 14.12 (96) | melbourne | 16.16 (112) | junction oval | 14000 | 18 june 1938
richmond | 15.14 (104) | essendon | 15.9 (99) | punt road oval | 20000 | 18 june 1938
footscray | 13.9 (87) | collingwood | 10.5 (65) | western oval | 18000 | 18 june 1938
north melbourne | 11.5 (71) | carlton | 16.25 (121) | arden street oval | 13000 | 18 june 1938
```

**思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([home team, home team score, away team, away team score])

  参数: [("['away team', 'away team score', 'home team', 'home team score']", np.float64(1.0))]

步骤 3: sort_column
  思考: Explanation: The statement asks whether only two teams, hawthorn and south melbourne, scored less than 10. To check this, we need the score columns and identify scores below 10. The relevant sortable ...

步骤 4: group_column
  思考: The statement is about how many teams have scores less than 10, so we should group rows by the score values in the score columns to identify those cases.

步骤 5: simple_query
  思考: Explanation: We check which teams scored less than 10 goals from both the home team score and away team score columns. The scores under 10 are Hawthorn with 6.13 and South Melbourne with 8.8. All othe...
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 3: 布尔判断错误

**UID**: `test-650`

**陈述**: the number 2 is the only erp w

**正确标签**: `False`

**预测标签**: `Unknown`

**表格数据**:
```
call sign | frequency mhz | city of license | erp w | class | fcc info
w221by | 92.1 | elgin , illinois | 38 | d | fcc
w264bf | 100.7 | englewood , illinois | 2 | d | fcc
w240bj | 95.9 | crown point , indiana | 10 | d | fcc
w276bm | 103.1 | park forest , illinois | 19 | d | fcc
w293al | 106.5 | rochester , indiana | 80 | d | fcc
w223au | 92.5 | south bend , indiana | 10 | d | fcc
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([erp w])

  参数: [("['erp w']", np.float64(1.0))]

步骤 2: group_column
  思考: The statement is about whether a specific value appears only once in column **erp w**.  
So we should group the values in that column.

**

步骤 3: sort_column
  思考: The statement asks whether 2 is the only value in the column `erp w`. To check this, we would look for duplicates/equality, not sort order. Sorting does not determine whether a value is the only one.

步骤 4: simple_query
  思考: The `erp w` values in the table are 38, 2, 10, 19, 80, and 10. The value `2` appears once, and no other `erp w` value is 2. Therefore, the number 2 is the only `erp w` equal to 2, so the statement is ...
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 4: 布尔判断错误

**UID**: `test-915`

**陈述**: on september 22nd 23 , 3380 people witnessed a win against the yankees of 8 - 1

**正确标签**: `False`

**预测标签**: `Unknown`

**表格数据**:
```
date | opponent | score | loss | attendance | record
september 1 | mets | 3 - 0 | hentgen (14 - 9) | 19196 | 65 - 71
september 2 | mets | 8 - 5 | clemens (20 - 5) | 17635 | 65 - 72
september 3 | mets | 4 - 2 | quantrill (6 - 6) | 14513 | 65 - 73
september 4 | rangers | 6 - 2 | carpenter (1 - 7) | 26178 | 65 - 74
september 5 | rangers | 5 - 1 | pavlik (2 - 4) | 27121 | 66 - 74
september 6 | rangers | 2 - 1 | burkett (7 - 12) | 31232 | 67 - 74
september 7 | rangers | 4 - 0 | oliver (11 - 11) | 30212 | 68 - 74
...
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 21])

  参数: [("['21']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([date, opponent, score, attendance])

  参数: [("['attendance', 'date', 'opponent', 'score']", np.float64(1.0))]

步骤 3: simple_query
  思考: NO

  参数: [('NO', np.float64(1.0))]

步骤 4: simple_query
  思考: Explanation: The extracted row shows that on September 22, the Blue Jays played the Yankees, won 8–1, and the attendance was 23,380. This matches the statement exactly.
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 5: 布尔判断错误

**UID**: `test-920`

**陈述**: the blue jays fell to 76 - 86 following their loss to the red sox on september 28

**正确标签**: `False`

**预测标签**: `Unknown`

**表格数据**:
```
date | opponent | score | loss | attendance | record
september 1 | mets | 3 - 0 | hentgen (14 - 9) | 19196 | 65 - 71
september 2 | mets | 8 - 5 | clemens (20 - 5) | 17635 | 65 - 72
september 3 | mets | 4 - 2 | quantrill (6 - 6) | 14513 | 65 - 73
september 4 | rangers | 6 - 2 | carpenter (1 - 7) | 26178 | 65 - 74
september 5 | rangers | 5 - 1 | pavlik (2 - 4) | 27121 | 66 - 74
september 6 | rangers | 2 - 1 | burkett (7 - 12) | 31232 | 67 - 74
september 7 | rangers | 4 - 0 | oliver (11 - 11) | 30212 | 68 - 74
...
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
  思考: On september 28, the Blue Jays played the Red Sox and their record became 76 - 86, but the score was 3 - 2, which indicates a win rather than a loss. Therefore, the statement saying they fell to 76 - ...
  参数: [('NO', np.float64(1.0))]
```

---

## 案例 6: 布尔判断错误

**UID**: `test-925`

**陈述**: there were 2.4 blocks per game in the selection where not field goal percentage was 594 (2nd)

**正确标签**: `False`

**预测标签**: `Unknown`

**表格数据**:
```
selection | month | season | team record | points per game | field goal percentage | rebounds per game | blocks per game
1 | april 2006 | 2005 - 06 (1 / 1) | 7-2 | 18.1 | 531 | 14.0 | 0.7
2 | october / november 2006 | 2006 - 07 (1 / 1) | 12-4 | 17.1 | 576 | 13.6 | 1.9
3 | october / november 2007 | 2007 - 08 (1 / 2) | 14-4 | 23.8 | 618 | 15.0 | 2.7
4 | december 2007 | 2007 - 08 (2 / 2) | 8-7 | 21.7 | 598 | 16.1 | 2.9
5 | october / november 2010 | 2010 - 11 (1 / 2) | 13-4 | 21.8 (5th) | 594 (2nd) | 12.1 (4th in league) | 2.4
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 5])

  参数: [("['5']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([selection, field goal percentage, blocks per game])

  参数: [("['blocks per game', 'field goal percentage', 'selection']", np.float64(1.0))]

步骤 3: simple_query
  思考: Explanation: In the extracted sub-table, the row where the field goal percentage is 594 (2nd) shows blocks per game as 2.4. This matches the statement exactly, so the statement is true.
  参数: [('YES', np.float64(1.0))]

步骤 4: simple_query
  思考: Explanation: The extracted sub-table shows that for selection 5, the field goal percentage is 594 (2nd) and the blocks per game value is 2.4. This matches the statement exactly. Therefore, the stateme...
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 7: 布尔判断错误

**UID**: `test-1040`

**陈述**: the first record was recorded in november of the year 1965

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
name | total | first | last | highest rank
kotonishiki | 34 | september 1990 | september 1999 | sekiwake
kaiō | 32 | may 1994 | july 2000 | ōzeki
musōyama | 31 | march 1994 | september 2000 | ōzeki
hasegawa | 30 | november 1965 | september 1974 | sekiwake
kotomitsuki | 30 | january 2001 | july 2007 | ōzeki
akinoshima | 27 | november 1988 | september 2000 | sekiwake
takamiyama | 27 | november 1969 | september 1982 | sekiwake
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([first])

  参数: [("['first']", np.float64(1.0))]

步骤 2: sort_column
  思考: The statement is asking whether the **first record** corresponds to a certain **date**.  
To check this, we should sort the **first** column by date.

- Column name: **first**
- Data type: **DateType*...

步骤 3: simple_query
  思考: Explanation: The sub-table shows multiple "first" recorded dates. The earliest year listed is November 1965, which appears in row 4. Therefore, the first record was recorded in November 1965, so the s...
  参数: [('YES', np.float64(1.0))]

步骤 4: simple_query
  思考: Explanation: The "first" column lists when each record was first recorded. Among the entries shown, one of them is "november 1965," but it is not the earliest date overall because there is also "novem...
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 8: 布尔判断错误

**UID**: `test-1218`

**陈述**: jonathan legear scored four more goals than matias suarez , the next highest ranked player in the belgian first dvision a league who played in the belgian cup

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
player | league | title playoff | super cup | total
mbark boussoufa | 11 | 0 | 0 | 11
tom de sutter | 9 | 0 | 0 | 9
guillaume gillet | 8 | 0 | 0 | 9
marcin wasilewski | 8 | 0 | 0 | 8
jonathan legear | 5 | 1 | 0 | 7
nicolás frutos | 6 | 0 | 0 | 6
thomas chatelle | 4 | 0 | 0 | 4
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([player, league])

  参数: [("['league', 'player']", np.float64(1.0))]

步骤 2: sort_column
  思考: f_sort_column(league), the order is "large to small".


步骤 3: simple_query
  思考: Explanation: From the sub-table, Jonathan Legear scored 5 league goals and Matías Suárez scored 1 league goal. The difference is 4 goals. However, the statement says Matías Suárez was “the next highes...
  参数: [('NO', np.float64(1.0))]
```

---

## 案例 9: 布尔判断错误

**UID**: `test-1261`

**陈述**: shane hall had an average finish of 31.39 between 1995 - 2008

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
year | races | wins | poles | top 5 | top 10 | dnf | finish | start | winnings | season rank | team (s)
1995 | 2 | 0 | 0 | 0 | 0 | 0 | 24.0 | 37.0 | 5225 | 75th | stegell motorsports
1996 | 14 | 0 | 0 | 0 | 0 | 6 | 26.4 | 25.1 | 63865 | 42nd | stegell motorsports
1997 | 28 | 0 | 1 | 0 | 1 | 10 | 27.1 | 21.6 | 196656 | 23rd | stegell motorsports
1998 | 31 | 0 | 1 | 0 | 3 | 5 | 24.9 | 25.5 | 335163 | 19th | stegell motorsports
1999 | 25 | 0 | 0 | 1 | 1 | 9 | 25.8 | 18.2 | 243810 | 24th | curb - agajanian performance g
2000 | 2 | 0 | 0 | 0 | 0 | 1 | 35.0 | 28.5 | 15900 | 90th | alumni motorsports
2001 | 33 | 0 | 0 | 0 | 0 | 6 | 27.9 | 32.7 | 491977 | 23rd | hensley racing
...
```

**思维链**:
```
步骤 1: select_column
  思考: f_select_column([year, finish])

  参数: [("['finish', 'year']", np.float64(1.0))]

步骤 2: simple_query
  思考: The `finish` values from 1995 through 2008 are:

24.0, 26.4, 27.1, 24.9, 25.8, 35.0, 27.9, 27.0, 35.8, 31.4, 40.9, 38.9, 43.0.

Their sum is 408.1, and there are 13 years listed.  
408.1 ÷ 13 = 31.392...
  参数: [('YES', np.float64(1.0))]
```

---

## 案例 10: 布尔判断错误

**UID**: `test-1354`

**陈述**: for all 28 matches that atletico ciudad played , his average was never below 0.61

**正确标签**: `True`

**预测标签**: `Unknown`

**表格数据**:
```
goalkeeper | goals | matches | average | team
miguel zapata | 17 | 28 | 0.61 | atlético ciudad
rubén martínez | 24 | 32 | 0.75 | cartagena
orlando quintana | 29 | 34 | 0.85 | lorca deportiva
álvaro campos | 24 | 28 | 0.86 | real murcia b
matías garavano | 26 | 30 | 0.87 | mérida
```

**思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 1])

  参数: [("['1']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([matches, average, team])

  参数: [("['average', 'matches', 'team']", np.float64(1.0))]

步骤 3: simple_query
  思考: The table shows that Atlético Ciudad played 28 matches and had an overall average of 0.61. However, the statement says that for all 28 matches, the average was never below 0.61, which is a stronger cl...
  参数: [('NO', np.float64(1.0))]
```

---

