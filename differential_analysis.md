

---

# 第三部分：横向对比分析 - 当前项目特有错误案例

**生成时间**: 2026-04-16

**说明**: 本部分分析当前项目(new_TC)出错但参考项目(Table-Critic)正确的案例，这是当前项目的特有问题，需要重点改进。

**方法**: 使用官方评估函数（wikitq_match_func）判断bad case

## 汇总统计

- **当前项目特有错误案例总数**: 22
- **当前项目错误案例总数**: 689
- **参考项目错误案例总数**: 682
- **特有错误占比**: 3.2%

## 当前项目特有错误分类

### 其他错误

- **数量**: 6
- **占比**: 27.3%
- **ID列表**: nu-2904, nu-2522, nu-538, nu-811, nu-1448, nu-2445

### 多答案处理错误

- **数量**: 2
- **占比**: 9.1%
- **ID列表**: nu-1792, nu-2168

### 实体识别错误

- **数量**: 6
- **占比**: 27.3%
- **ID列表**: nu-58, nu-3507, nu-4311, nu-1055, nu-2562, nu-320

### 数值统计错误

- **数量**: 8
- **占比**: 36.4%
- **ID列表**: nu-82, nu-122, nu-1798, nu-245, nu-4300, nu-1867, nu-2756, nu-1477

## 当前项目特有错误案例详细分析

### 其他错误

#### 案例 1: `nu-2904`

**问题**: how many women competed in the 1997 world championships in athletics women's 5000 metres?

**正确答案**: `42`

**当前项目预测**: `**38**`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([*])

  参数: [("['*']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([name])

  参数: [("['name']", np.float64(1.0))]

步骤 3: simple_query
  思考: To answer how many women **competed** in the 1997 World Championships in Athletics women's 5000 metres, we count the athletes listed in the table but exclude those marked **dns** because **dns** means *did not start*, so they did not actually compete.

There are **42** women listed in total.  
Among them, **4** are marked **dns**.  

So, the number who actually competed is:

**42 - 4 = 38**
  参数: [('**38**', np.float64(1.0))]

```

**完整表格**:
```
heat | rank | name | result | notes
1 | 1 | gabriela szabo (rou) | 15:26.62 q | 
1 | 2 | paula radcliffe (gbr) | 15:27.25 q | 
2 | 3 | fernanda ribeiro (por) | 15:27.30 q | 
1 | 4 | harumi hiroyama (jpn) | 15:27.75 q | 
1 | 5 | roberta brunet (ita) | 15:29.03 q | 
2 | 6 | liu jianying (chn) | 15:29.28 q | pb
1 | 7 | ayelech worku (eth) | 15:29.37 q | 
1 | 8 | li wei (chn) | 15:29.62 q | 
1 | 9 | libbie hickman (usa) | 15:30.56 q | sb
2 | 10 | lydia cheromei (ken) | 15:32.00 q | 
2 | 11 | merima denboba (eth) | 15:32.01 q | 
1 | 12 | gunhild hall (nor) | 15:32.13 q | 
2 | 13 | naoko takahashi (jpn) | 15:32.25 q | 
2 | 14 | yuko kawakami (jpn) | 15:32.71 q | 
1 | 15 | kate anderson (aus) | 15:36.16 q | 
1 | 16 | yelena kopytova (rus) | 15:37.19 | pb
2 | 17 | sonia o'sullivan (irl) | 15:40.82 | 
2 | 18 | stela olteanu (rou) | 15:40.86 | 
1 | 19 | adriana fernandez (mex) | 15:41.55 | 
2 | 20 | olivera jevtić (yug) | 15:43.76 | 
1 | 21 | melody fairchild (usa) | 15:47.66 | 
2 | 22 | chrystosomia iakovou (gre) | 15:51.14 | 
1 | 23 | marina bastos (por) | 15:54.01 | 
2 | 24 | restituta joseph (tan) | 15:55.22 | nr
1 | 25 | valerie vaughan (irl) | 15:57.58 | 
1 | 26 | zohra ouaziz (mar) | 15:58.84 | 
2 | 27 | amy rudolph (usa) | 16:00.87 | 
1 | 28 | genet gebregiorgis (eth) | 16:04.40 | sb
1 | 29 | laurence duquenoy (fra) | 16:06.02 | 
2 | 30 | una english (irl) | 16:07.09 | 
2 | 31 | jelena chelnova (lat) | 16:27.63 | 
2 | 32 | helena javornik (slo) | 16:28.38 | 
1 | 33 | justine nahimana (bur) | 17:21.77 | 
1 | 34 | nebiat habtemariam (eri) | 18:26.50 | 
1 | 35 | zalia aliou (tog) | 18:34.45 | nr
1 | 36 | martha portobanco (nca) | 19:08.44 | 
2 | — | anne hare (nzl) | dnf | 
2 | — | kristina da fonseca-wollheim (ger) | dnf | 
1 | — | maysa matrood (irq) | dns | 
1 | — | elana meyer (rsa) | dns | 
2 | — | carol howe (can) | dns | 
2 | — | annemari sandell (fin) | dns | 
```

**原始表格**:
```
heat | rank | name | result | notes
1 | 1 | gabriela szabo (rou) | 15:26.62 q | 
1 | 2 | paula radcliffe (gbr) | 15:27.25 q | 
2 | 3 | fernanda ribeiro (por) | 15:27.30 q | 
1 | 4 | harumi hiroyama (jpn) | 15:27.75 q | 
1 | 5 | roberta brunet (ita) | 15:29.03 q | 
2 | 6 | liu jianying (chn) | 15:29.28 q | pb
1 | 7 | ayelech worku (eth) | 15:29.37 q | 
1 | 8 | li wei (chn) | 15:29.62 q | 
1 | 9 | libbie hickman (usa) | 15:30.56 q | sb
2 | 10 | lydia cheromei (ken) | 15:32.00 q | 
2 | 11 | merima denboba (eth) | 15:32.01 q | 
1 | 12 | gunhild hall (nor) | 15:32.13 q | 
2 | 13 | naoko takahashi (jpn) | 15:32.25 q | 
2 | 14 | yuko kawakami (jpn) | 15:32.71 q | 
1 | 15 | kate anderson (aus) | 15:36.16 q | 
1 | 16 | yelena kopytova (rus) | 15:37.19 | pb
2 | 17 | sonia o'sullivan (irl) | 15:40.82 | 
2 | 18 | stela olteanu (rou) | 15:40.86 | 
1 | 19 | adriana fernandez (mex) | 15:41.55 | 
2 | 20 | olivera jevtić (yug) | 15:43.76 | 
1 | 21 | melody fairchild (usa) | 15:47.66 | 
2 | 22 | chrystosomia iakovou (gre) | 15:51.14 | 
1 | 23 | marina bastos (por) | 15:54.01 | 
2 | 24 | restituta joseph (tan) | 15:55.22 | nr
1 | 25 | valerie vaughan (irl) | 15:57.58 | 
1 | 26 | zohra ouaziz (mar) | 15:58.84 | 
2 | 27 | amy rudolph (usa) | 16:00.87 | 
1 | 28 | genet gebregiorgis (eth) | 16:04.40 | sb
1 | 29 | laurence duquenoy (fra) | 16:06.02 | 
2 | 30 | una english (irl) | 16:07.09 | 
2 | 31 | jelena chelnova (lat) | 16:27.63 | 
2 | 32 | helena javornik (slo) | 16:28.38 | 
1 | 33 | justine nahimana (bur) | 17:21.77 | 
1 | 34 | nebiat habtemariam (eri) | 18:26.50 | 
1 | 35 | zalia aliou (tog) | 18:34.45 | nr
1 | 36 | martha portobanco (nca) | 19:08.44 | 
2 | — | anne hare (nzl) | dnf | 
2 | — | kristina da fonseca-wollheim (ger) | dnf | 
1 | — | maysa matrood (irq) | dns | 
1 | — | elana meyer (rsa) | dns | 
2 | — | carol howe (can) | dns | 
2 | — | annemari sandell (fin) | dns | 
```

---

#### 案例 2: `nu-2522`

**问题**: total years errea manufactured?

**正确答案**: `16`

**当前项目预测**: `cannot be determined`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 11, row 12, row 13, row 14, row 15, row 16, row 17])

  参数: [("['11', '12', '13', '14', '15', '16', '17']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([year, kit manufacturer])

  参数: [("['kit manufacturer', 'year']", np.float64(1.0))]

步骤 3: group_column
  参数: [("('kit manufacturer', [('errea', 7)])", np.float64(1.0))]

步骤 4: simple_query
  思考: The table shows that **Errea** is listed as the kit manufacturer for these year ranges: **1997–1999, 1999–2004, 2004–2008, 2008–, 2009–2011, 2011–2013, and 2013–**. However, these periods overlap and some are open-ended, so the table does not provide enough information to calculate one exact total number of years. Therefore, the total years Errea manufactured cannot be determined exactly from the table.
  参数: [('cannot be determined', np.float64(1.0))]

```

**完整表格**:
```
year | kit manufacturer | shirt sponsor | back of shirt sponsor | short sponsor
1977–1978 |  | national express |  | 
1982–1985 | umbro |  |  | 
1985–1986 | umbro | whitbread |  | 
1986–1988 | henson | duraflex |  | 
1988–1989 |  | gulf oil |  | 
1991–1993 | technik | gulf oil |  | 
1993–1994 | club sport | gulf oil |  | 
1994–1995 | klūb sport | empress |  | 
1995–1996 | matchwinner | empress |  | 
1996–1997 | uk | endsleigh insurance |  | 
1997–1999 | errea | endsleigh insurance |  | 
1999–2004 | errea | towergate insurance |  | 
2004–2008 | errea | bence building merchants |  | 
2008– | errea | mira showers |  | 
2009–2011 | errea | mira showers | psu technology group | 
2011–2013 | errea | mira showers | barr stadia | gloucestershire echo
2013– | errea | mira showers | gloucestershire college | gloucestershire echo
```

**原始表格**:
```
year | kit manufacturer | shirt sponsor | back of shirt sponsor | short sponsor
1977–1978 |  | national express |  | 
1982–1985 | umbro |  |  | 
1985–1986 | umbro | whitbread |  | 
1986–1988 | henson | duraflex |  | 
1988–1989 |  | gulf oil |  | 
1991–1993 | technik | gulf oil |  | 
1993–1994 | club sport | gulf oil |  | 
1994–1995 | klūb sport | empress |  | 
1995–1996 | matchwinner | empress |  | 
1996–1997 | uk | endsleigh insurance |  | 
1997–1999 | errea | endsleigh insurance |  | 
1999–2004 | errea | towergate insurance |  | 
2004–2008 | errea | bence building merchants |  | 
2008– | errea | mira showers |  | 
2009–2011 | errea | mira showers | psu technology group | 
2011–2013 | errea | mira showers | barr stadia | gloucestershire echo
2013– | errea | mira showers | gloucestershire college | gloucestershire echo
```

---

#### 案例 3: `nu-538`

**问题**: how long was the longest flight located in france.

**正确答案**: `1950 hours`

**当前项目预测**: `cannot be determined`

**完整思维链**:
```
步骤 1: add_column

步骤 2: select_row
  思考: f_select_row([row 1, row 2, row 3, row 4, row 5, row 6])

  参数: [("['1', '2', '3', '4', '5', '6']", np.float64(1.0))]

步骤 3: select_column
  思考: f_select_column([date/time, location])

  参数: [("['date/time', 'location']", np.float64(1.0))]

步骤 4: sort_column
  思考: To answer this question, we should identify the column that can determine “how long was the longest flight.” However, the available columns are only:

- date/time
- location

There is no column containing flight duration or length, so the question cannot be answered from the given table.

步骤 5: simple_query
  思考: The rows located in France are:

- 4 december 1916 @ 1100 hours — northeast of bapaume, france  
- 24 april 1917 @ 0840 hours — sailly, france  
- 2 may 1917 @ 0945 hours — douai, france  
- 11 may 1917 @ 1950 hours — douai, france  
- 11 may 1917 @ 1950 hours — douai, france  
- 23 may 1917 @ 1800 hours — douai, france  

However, the question asks “how long was the longest flight located in France,” and the table does not contain any flight duration column. The `date/time` values only show when the event happened, not how long the flight lasted. Therefore, the longest flight duration cannot be determined from this table.
  参数: [('cannot be determined', np.float64(1.0))]

```

**完整表格**:
```
no. | date/time | aircraft | foe | result | location | notes
1 | 4 december 1916 @ 1100 hours | nieuport serial number 3958 | albatros d.i | driven down out of control | northeast of bapaume, france | victory shared with another pilot
2 | 24 april 1917 @ 0840 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | sailly, france | 
3 | 2 may 1917 @ 0945 hours | sopwith triplane s/n n5460 | german two-seater aircraft | driven down out of control | douai, france | 
4 | 11 may 1917 @ 1950 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | douai, france | 
5 | 11 may 1917 @ 1950 hours | sopwith triplane s/n n5460 | albatros d.iii | set afire in midair; destroyed | douai, france | 
6 | 23 may 1917 @ 1800 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | douai, france | 
7 | 24 july 1917 @ 0635 hours | sopwith triplane s/n n5462 | german two-seater aircraft | driven down out of control | leffinghe | 
8 | 28 july 1917 @ 1735 hours | sopwith triplane s/n n5462 | german two-seater aircraft | driven down out of control | middelkerke, belgium | victory shared with francis mellersh
```

**原始表格**:
```
no. | date/time | aircraft | foe | result | location | notes
1 | 4 december 1916 @ 1100 hours | nieuport serial number 3958 | albatros d.i | driven down out of control | northeast of bapaume, france | victory shared with another pilot
2 | 24 april 1917 @ 0840 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | sailly, france | 
3 | 2 may 1917 @ 0945 hours | sopwith triplane s/n n5460 | german two-seater aircraft | driven down out of control | douai, france | 
4 | 11 may 1917 @ 1950 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | douai, france | 
5 | 11 may 1917 @ 1950 hours | sopwith triplane s/n n5460 | albatros d.iii | set afire in midair; destroyed | douai, france | 
6 | 23 may 1917 @ 1800 hours | sopwith triplane s/n n5460 | albatros d.iii | driven down out of control | douai, france | 
7 | 24 july 1917 @ 0635 hours | sopwith triplane s/n n5462 | german two-seater aircraft | driven down out of control | leffinghe | 
8 | 28 july 1917 @ 1735 hours | sopwith triplane s/n n5462 | german two-seater aircraft | driven down out of control | middelkerke, belgium | victory shared with francis mellersh
```

---

### 多答案处理错误

#### 案例 1: `nu-1792`

**问题**: which player had the longest streak of seasons as top scorer?

**正确答案**: `Bent Christensen`

**当前项目预测**: `bent christensen|morten rasmussen`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([season, league\ntop scorer])

  参数: [("['league\\\\ntop scorer', 'season']", np.float64(1.0))]

步骤 2: group_column
  思考: To determine which player had the longest streak of seasons as top scorer, we should group the entries by the player name in the **league top scorer** column.

步骤 3: sort_column

步骤 4: simple_query
  思考: To find the player with the longest streak of seasons as league top scorer, we look for the same name appearing in consecutive seasons in the **league top scorer** column.

From the table:
- **Claus Nielsen** was top scorer for **3 consecutive seasons**: 1984–85, 1985–86, 1986–87.
- **Bent Christensen** was top scorer for **4 consecutive seasons**: 1987–88, 1988–89, 1989–90, 1990–91.
- **Kim Vilfort** had **2 consecutive seasons**.
- **Mark Strudal** had **2 consecutive seasons**.
- **Peter Møller** had **2 consecutive seasons**.
- **Morten Rasmussen** appears in **4 consecutive seasons**: 2006–07, 2007–08, 2008–09, 2009–10, but in 2007–08 and 2008–09 he was a **shared** top scorer.

So, if shared top-scorer seasons are counted, the longest streak is a tie between **Bent Christensen** and **Morten Rasmussen**, each with 4 seasons.
  参数: [('bent christensen|morten rasmussen', np.float64(1.0))]

```

**完整表格**:
```
season | league\npos. | league\ncompetition | league\ntop scorer | danish cup | europe | others
1981-82 | 4 | 1982 1st division | michael laudrup (15) | 4th round |  | 
1982-83 | 4 | 1983 1st division | brian chrøis (12) | 4th round |  | 
1983-84 | 4 | 1984 1st division | jens kolding (11) | 3rd round |  | 
1984-85 | 1 | 1985 1st division | claus nielsen (17) | 3rd round |  | 
1985-86 | 2 | 1986 1st division | claus nielsen (16) | quarter-final |  | 
1986-87 | 1 | 1987 1st division | claus nielsen (20) | 4th round | ec1 quarter-final | 
1987-88 | 1 | 1988 1st division | bent christensen (21) | finalist | ec3 2nd round | 
1988-89 | 2 | 1989 1st division | bent christensen (10) | winner | ec1 1st round | 
1989-90 | 1 | 1990 1st division | bent christensen (17) | quarter-final | ec1 1st round | 
1990-91 | 1 | 1991 superliga | bent christensen (11) | semi-final | ec3 semi-final | 
1991-92 | 7 | 1991-92 superliga | kim vilfort (9) | 4th round | ec1 2nd round | 
1992-93 | 3 | 1992-93 superliga | kim vilfort (10) | 5th round |  | 
1993-94 | 3 | 1993-94 superliga | mark strudal (13) | winner | ec3 3rd round | 
1994-95 | 2 | 1994-95 superliga | mark strudal (12) | quarter-final | ec2 2nd round | danish supercup winner
1995-96 | 1 | 1995-96 superliga | peter møller (15) | finalist | ec3 3rd round | 
1996-97 | 1 | 1996-97 superliga | peter møller (22) | semi-final | ec1 qualification round\nec3 quarter-final | danish supercup winner
1997-98 | 1 | 1997-98 superliga | ebbe sand (28) | winner | ec1 qual 2nd round\nec3 1st round | danish supercup winner
1998-99 | 2 | 1998-99 superliga | ebbe sand (19) | semi-final | ec1 group stage | 
1999-00 | 2 | 1999-00 superliga | bent christensen (13) | semi-final | ec1 qual 3rd round\nec3 1st round | 
2000-01 | 2 | 2000-01 superliga | peter graulund (21) | quarter-final | ec1 qual 3rd round\nec3 1st round | 
2001-02 | 1 | 2001-02 superliga | peter madsen (22) | 5th round | ec3 3rd round | 
2002-03 | 2 | 2002-03 superliga | mattias jonson (11) | winner | ec1 qual 3rd round\nec3 1st round | danish supercup winner
2003-04 | 2 | 2003-04 superliga | thomas kahlenberg (11) | semi-final | ec3 3rd round | 
2004-05 | 1 | 2004-05 superliga | thomas kahlenberg (13) | winner | ec3 qual 2nd round | royal league group stage
2005-06 | 2 | 2005-06 superliga | johan elmander (13) | semi-final | ec1 qual 3rd round\nec3 group stage | royal league group stage\ndanish league cup winner
2006-07 | 6 | 2006-07 superliga | morten rasmussen (15) | 4th round | ec3 1st round | royal league winner\ndanish league cup winner
2007-08 | 8 | 2007-08 superliga | morten rasmussen (7)\nmartin ericsson (7) | winner |  | 
2008-09 | 3 | 2008-09 superliga | morten rasmussen (9)\nalexander farnerud (9)\nousman jallow (9) | semi-final | ec3 1st round | 
2009-10 | 3 | 2009-10 superliga | morten rasmussen (12) | 4th round | ec3 qual play-off round | 
2010-11 | 3 | 2010-11 superliga | michael krohn-dehli (11) |  |  | 
2011-12 | 9 | 2011-12 superliga | simon makienok christoffersen (10) |  |  | 
```

**原始表格**:
```
season | league\npos. | league\ncompetition | league\ntop scorer | danish cup | europe | others
1981-82 | 4 | 1982 1st division | michael laudrup (15) | 4th round |  | 
1982-83 | 4 | 1983 1st division | brian chrøis (12) | 4th round |  | 
1983-84 | 4 | 1984 1st division | jens kolding (11) | 3rd round |  | 
1984-85 | 1 | 1985 1st division | claus nielsen (17) | 3rd round |  | 
1985-86 | 2 | 1986 1st division | claus nielsen (16) | quarter-final |  | 
1986-87 | 1 | 1987 1st division | claus nielsen (20) | 4th round | ec1 quarter-final | 
1987-88 | 1 | 1988 1st division | bent christensen (21) | finalist | ec3 2nd round | 
1988-89 | 2 | 1989 1st division | bent christensen (10) | winner | ec1 1st round | 
1989-90 | 1 | 1990 1st division | bent christensen (17) | quarter-final | ec1 1st round | 
1990-91 | 1 | 1991 superliga | bent christensen (11) | semi-final | ec3 semi-final | 
1991-92 | 7 | 1991-92 superliga | kim vilfort (9) | 4th round | ec1 2nd round | 
1992-93 | 3 | 1992-93 superliga | kim vilfort (10) | 5th round |  | 
1993-94 | 3 | 1993-94 superliga | mark strudal (13) | winner | ec3 3rd round | 
1994-95 | 2 | 1994-95 superliga | mark strudal (12) | quarter-final | ec2 2nd round | danish supercup winner
1995-96 | 1 | 1995-96 superliga | peter møller (15) | finalist | ec3 3rd round | 
1996-97 | 1 | 1996-97 superliga | peter møller (22) | semi-final | ec1 qualification round\nec3 quarter-final | danish supercup winner
1997-98 | 1 | 1997-98 superliga | ebbe sand (28) | winner | ec1 qual 2nd round\nec3 1st round | danish supercup winner
1998-99 | 2 | 1998-99 superliga | ebbe sand (19) | semi-final | ec1 group stage | 
1999-00 | 2 | 1999-00 superliga | bent christensen (13) | semi-final | ec1 qual 3rd round\nec3 1st round | 
2000-01 | 2 | 2000-01 superliga | peter graulund (21) | quarter-final | ec1 qual 3rd round\nec3 1st round | 
2001-02 | 1 | 2001-02 superliga | peter madsen (22) | 5th round | ec3 3rd round | 
2002-03 | 2 | 2002-03 superliga | mattias jonson (11) | winner | ec1 qual 3rd round\nec3 1st round | danish supercup winner
2003-04 | 2 | 2003-04 superliga | thomas kahlenberg (11) | semi-final | ec3 3rd round | 
2004-05 | 1 | 2004-05 superliga | thomas kahlenberg (13) | winner | ec3 qual 2nd round | royal league group stage
2005-06 | 2 | 2005-06 superliga | johan elmander (13) | semi-final | ec1 qual 3rd round\nec3 group stage | royal league group stage\ndanish league cup winner
2006-07 | 6 | 2006-07 superliga | morten rasmussen (15) | 4th round | ec3 1st round | royal league winner\ndanish league cup winner
2007-08 | 8 | 2007-08 superliga | morten rasmussen (7)\nmartin ericsson (7) | winner |  | 
2008-09 | 3 | 2008-09 superliga | morten rasmussen (9)\nalexander farnerud (9)\nousman jallow (9) | semi-final | ec3 1st round | 
2009-10 | 3 | 2009-10 superliga | morten rasmussen (12) | 4th round | ec3 qual play-off round | 
2010-11 | 3 | 2010-11 superliga | michael krohn-dehli (11) |  |  | 
2011-12 | 9 | 2011-12 superliga | simon makienok christoffersen (10) |  |  | 
```

---

#### 案例 2: `nu-2168`

**问题**: who was leading rusher for the philadelphia eagles the only time they were nfc champions?

**正确答案**: `Wilbert Montgomery`

**当前项目预测**: `wilbert montgomery|brian westbrook`

**完整思维链**:
```
步骤 1: select_row
  思考: Select relevant rows.
Explanation: The question asks for the leading rusher for the Philadelphia Eagles when they were NFC champions. To determine this, we need the rows where the team is Philadelphia Eagles, then identify the relevant championship occurrence from the table. The relevant rows are row 11 and row 35.
  参数: [("['11', '35']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([season, team, leading rusher])

  参数: [("['leading rusher', 'season', 'team']", np.float64(1.0))]

步骤 3: simple_query
  思考: The table shows that the **Philadelphia Eagles** appear twice as NFC champions: **1980** and **2004**. Their **leading rushers** in those seasons were **Wilbert Montgomery** and **Brian Westbrook**, respectively. Since the question says “the only time,” but the table shows they were champions twice, there is not just one valid row. Therefore, both leading rushers should be returned.
  参数: [('wilbert montgomery|brian westbrook', np.float64(1.0))]

```

**完整表格**:
```
season | team | record | head coach | quarterback | leading rusher | leading receiver | all-pros | runner up
1970 | dallas cowboys | 10–4 | tom landry* | craig morton | duane thomas | bob hayes* | howley | san francisco 49ers
1971 | dallas cowboys† | 11–3 | tom landry* | roger staubach* | duane thomas | bob hayes* | lilly*, niland, wright* | san francisco 49ers
1972 | washington redskins | 11–3 | george allen* | billy kilmer | larry brown | charley taylor* | brown, hanburger* | dallas cowboys
1973 | minnesota vikings | 12–2 | bud grant* | fran tarkenton* | chuck foreman | john gilliam | eller*, page*, yary* | dallas cowboys
1974 | minnesota vikings | 10–4 | bud grant* | fran tarkenton* | chuck foreman | jim lash | page*, yary* | los angeles rams
1975 | dallas cowboys | 10–4 | tom landry* | roger staubach* | robert newhouse | drew pearson | none | los angeles rams
1976 | minnesota vikings | 11–2–1 | bud grant* | fran tarkenton* | chuck foreman | sammy white | yary* | los angeles rams
1977 | dallas cowboys† | 12–2 | tom landry* | roger staubach* | tony dorsett* | drew pearson | harris, herrera, martin, pearson | minnesota vikings
1978 | dallas cowboys | 12–4 | tom landry* | roger staubach* | tony dorsett* | tony hill | harris, white* | los angeles rams
1979 | los angeles rams | 9–7 | ray malavasi | pat haden | wendell tyler | preston dennard | brooks, youngblood* | tampa bay buccaneers
1980 | philadelphia eagles | 12–4 | dick vermeil | ron jaworski | wilbert montgomery | charlie smith | johnson | dallas cowboys
1981 | san francisco 49ers† | 13–3 | bill walsh* | joe montana* | ricky patton | dwight clark | dean*, lott* | dallas cowboys
1982 | washington redskins† | 8–1 | joe gibbs* | joe theismann | john riggins* | charlie brown | moseley | dallas cowboys
1983 | washington redskins | 14–2 | joe gibbs* | joe theismann | john riggins* | charlie brown | butz, grimm*, jacoby, murphy, nelms, riggins*, theismann | san francisco 49ers
1984 | san francisco 49ers† | 15–1 | bill walsh* | joe montana* | wendell tyler | dwight clark | fahnhorst | chicago bears
1985 | chicago bears† | 15–1 | mike ditka* | jim mcmahon | walter payton* | willie gault | covert, dent*, mcmichael, payton*, singletary* | los angeles rams
1986 | new york giants† | 14–2 | bill parcells* | phil simms | joe morris | mark bavaro | bavaro, landeta, morris, taylor* | washington redskins
1987 | washington redskins† | 11–4 | joe gibbs* | jay schroeder | george rogers | gary clark | clark, wilburn | minnesota vikings
1988 | san francisco 49ers† | 10–6 | bill walsh* | joe montana* | roger craig | jerry rice* | craig, rice* | chicago bears
1989 | san francisco 49ers† | 14–2 | george seifert | joe montana* | roger craig | jerry rice* | cofer, lott*, montana*, rice*, | los angeles rams
1990 | new york giants† | 13–3 | bill parcells* | phil simms | ottis anderson | stephen baker | johnson, landeta | san francisco 49ers
1991 | washington redskins† | 14–2 | joe gibbs* | mark rypien | earnest byner | gary clark | green*, lachey | detroit lions
1992 | dallas cowboys† | 13–3 | jimmy johnson | troy aikman* | emmitt smith* | michael irvin* | novacek, smith* | san francisco 49ers
1993 | dallas cowboys† | 12–4 | jimmy johnson | troy aikman* | emmitt smith* | michael irvin* | smith*, williams | san francisco 49ers
1994 | san francisco 49ers† | 13–3 | george seifert | steve young* | ricky watters | jerry rice* | rice*, sanders*, young* | dallas cowboys
1995 | dallas cowboys† | 12–4 | barry switzer | troy aikman* | emmitt smith* | michael irvin* | newton, smith*, woodson | green bay packers
1996 | green bay packers† | 13–3 | mike holmgren | brett favre | edgar bennett | antonio freeman | butler, favre | carolina panthers
1997 | green bay packers | 13–3 | mike holmgren | brett favre | dorsey levens | antonio freeman | butler, favre | san francisco 49ers
1998 | atlanta falcons | 14–2 | dan reeves | chris chandler | jamal anderson | tony martin | anderson | minnesota vikings
1999 | st. louis rams† | 13–3 | dick vermeil | kurt warner | marshall faulk* | isaac bruce | carter, faulk*, pace, warner | tampa bay buccaneers
2000 | new york giants | 12–4 | jim fassel | kerry collins | tiki barber | amani toomer | none | minnesota vikings
2001 | st. louis rams | 14–2 | mike martz | kurt warner | marshall faulk* | torry holt | faulk*, pace, warner, williams* | philadelphia eagles
2002 | tampa bay buccaneers† | 12–4 | jon gruden | brad johnson | michael pittman | keyshawn johnson | brooks*, rice, sapp* | philadelphia eagles
2003 | carolina panthers | 11–5 | john fox | jake delhomme | stephen davis | steve smith | jenkins | philadelphia eagles
2004 | philadelphia eagles | 13–3 | andy reid | donovan mcnabb | brian westbrook | terrell owens | dawkins, owens, sheppard | atlanta falcons
2005 | seattle seahawks | 13–3 | mike holmgren | matt hasselbeck | shaun alexander | bobby engram | alexander, hutchinson, jones*, strong | carolina panthers
2006 | chicago bears | 13–3 | lovie smith | rex grossman | thomas jones | muhsin muhammad | gould, hester, kreutz, urlacher | new orleans saints
2007 | new york giants† | 10–6 | tom coughlin | eli manning | brandon jacobs | plaxico burress | none | green bay packers
2008 | arizona cardinals | 9–7 | ken whisenhunt | kurt warner | edgerrin james | larry fitzgerald | fitzgerald | philadelphia eagles
2009 | new orleans saints† | 13–3 | sean payton | drew brees | pierre thomas | marques colston | evans | minnesota vikings
2010 | green bay packers† | 10–6 | mike mccarthy | aaron rodgers | brandon jackson | greg jennings | clifton, collins, jennings, matthews, woodson | chicago bears
2011 | new york giants† | 9–7 | tom coughlin | eli manning | ahmad bradshaw | victor cruz | pierre-paul | san francisco 49ers
2012 | san francisco 49ers | 11–4–1 | jim harbaugh | colin kaepernick | frank gore | michael crabtree | bowman, goldson, iupati, lee, smith, willis | atlanta falcons
2013 | seattle seahawks† | 13–3 | pete carroll | russell wilson | marshawn lynch | golden tate | sherman, thomas | san francisco 49ers
```

**原始表格**:
```
season | team | record | head coach | quarterback | leading rusher | leading receiver | all-pros | runner up
1970 | dallas cowboys | 10–4 | tom landry* | craig morton | duane thomas | bob hayes* | howley | san francisco 49ers
1971 | dallas cowboys† | 11–3 | tom landry* | roger staubach* | duane thomas | bob hayes* | lilly*, niland, wright* | san francisco 49ers
1972 | washington redskins | 11–3 | george allen* | billy kilmer | larry brown | charley taylor* | brown, hanburger* | dallas cowboys
1973 | minnesota vikings | 12–2 | bud grant* | fran tarkenton* | chuck foreman | john gilliam | eller*, page*, yary* | dallas cowboys
1974 | minnesota vikings | 10–4 | bud grant* | fran tarkenton* | chuck foreman | jim lash | page*, yary* | los angeles rams
1975 | dallas cowboys | 10–4 | tom landry* | roger staubach* | robert newhouse | drew pearson | none | los angeles rams
1976 | minnesota vikings | 11–2–1 | bud grant* | fran tarkenton* | chuck foreman | sammy white | yary* | los angeles rams
1977 | dallas cowboys† | 12–2 | tom landry* | roger staubach* | tony dorsett* | drew pearson | harris, herrera, martin, pearson | minnesota vikings
1978 | dallas cowboys | 12–4 | tom landry* | roger staubach* | tony dorsett* | tony hill | harris, white* | los angeles rams
1979 | los angeles rams | 9–7 | ray malavasi | pat haden | wendell tyler | preston dennard | brooks, youngblood* | tampa bay buccaneers
1980 | philadelphia eagles | 12–4 | dick vermeil | ron jaworski | wilbert montgomery | charlie smith | johnson | dallas cowboys
1981 | san francisco 49ers† | 13–3 | bill walsh* | joe montana* | ricky patton | dwight clark | dean*, lott* | dallas cowboys
1982 | washington redskins† | 8–1 | joe gibbs* | joe theismann | john riggins* | charlie brown | moseley | dallas cowboys
1983 | washington redskins | 14–2 | joe gibbs* | joe theismann | john riggins* | charlie brown | butz, grimm*, jacoby, murphy, nelms, riggins*, theismann | san francisco 49ers
1984 | san francisco 49ers† | 15–1 | bill walsh* | joe montana* | wendell tyler | dwight clark | fahnhorst | chicago bears
1985 | chicago bears† | 15–1 | mike ditka* | jim mcmahon | walter payton* | willie gault | covert, dent*, mcmichael, payton*, singletary* | los angeles rams
1986 | new york giants† | 14–2 | bill parcells* | phil simms | joe morris | mark bavaro | bavaro, landeta, morris, taylor* | washington redskins
1987 | washington redskins† | 11–4 | joe gibbs* | jay schroeder | george rogers | gary clark | clark, wilburn | minnesota vikings
1988 | san francisco 49ers† | 10–6 | bill walsh* | joe montana* | roger craig | jerry rice* | craig, rice* | chicago bears
1989 | san francisco 49ers† | 14–2 | george seifert | joe montana* | roger craig | jerry rice* | cofer, lott*, montana*, rice*, | los angeles rams
1990 | new york giants† | 13–3 | bill parcells* | phil simms | ottis anderson | stephen baker | johnson, landeta | san francisco 49ers
1991 | washington redskins† | 14–2 | joe gibbs* | mark rypien | earnest byner | gary clark | green*, lachey | detroit lions
1992 | dallas cowboys† | 13–3 | jimmy johnson | troy aikman* | emmitt smith* | michael irvin* | novacek, smith* | san francisco 49ers
1993 | dallas cowboys† | 12–4 | jimmy johnson | troy aikman* | emmitt smith* | michael irvin* | smith*, williams | san francisco 49ers
1994 | san francisco 49ers† | 13–3 | george seifert | steve young* | ricky watters | jerry rice* | rice*, sanders*, young* | dallas cowboys
1995 | dallas cowboys† | 12–4 | barry switzer | troy aikman* | emmitt smith* | michael irvin* | newton, smith*, woodson | green bay packers
1996 | green bay packers† | 13–3 | mike holmgren | brett favre | edgar bennett | antonio freeman | butler, favre | carolina panthers
1997 | green bay packers | 13–3 | mike holmgren | brett favre | dorsey levens | antonio freeman | butler, favre | san francisco 49ers
1998 | atlanta falcons | 14–2 | dan reeves | chris chandler | jamal anderson | tony martin | anderson | minnesota vikings
1999 | st. louis rams† | 13–3 | dick vermeil | kurt warner | marshall faulk* | isaac bruce | carter, faulk*, pace, warner | tampa bay buccaneers
2000 | new york giants | 12–4 | jim fassel | kerry collins | tiki barber | amani toomer | none | minnesota vikings
2001 | st. louis rams | 14–2 | mike martz | kurt warner | marshall faulk* | torry holt | faulk*, pace, warner, williams* | philadelphia eagles
2002 | tampa bay buccaneers† | 12–4 | jon gruden | brad johnson | michael pittman | keyshawn johnson | brooks*, rice, sapp* | philadelphia eagles
2003 | carolina panthers | 11–5 | john fox | jake delhomme | stephen davis | steve smith | jenkins | philadelphia eagles
2004 | philadelphia eagles | 13–3 | andy reid | donovan mcnabb | brian westbrook | terrell owens | dawkins, owens, sheppard | atlanta falcons
2005 | seattle seahawks | 13–3 | mike holmgren | matt hasselbeck | shaun alexander | bobby engram | alexander, hutchinson, jones*, strong | carolina panthers
2006 | chicago bears | 13–3 | lovie smith | rex grossman | thomas jones | muhsin muhammad | gould, hester, kreutz, urlacher | new orleans saints
2007 | new york giants† | 10–6 | tom coughlin | eli manning | brandon jacobs | plaxico burress | none | green bay packers
2008 | arizona cardinals | 9–7 | ken whisenhunt | kurt warner | edgerrin james | larry fitzgerald | fitzgerald | philadelphia eagles
2009 | new orleans saints† | 13–3 | sean payton | drew brees | pierre thomas | marques colston | evans | minnesota vikings
2010 | green bay packers† | 10–6 | mike mccarthy | aaron rodgers | brandon jackson | greg jennings | clifton, collins, jennings, matthews, woodson | chicago bears
2011 | new york giants† | 9–7 | tom coughlin | eli manning | ahmad bradshaw | victor cruz | pierre-paul | san francisco 49ers
2012 | san francisco 49ers | 11–4–1 | jim harbaugh | colin kaepernick | frank gore | michael crabtree | bowman, goldson, iupati, lee, smith, willis | atlanta falcons
2013 | seattle seahawks† | 13–3 | pete carroll | russell wilson | marshawn lynch | golden tate | sherman, thomas | san francisco 49ers
```

---

### 实体识别错误

#### 案例 1: `nu-58`

**问题**: who was the top placing competitor?

**正确答案**: `Esther Shahamorov`

**当前项目预测**: `ze'ev friedman`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([name, placing])

  参数: [("['name', 'placing']", np.float64(1.0))]

步骤 2: sort_column

步骤 3: group_column
  思考: To find the top placing competitor, we need to identify the best result in the **placing** column, which means selecting the minimum/best placing value rather than grouping.

步骤 4: simple_query
  思考: To find the top placing competitor, compare only the clear overall numeric placings in the `placing` column, and do not treat stage results like `semifinal (5th)`, `second round`, `heats (8th)`, or `group stage` as directly comparable final rankings. The explicit numeric placings are: Shaul Ladani `19`, Yair Michaeli `23`, Itzhak Nir `23`, Henry Hershkowitz `23`, Henry Hershkowitz `46`, Zelig Stroch `57`, and Ze'ev Friedman `12`. The best placing is the smallest number, which is `12`, achieved by Ze'ev Friedman.
  参数: [("ze'ev friedman", np.float64(1.0))]

```

**完整表格**:
```
name | sport | event | placing | performance
shaul ladani | athletics | men's 50 km walk | 19 | 4:24:38.6\n(also entered for 20 km walk, but did not start)
esther shahamorov | athletics | women's 100 m | semifinal (5th) | 11.49
esther shahamorov | athletics | women's 100 m hurdles | semifinal | did not start (left munich before the semifinal)
dan alon | fencing | men's foil | second round | w5–l5 (1r 3-2, 2r 2-3)
yehuda weissenstein | fencing | men's foil | second round | w2–l8 (1r 2-3, 2r 0-5)
yair michaeli | sailing | flying dutchman | 23 | 28-22-22-19-25-19-dns = 171 pts\n(left kiel before 7th race)
itzhak nir | sailing | flying dutchman | 23 | 28-22-22-19-25-19-dns = 171 pts\n(left kiel before 7th race)
henry hershkowitz | shooting | 50 metre rifle prone | 23 | 593/600
henry hershkowitz | shooting | 50 metre rifle three positions | 46 | 1114/1200
zelig stroch | shooting | 50 metre rifle prone | 57 | 589/600
shlomit nir | swimming | women's 100 m breaststroke | heats (8th) | 1:20.90
shlomit nir | swimming | women's 200 m breaststroke | heats (6th) | 2:53.60
david berger | weightlifting | light-heavyweight <82.5 kg | — | j:132.5 c:122.5 s:— t:—
ze'ev friedman | weightlifting | bantamweight <56 kg | 12 | j:102.5 c:102.5 s:125 t:330
yossef romano | weightlifting | middleweight <75 kg | — | (retired injured on third attempt to press 137.5kg)
gad tsobari | wrestling | freestyle — light flyweight <48 kg | group stage | 0w–2l
eliezer halfin | wrestling | freestyle — lightweight <68 kg | group stage | 1w–2l
mark slavin | wrestling | greco-roman — middleweight <82 kg | — | (taken hostage before his scheduled event)
```

**原始表格**:
```
name | sport | event | placing | performance
shaul ladani | athletics | men's 50 km walk | 19 | 4:24:38.6\n(also entered for 20 km walk, but did not start)
esther shahamorov | athletics | women's 100 m | semifinal (5th) | 11.49
esther shahamorov | athletics | women's 100 m hurdles | semifinal | did not start (left munich before the semifinal)
dan alon | fencing | men's foil | second round | w5–l5 (1r 3-2, 2r 2-3)
yehuda weissenstein | fencing | men's foil | second round | w2–l8 (1r 2-3, 2r 0-5)
yair michaeli | sailing | flying dutchman | 23 | 28-22-22-19-25-19-dns = 171 pts\n(left kiel before 7th race)
itzhak nir | sailing | flying dutchman | 23 | 28-22-22-19-25-19-dns = 171 pts\n(left kiel before 7th race)
henry hershkowitz | shooting | 50 metre rifle prone | 23 | 593/600
henry hershkowitz | shooting | 50 metre rifle three positions | 46 | 1114/1200
zelig stroch | shooting | 50 metre rifle prone | 57 | 589/600
shlomit nir | swimming | women's 100 m breaststroke | heats (8th) | 1:20.90
shlomit nir | swimming | women's 200 m breaststroke | heats (6th) | 2:53.60
david berger | weightlifting | light-heavyweight <82.5 kg | — | j:132.5 c:122.5 s:— t:—
ze'ev friedman | weightlifting | bantamweight <56 kg | 12 | j:102.5 c:102.5 s:125 t:330
yossef romano | weightlifting | middleweight <75 kg | — | (retired injured on third attempt to press 137.5kg)
gad tsobari | wrestling | freestyle — light flyweight <48 kg | group stage | 0w–2l
eliezer halfin | wrestling | freestyle — lightweight <68 kg | group stage | 1w–2l
mark slavin | wrestling | greco-roman — middleweight <82 kg | — | (taken hostage before his scheduled event)
```

---

#### 案例 2: `nu-3507`

**问题**: who was the first recipient of the guardian of zion award in the 21st century?

**正确答案**: `Sir Martin Gilbert`

**当前项目预测**: `cynthia ozick`

**完整思维链**:
```
步骤 1: select_row
  思考: Select relevant rows.

  参数: [("['5']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([year, recipient])

  参数: [("['recipient', 'year']", np.float64(1.0))]

步骤 3: simple_query
  思考: Explanation: The 21st century begins in 2001. In the resulting sub-table, the year 2001 corresponds to the recipient Cynthia Ozick. Therefore, the first recipient of the Guardian of Zion Award in the 21st century was Cynthia Ozick.
  参数: [('cynthia ozick', np.float64(1.0))]

```

**完整表格**:
```
year | recipient | nationality | profession | speech
1997 | elie wiesel | united states | professional writer\nwinner of the nobel peace prize (1986) | 
1998 | herman wouk | united states | professional writer and 1952 pulitzer prize winner | 
1999 | a.m. rosenthal | united states | former new york times editor\nformer new york daily news columnist | 
2000 | sir martin gilbert | united kingdom | historian and writer | 
2001 | cynthia ozick | united states | professional writer | 
2002 | charles krauthammer | united states | the washington post columnist | [1]
2003 | ruth roskies wisse | united states | yiddish professor of harvard university | [2]
2004 | arthur cohn | switzerland | filmmaker and writer | 
2005 | william safire | united states | author, journalist and speechwriter\n1978 pulitzer prize winner | 
2006 | daniel pipes | united states | author and historian | 
2007 | norman podhoretz | united states | author, columnist | 
2008 | david be'eri, mordechai eliav, rabbi yehuda maly | israel |  | 
2009 | caroline glick | israel | journalist | 
2010 | malcolm hoenlein | united states | executive vice chairman of the conference of presidents of major american jewish organizations | 
```

**原始表格**:
```
year | recipient | nationality | profession | speech
1997 | elie wiesel | united states | professional writer\nwinner of the nobel peace prize (1986) | 
1998 | herman wouk | united states | professional writer and 1952 pulitzer prize winner | 
1999 | a.m. rosenthal | united states | former new york times editor\nformer new york daily news columnist | 
2000 | sir martin gilbert | united kingdom | historian and writer | 
2001 | cynthia ozick | united states | professional writer | 
2002 | charles krauthammer | united states | the washington post columnist | [1]
2003 | ruth roskies wisse | united states | yiddish professor of harvard university | [2]
2004 | arthur cohn | switzerland | filmmaker and writer | 
2005 | william safire | united states | author, journalist and speechwriter\n1978 pulitzer prize winner | 
2006 | daniel pipes | united states | author and historian | 
2007 | norman podhoretz | united states | author, columnist | 
2008 | david be'eri, mordechai eliav, rabbi yehuda maly | israel |  | 
2009 | caroline glick | israel | journalist | 
2010 | malcolm hoenlein | united states | executive vice chairman of the conference of presidents of major american jewish organizations | 
```

---

#### 案例 3: `nu-4311`

**问题**: what is the total number of points india has scored throughout the rivalry?

**正确答案**: `16`

**当前项目预测**: `**16**`

**完整思维链**:
```
步骤 1: add_column

步骤 2: select_column
  思考: f_select_column([winner, results])

  参数: [("['results', 'winner']", np.float64(1.0))]

步骤 3: simple_query
  思考: To find the total number of points India scored throughout the rivalry, use the **winner** and **results** columns together.

From the table:

- **Pakistan win, 3 - 1** → India scored **1**
- **Pakistan win, 2 - 1** → India scored **1**
- **India win, 3 - 2** → India scored **3**
- **Draw, 2 - 2** → India scored **2**
- **Pakistan win, 4 - 3** → India scored **3**
- **Pakistan win, 5 - 3** → India scored **3**
- **Pakistan win, 4 - 2** → India scored **2**
- **Pakistan win, 3 - 1** → India scored **1**

Ignore the **tba** row since no result is given.

Adding India’s points:  
1 + 1 + 3 + 2 + 3 + 3 + 2 + 1 = **16**
  参数: [('**16**', np.float64(1.0))]

```

**完整表格**:
```
year | matches | winner | results | pakistan\ncaptain | pakistan\ncoach | india\ncaptain | india\ncoach
1978 | 4 | pakistan win | 3 - 1 | islahuddin siddique | sayad a. hussain | v. j. philips | r. s. gentle
1981 | 4 | pakistan win | 2 - 1 | akhtar rasool | zakauddin | surjeet singh | harmeek singh
1986 | 7 | india win | 3 - 2 | hassan sardar | anwar ahmad khan | mohmmad shaheed | m. p. ganesh
1988 | 6 | draw | 2 - 2 | nasir ali | manzoor-ul-hasan | m. m. somaya | m. p. ganesh
1998 | 8 | pakistan win | 4 - 3 | tahir zaman | islahuddin siddique | dhanraj pillay | v bhaskaran
1999 | 9 | pakistan win | 5 - 3 | atif bashir | shahnaz shaikh | anil aldrin | v bhaskaran
2004 | 8 | pakistan win | 4 - 2 | waseem ahmad | roelant oltmans | dileep tirkey | gehard rach
2006 | 6 | pakistan win | 3 - 1 | mohammad saqlain | asif bajwa | ignace tirkey | rajinder singh jr.
2013 | tba | tba | tba | tba | tba | tba | tba
```

**原始表格**:
```
year | matches | winner | results | pakistan\ncaptain | pakistan\ncoach | india\ncaptain | india\ncoach
1978 | 4 | pakistan win | 3 - 1 | islahuddin siddique | sayad a. hussain | v. j. philips | r. s. gentle
1981 | 4 | pakistan win | 2 - 1 | akhtar rasool | zakauddin | surjeet singh | harmeek singh
1986 | 7 | india win | 3 - 2 | hassan sardar | anwar ahmad khan | mohmmad shaheed | m. p. ganesh
1988 | 6 | draw | 2 - 2 | nasir ali | manzoor-ul-hasan | m. m. somaya | m. p. ganesh
1998 | 8 | pakistan win | 4 - 3 | tahir zaman | islahuddin siddique | dhanraj pillay | v bhaskaran
1999 | 9 | pakistan win | 5 - 3 | atif bashir | shahnaz shaikh | anil aldrin | v bhaskaran
2004 | 8 | pakistan win | 4 - 2 | waseem ahmad | roelant oltmans | dileep tirkey | gehard rach
2006 | 6 | pakistan win | 3 - 1 | mohammad saqlain | asif bajwa | ignace tirkey | rajinder singh jr.
2013 | tba | tba | tba | tba | tba | tba | tba
```

---

### 数值统计错误

#### 案例 1: `nu-82`

**问题**: how many teams did not score any goals in the 2006 season?

**正确答案**: `1`

**当前项目预测**: `0`

**完整思维链**:
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

**完整表格**:
```
season | team | country | division | apps | goals
2004 | cska moscow | russia | 1 | 0 | 0
2005 | cska moscow | russia | 1 | 0 | 0
2006 | spartak nizhny novgorod | russia | 2 | 36 | 1
2006/07 | dnipro dnipropetrovsk | ukraine | 1 | 12 | 0
2007/08 | dnipro dnipropetrovsk | ukraine | 1 | 24 | 0
2008/09 | dnipro dnipropetrovsk | ukraine | 1 | 22 | 1
2009/10 | dnipro dnipropetrovsk | ukraine | 1 | 28 | 0
2010/11 | dnipro dnipropetrovsk | ukraine | 1 | 23 | 0
2011/12 | dnipro dnipropetrovsk | ukraine | 1 | 16 | 0
2012/13 | dnipro dnipropetrovsk | ukraine | 1 | 10 | 1
2012/13 | lokomotiv moscow | russia | 1 | 8 | 0
2013/14 | lokomotiv moscow | russia | 1 | 14 | 1
```

**原始表格**:
```
season | team | country | division | apps | goals
2004 | cska moscow | russia | 1 | 0 | 0
2005 | cska moscow | russia | 1 | 0 | 0
2006 | spartak nizhny novgorod | russia | 2 | 36 | 1
2006/07 | dnipro dnipropetrovsk | ukraine | 1 | 12 | 0
2007/08 | dnipro dnipropetrovsk | ukraine | 1 | 24 | 0
2008/09 | dnipro dnipropetrovsk | ukraine | 1 | 22 | 1
2009/10 | dnipro dnipropetrovsk | ukraine | 1 | 28 | 0
2010/11 | dnipro dnipropetrovsk | ukraine | 1 | 23 | 0
2011/12 | dnipro dnipropetrovsk | ukraine | 1 | 16 | 0
2012/13 | dnipro dnipropetrovsk | ukraine | 1 | 10 | 1
2012/13 | lokomotiv moscow | russia | 1 | 8 | 0
2013/14 | lokomotiv moscow | russia | 1 | 14 | 1
```

---

#### 案例 2: `nu-122`

**问题**: how many designers do not have an associated publication?

**正确答案**: `6`

**当前项目预测**: `10`

**完整思维链**:
```
步骤 1: select_column
  思考: f_select_column([designer(s), associated publication])

  参数: [("['associated publication', 'designer(s)']", np.float64(1.0))]

步骤 2: group_column
  思考: The question asks for entries where the associated publication is missing, so we should group by the "associated publication" column to identify the blank/non-blank groups.
  参数: [('(\'associated publication\', [(\'\', 6), (\'the sunday times\', 4), (\'the times\', 4), (\'vogue\', 4), (\'the daily telegraph\', 3), (\'brides\', 2), (\'elle\', 2), ("harper\'s & queen", 2), (\'the guardian\', 2), (\'the independent\', 2), (\'the observer\', 2), (\'uk vogue\', 2), (\'browns\', 1), (\'country life\', 1), (\'fashion magazine\', 1), (\'financial times\', 1), (\'gq; the guardian\', 1), (\'grazia\', 1), ("harper\'s bazaar", 1), ("harper\'s bazaar and queen magazine", 1), (\'marie claire\', 1), (\'the clothes show (bbc)\', 1), (\'the daily express\', 1), (\'the daily mail\', 1), (\'the daily mirror\', 1), (\'the sunday telegraph\', 1), (\'vanity fair\', 1)])', np.float64(1.0))]

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

**完整表格**:
```
year | designer(s) | brief description | selected by: | associated publication
1963 | mary quant\nreed crawford (hat)\nanello & davide (boots) | grey wool 'rex harrison' pinafore dress & cream blouse | members of the fashion writers' association | 
1964 | jean muir for jane & jane\ncharles jourdan for dior (shoes) | dress in printed liberty silk | members of the fashion writers' association | 
1965 | john bates for jean varon\nanello & davide (shoes) | printed linen dress with mesh midriff | members of the fashion writers' association | 
1966 | michèle rosier of v de v (coat)\nyoung jaeger (dress)\nsimone mirman (hat)\nelliott (boots)\njohn bates for echo (tights) | clear plastic raincoat and boots worn with black & white rayon linen dress, white tights and white hat with red plastic visor | ernestine carter | the sunday times
1967 | david bond for slimma\nedward mann (hat)\nsaxone (shoes) | woman's trouser suit, hat & blouse in striped cotton | felicity green | the daily mirror
1968 | jean muir\nbally (shoes) | black-spotted white cotton voile dress | ailsa garland | fashion magazine
1969 | ossie clark for quorum\nrayne (shoes) | woman's silk chiffon and satin trouser suit in celia birtwell print | prudence glynn | the times
1970 | bill gibb for baccarat\nkaffe fassett (knitwear)\nchelsea cobbler (boots) | plaid wool skirt and blue and white blouse, knitted waistcoat, blue suede boots | beatrix miller | uk vogue
1971 | female: graziella fontana for judith hornby\nravel (sandals)\nmale: rupert lycett green for blades | female: hot pants suit in checked liberty cotton\nmale: black velvet evening suit & boots | serena sinclair and patrick lichfield | the daily telegraph
1972 | teenage girl:biba\nyoung girl: bobby hillson\nyoung boy: orange hand for montague burton | teenage girl: dress, hat & boots, all in red & white spotted cotton\nyoung girl: checked cotton dress & pinafore\nyoung boy: trousers, jumper and tank top | moira keenan | the sunday times
1973 | female: marc bohan for christian dior london\nmale: yves saint laurent rive gauche | female: white wool coat & hat\nmale: wool jacket, trousers & sweater | alison adburgham | the guardian
1974 | ottavio and rosita missoni\npasquali (shoes) | male & female ensembles in knitted wool & rayon | jennifer hocking | harper's bazaar and queen magazine
1975 | female: gina fratini\nmale: tommy nutter\nchelsea cobbler (shoes) | female: wedding dress, veil & posy basket, cream silk organza with mimosa print\nmale: bridegroom's frock coat suit, eau de nil wool | anna harvey | brides
1976 | female: kenzo takada of jungle jap\nmale: fiorucci | female: two printed cotton ensembles with wooden jewellery\nmale: hand-knitted sweater, two shirts and jeans | helena matheopoulos | the daily express
1977 | kenzo takada of jungle jap | shirt-dress in khaki cotton, straw hat & plimsolls | ann boyd | the observer
1978 | female: gordon luke clarke\nmale: cerruti | female: printed cotton & polyester jersey tunic, skirt and trousers worn with black leather skirt and coat\nmale: coat, jacket, waistcoat & trousers, knitted wool and wool tweed | barbara griggs | the daily mail
1979 | jean muir\nmanolo blahnik for zapata (shoes) | black rayon jersey dress & beret with black leather jacket | geraldine ranson | the sunday telegraph
1980 | calvin klein\ndiego della valle (sandals) | red & brown striped silk dress with leather belt & wooden jewellery | michael roberts | the sunday times
1981 | karl lagerfeld for chloé\nwalter steiger (shoes)\nugo correani (necklace) | printed white silk dress | vanessa de lisle | harper's & queen
1982 | margaret howell\nnigel preston of maxfield parrish (leather wear)\nmulberry (belt)\nmanolo blahnik for zapata (shoes) | two women's ensembles, a linen skirt, shirt and waistcoat and a blue suede and fawn chamois leather skirt & jacket with cotton shirt | grace coddington | uk vogue
1983 | sheridan barnett\nmanolo blahnik (shoes) | linen dress and coat | sally brampton | the observer
1984 | female: bodymap\nfemale: betty jackson\nbrian bolger: (scarf)\nmale: katharine hamnett | female: ensemble comprising skirt, jumper, stockings, hat, waxed jacket & earrings (bodymap)\nfemale: dress, cardigan & hat and scarf (jackson & bolger)\nmale: t-shirt, shirt and cotton trousers | brenda polan | the guardian
1985 | female: bruce oldfield\ncharles jourdan (shoes)\nmaria buck (jewellery)\nmale: scott crolla | female: black silk & gold lamé evening dress\nmale: shirt, crushed velvet trousers and ikat mules | suzy menkes | the times
1986 | giorgio armani | female: checked wool jacket, skirt, and black suede shoes\nmale: jacket, trousers, shirt and brogues | colin mcdowell | country life
1987 | john galliano\npatrick cox (shoes) | checked cotton coat, skirt, shirt & hat | debbi mason | elle
1988 | jean-paul gaultier for junior gaultier | black denim dress, mesh t-shirt, hat, tights & shoes | jeff banks | the clothes show (bbc)
1989 | rifat ozbek | woman's embroidered velvet evening ensemble | kathryn samuel | the daily telegraph
1990 | romeo gigli | woman's dark blue velvet trouser suit with organza blouse | joan burstein | browns
1991 | karl lagerfeld for chanel | pink lurex & wool tweed jacket & shoes, denim skirt & hat, belt & costume jewellery | elizabeth tilberis | vogue
1992 | ralph lauren | woman's black and white pinstripe trouser suit & shirt | liz smith | the times
1993 | donna karan | purple wool & stretch velvet dress, hat & boots | glenda bailey | marie claire
1994 | john galliano | black silk strapless evening dress | meredith etherington smith | harper's & queen
1995 | female: catherine rayner\nemma hope (shoes)\nmale: tom gilbey | female: beaded ivory silk satin wedding dress\nmale: ivory silk frock coat, cream wool trousers and embroidered waistcoat | sandra boler | brides
1996 | female: alexander mcqueen\nmale: paul smith | female: floral brocade top with red 'bumster' trousers\nmale: bright blue two-piece suit and shirt | tamsin blanchard | the independent
1997 | female: hussein chalayan\nfemale: julien macdonald\nfemale: lainey keogh\nfemale: deborah milner\nphilip treacy (bonnet) | female: purple evening dress with sunburst bead embroidery (chalayan)\nfemale: 'mermaid' evening dress, gold knitted rayon & horsehair (macdonald)\nfemale: evening dress and coat, black knit with beading (keogh)\nfemale: evening coat, purple velvet, with fur collar (milner)\nsculptural black bonnet | isabella blow | the sunday times
1998 | female: sonia rykiel\nmale: chris bailey for jigsaw menswear | female: black knitted sweater & combat trousers, with pink marabou stole\nmale: silver-grey suit, white t-shirt and ankle-length puffa jacket | iain r. webb | elle
1999 | alexander mcqueen | cream lace dress with brown leather collar and sandals | susannah frankel | the independent
2000 | donatella versace for versace | bamboo-print silk chiffon evening dress and jeweled mules | lisa armstrong | the times
2001 | tom ford for yves saint laurent rive gauche | 'peasant' ensemble of gauze top and velvet & satin skirt, with boots and velvet scarf | alexandra shulman | vogue
2002 | junya watanabe | dress, pieced together knit & jersey fabrics, with distressed cow-hide shoes | hilary alexander | the daily telegraph
2003 | marni | colorful printed dress | lucinda chambers | vogue
2004 | tom ford for yves saint laurent rive gauche | evening dress in chinese dragon print satin | sarajane hoare | vanity fair
2005 | alber elbaz for lanvin | blue silk faille dress with full skirt | charlie porter | gq; the guardian
2006 | prada | woman's olive green coat with fur patch pockets | sarah mower | 
2007 | giles deacon at giles | orange 'troubadour' dress with accompanying orange scarf | hywel davies | 
2008 | karl lagerfeld for chanel (trouser ensemble)\nkate moss for topshop (dress) | gold star and navy blue trouser ensemble\nlong sleeved black dress with heart-print | paula reed | grazia
2009 | antonio berardi | white and black trompe l'oeil corset dress | lucy yeomans | harper's bazaar
2010 | vivienne westwood | green ribbed shot-silk deconstructed dress | stephen jones | 
2011 | sarah burton for alexander mcqueen | white embroidered ivory tulle and organza ballgown | hamish bowles | vogue
2012 | raf simons for christian dior | embroidered and appliquéd silk cut-off ballgown and black cigarette pants | vanessa friedman | financial times
```

**原始表格**:
```
year | designer(s) | brief description | selected by: | associated publication
1963 | mary quant\nreed crawford (hat)\nanello & davide (boots) | grey wool 'rex harrison' pinafore dress & cream blouse | members of the fashion writers' association | 
1964 | jean muir for jane & jane\ncharles jourdan for dior (shoes) | dress in printed liberty silk | members of the fashion writers' association | 
1965 | john bates for jean varon\nanello & davide (shoes) | printed linen dress with mesh midriff | members of the fashion writers' association | 
1966 | michèle rosier of v de v (coat)\nyoung jaeger (dress)\nsimone mirman (hat)\nelliott (boots)\njohn bates for echo (tights) | clear plastic raincoat and boots worn with black & white rayon linen dress, white tights and white hat with red plastic visor | ernestine carter | the sunday times
1967 | david bond for slimma\nedward mann (hat)\nsaxone (shoes) | woman's trouser suit, hat & blouse in striped cotton | felicity green | the daily mirror
1968 | jean muir\nbally (shoes) | black-spotted white cotton voile dress | ailsa garland | fashion magazine
1969 | ossie clark for quorum\nrayne (shoes) | woman's silk chiffon and satin trouser suit in celia birtwell print | prudence glynn | the times
1970 | bill gibb for baccarat\nkaffe fassett (knitwear)\nchelsea cobbler (boots) | plaid wool skirt and blue and white blouse, knitted waistcoat, blue suede boots | beatrix miller | uk vogue
1971 | female: graziella fontana for judith hornby\nravel (sandals)\nmale: rupert lycett green for blades | female: hot pants suit in checked liberty cotton\nmale: black velvet evening suit & boots | serena sinclair and patrick lichfield | the daily telegraph
1972 | teenage girl:biba\nyoung girl: bobby hillson\nyoung boy: orange hand for montague burton | teenage girl: dress, hat & boots, all in red & white spotted cotton\nyoung girl: checked cotton dress & pinafore\nyoung boy: trousers, jumper and tank top | moira keenan | the sunday times
1973 | female: marc bohan for christian dior london\nmale: yves saint laurent rive gauche | female: white wool coat & hat\nmale: wool jacket, trousers & sweater | alison adburgham | the guardian
1974 | ottavio and rosita missoni\npasquali (shoes) | male & female ensembles in knitted wool & rayon | jennifer hocking | harper's bazaar and queen magazine
1975 | female: gina fratini\nmale: tommy nutter\nchelsea cobbler (shoes) | female: wedding dress, veil & posy basket, cream silk organza with mimosa print\nmale: bridegroom's frock coat suit, eau de nil wool | anna harvey | brides
1976 | female: kenzo takada of jungle jap\nmale: fiorucci | female: two printed cotton ensembles with wooden jewellery\nmale: hand-knitted sweater, two shirts and jeans | helena matheopoulos | the daily express
1977 | kenzo takada of jungle jap | shirt-dress in khaki cotton, straw hat & plimsolls | ann boyd | the observer
1978 | female: gordon luke clarke\nmale: cerruti | female: printed cotton & polyester jersey tunic, skirt and trousers worn with black leather skirt and coat\nmale: coat, jacket, waistcoat & trousers, knitted wool and wool tweed | barbara griggs | the daily mail
1979 | jean muir\nmanolo blahnik for zapata (shoes) | black rayon jersey dress & beret with black leather jacket | geraldine ranson | the sunday telegraph
1980 | calvin klein\ndiego della valle (sandals) | red & brown striped silk dress with leather belt & wooden jewellery | michael roberts | the sunday times
1981 | karl lagerfeld for chloé\nwalter steiger (shoes)\nugo correani (necklace) | printed white silk dress | vanessa de lisle | harper's & queen
1982 | margaret howell\nnigel preston of maxfield parrish (leather wear)\nmulberry (belt)\nmanolo blahnik for zapata (shoes) | two women's ensembles, a linen skirt, shirt and waistcoat and a blue suede and fawn chamois leather skirt & jacket with cotton shirt | grace coddington | uk vogue
1983 | sheridan barnett\nmanolo blahnik (shoes) | linen dress and coat | sally brampton | the observer
1984 | female: bodymap\nfemale: betty jackson\nbrian bolger: (scarf)\nmale: katharine hamnett | female: ensemble comprising skirt, jumper, stockings, hat, waxed jacket & earrings (bodymap)\nfemale: dress, cardigan & hat and scarf (jackson & bolger)\nmale: t-shirt, shirt and cotton trousers | brenda polan | the guardian
1985 | female: bruce oldfield\ncharles jourdan (shoes)\nmaria buck (jewellery)\nmale: scott crolla | female: black silk & gold lamé evening dress\nmale: shirt, crushed velvet trousers and ikat mules | suzy menkes | the times
1986 | giorgio armani | female: checked wool jacket, skirt, and black suede shoes\nmale: jacket, trousers, shirt and brogues | colin mcdowell | country life
1987 | john galliano\npatrick cox (shoes) | checked cotton coat, skirt, shirt & hat | debbi mason | elle
1988 | jean-paul gaultier for junior gaultier | black denim dress, mesh t-shirt, hat, tights & shoes | jeff banks | the clothes show (bbc)
1989 | rifat ozbek | woman's embroidered velvet evening ensemble | kathryn samuel | the daily telegraph
1990 | romeo gigli | woman's dark blue velvet trouser suit with organza blouse | joan burstein | browns
1991 | karl lagerfeld for chanel | pink lurex & wool tweed jacket & shoes, denim skirt & hat, belt & costume jewellery | elizabeth tilberis | vogue
1992 | ralph lauren | woman's black and white pinstripe trouser suit & shirt | liz smith | the times
1993 | donna karan | purple wool & stretch velvet dress, hat & boots | glenda bailey | marie claire
1994 | john galliano | black silk strapless evening dress | meredith etherington smith | harper's & queen
1995 | female: catherine rayner\nemma hope (shoes)\nmale: tom gilbey | female: beaded ivory silk satin wedding dress\nmale: ivory silk frock coat, cream wool trousers and embroidered waistcoat | sandra boler | brides
1996 | female: alexander mcqueen\nmale: paul smith | female: floral brocade top with red 'bumster' trousers\nmale: bright blue two-piece suit and shirt | tamsin blanchard | the independent
1997 | female: hussein chalayan\nfemale: julien macdonald\nfemale: lainey keogh\nfemale: deborah milner\nphilip treacy (bonnet) | female: purple evening dress with sunburst bead embroidery (chalayan)\nfemale: 'mermaid' evening dress, gold knitted rayon & horsehair (macdonald)\nfemale: evening dress and coat, black knit with beading (keogh)\nfemale: evening coat, purple velvet, with fur collar (milner)\nsculptural black bonnet | isabella blow | the sunday times
1998 | female: sonia rykiel\nmale: chris bailey for jigsaw menswear | female: black knitted sweater & combat trousers, with pink marabou stole\nmale: silver-grey suit, white t-shirt and ankle-length puffa jacket | iain r. webb | elle
1999 | alexander mcqueen | cream lace dress with brown leather collar and sandals | susannah frankel | the independent
2000 | donatella versace for versace | bamboo-print silk chiffon evening dress and jeweled mules | lisa armstrong | the times
2001 | tom ford for yves saint laurent rive gauche | 'peasant' ensemble of gauze top and velvet & satin skirt, with boots and velvet scarf | alexandra shulman | vogue
2002 | junya watanabe | dress, pieced together knit & jersey fabrics, with distressed cow-hide shoes | hilary alexander | the daily telegraph
2003 | marni | colorful printed dress | lucinda chambers | vogue
2004 | tom ford for yves saint laurent rive gauche | evening dress in chinese dragon print satin | sarajane hoare | vanity fair
2005 | alber elbaz for lanvin | blue silk faille dress with full skirt | charlie porter | gq; the guardian
2006 | prada | woman's olive green coat with fur patch pockets | sarah mower | 
2007 | giles deacon at giles | orange 'troubadour' dress with accompanying orange scarf | hywel davies | 
2008 | karl lagerfeld for chanel (trouser ensemble)\nkate moss for topshop (dress) | gold star and navy blue trouser ensemble\nlong sleeved black dress with heart-print | paula reed | grazia
2009 | antonio berardi | white and black trompe l'oeil corset dress | lucy yeomans | harper's bazaar
2010 | vivienne westwood | green ribbed shot-silk deconstructed dress | stephen jones | 
2011 | sarah burton for alexander mcqueen | white embroidered ivory tulle and organza ballgown | hamish bowles | vogue
2012 | raf simons for christian dior | embroidered and appliquéd silk cut-off ballgown and black cigarette pants | vanessa friedman | financial times
```

---

#### 案例 3: `nu-1798`

**问题**: in the 2008 presidential primary polling in iowa in 2008, how many times did a democrat have at least 50% of the vote?

**正确答案**: `15`

**当前项目预测**: `7`

**完整思维链**:
```
步骤 1: select_row
  思考: f_select_row([row 4, row 8, row 9, row 13, row 14, row 15, row 16])

  参数: [("['13', '14', '15', '16', '4', '8', '9']", np.float64(1.0))]

步骤 2: select_column
  思考: f_select_column([democrat, %])

  参数: [("['%', 'democrat']", np.float64(1.0))]

步骤 3: group_column
  思考: f_group_column(%)


步骤 4: simple_query
  思考: Explanation: We count the rows where the Democrat had at least 50% of the vote. The percentages listed are 50, 51, 51, 66, 58, 55, and 59. All 7 of these are at least 50%, so this happened 7 times.
  参数: [('7', np.float64(1.0))]

```

**完整表格**:
```
poll source | sample size | margin of error | date | democrat | % | republican | %
rasmussen reports | 500 | 4.5 | mar 31, 2008 | hillary clinton | 36 | john mccain | 51
rasmussen reports | 500 | 4.5 | mar 31, 2008 | barack obama | 46 | john mccain | 42
survey usa | 517 | 4.4 | mar 14-16, 2008 | hillary clinton | 44 | john mccain | 48
survey usa | 517 | 4.4 | mar 14-16, 2008 | barack obama | 50 | john mccain | 44
rasmussen reports | 500 |  | feb 18, 2008 | hillary clinton | 37 | john mccain | 47
rasmussen reports | 500 |  | feb 18, 2008 | barack obama | 44 | john mccain | 41
survey usa | 563 | 4.2 | feb 15-17, 2008 | hillary clinton | 41 | john mccain | 52
survey usa | 563 | 4.2 | feb 15-17, 2008 | barack obama | 51 | john mccain | 41
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 51 | rudy giuliani | 35
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 47 | mike huckabee | 45
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 44 | john mccain | 48
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 48 | mitt romney | 40
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 66 | rudy giuliani | 26
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 58 | mike huckabee | 35
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 55 | john mccain | 38
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 59 | mitt romney | 33
survey usa |  |  | dec. 17, 2007 | hillary clinton | 46 | mike huckabee | 45
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 47 | rudy giuliani | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 49 | mike huckabee | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 44 | john mccain | 48
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 49 | mitt romney | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 52 | rudy giuliani | 39
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 56 | mike huckabee | 35
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 50 | john mccain | 42
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 53 | mitt romney | 39
survey usa | 513 | 4.4 | oct 12-14, 2007 | hillary clinton | 48 | rudy giuliani | 43
survey usa | 506 | 4.3 | oct 12-14, 2007 | hillary clinton | 51 | mike huckabee | 41
survey usa | 502 | 4.5 | oct 12-14, 2007 | hillary clinton | 49 | john mccain | 44
survey usa | 498 | 4.5 | oct 12-14, 2007 | hillary clinton | 52 | ron paul | 36
survey usa | 506 | 4.4 | oct 12-14, 2007 | hillary clinton | 50 | mitt romney | 42
survey usa | 509 | 4.4 | oct 12-14, 2007 | hillary clinton | 50 | fred thompson | 42
```

**原始表格**:
```
poll source | sample size | margin of error | date | democrat | % | republican | %
rasmussen reports | 500 | 4.5 | mar 31, 2008 | hillary clinton | 36 | john mccain | 51
rasmussen reports | 500 | 4.5 | mar 31, 2008 | barack obama | 46 | john mccain | 42
survey usa | 517 | 4.4 | mar 14-16, 2008 | hillary clinton | 44 | john mccain | 48
survey usa | 517 | 4.4 | mar 14-16, 2008 | barack obama | 50 | john mccain | 44
rasmussen reports | 500 |  | feb 18, 2008 | hillary clinton | 37 | john mccain | 47
rasmussen reports | 500 |  | feb 18, 2008 | barack obama | 44 | john mccain | 41
survey usa | 563 | 4.2 | feb 15-17, 2008 | hillary clinton | 41 | john mccain | 52
survey usa | 563 | 4.2 | feb 15-17, 2008 | barack obama | 51 | john mccain | 41
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 51 | rudy giuliani | 35
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 47 | mike huckabee | 45
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 44 | john mccain | 48
survey usa | 543 | 4.3 | jan 4-6, 2008 | hillary clinton | 48 | mitt romney | 40
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 66 | rudy giuliani | 26
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 58 | mike huckabee | 35
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 55 | john mccain | 38
survey usa | 543 | 4.3 | jan 4-6, 2008 | barack obama | 59 | mitt romney | 33
survey usa |  |  | dec. 17, 2007 | hillary clinton | 46 | mike huckabee | 45
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 47 | rudy giuliani | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 49 | mike huckabee | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 44 | john mccain | 48
survey usa | 546 | 4.3 | nov 9-11, 2007 | hillary clinton | 49 | mitt romney | 43
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 52 | rudy giuliani | 39
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 56 | mike huckabee | 35
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 50 | john mccain | 42
survey usa | 546 | 4.3 | nov 9-11, 2007 | barack obama | 53 | mitt romney | 39
survey usa | 513 | 4.4 | oct 12-14, 2007 | hillary clinton | 48 | rudy giuliani | 43
survey usa | 506 | 4.3 | oct 12-14, 2007 | hillary clinton | 51 | mike huckabee | 41
survey usa | 502 | 4.5 | oct 12-14, 2007 | hillary clinton | 49 | john mccain | 44
survey usa | 498 | 4.5 | oct 12-14, 2007 | hillary clinton | 52 | ron paul | 36
survey usa | 506 | 4.4 | oct 12-14, 2007 | hillary clinton | 50 | mitt romney | 42
survey usa | 509 | 4.4 | oct 12-14, 2007 | hillary clinton | 50 | fred thompson | 42
```

---

