# Week 5: Interview problem set

This week is practice, not new syntax. The 26 exercises in `exercises.py` are the classic questions that show up in Google, Uber and similar SQL rounds. This lesson gives you a method and the pattern behind each problem family. The examples here use tiny made-up data so they do not give away the exercises.

Run the tests with `pytest -q` from this folder. Work the problems in order of family, not in file order, if you prefer.

## 1. A method for any SQL interview question

1. Restate the question and ask about the grain. "One row per what?" in the output and in each input table.
2. Ask about edge cases out loud: NULLs, ties, duplicates, empty groups, missing days.
3. Sketch the output columns first, then work backwards.
4. Build in small steps with CTEs. Name each step for what it produces.
5. Check fan-out after every join. Count rows before and after.
6. Run it mentally on 3 or 4 rows, including a tie and a NULL.
7. State complexity and indexes at the end ("this scans once and sorts once").

Interviewers grade the process as much as the answer. Talking through ties and NULLs unprompted is a strong signal.

## 2. Problem families and their patterns

### 2.1 Nth highest and ties
Rank, then filter. `DENSE_RANK` counts distinct values, so "second highest salary" means rank 2 with `DENSE_RANK`. `RANK` skips numbers after ties and `ROW_NUMBER` breaks ties arbitrarily.

```sql
WITH t(n, v) AS (VALUES ('a',30),('b',20),('c',20),('d',10))
SELECT n, v, DENSE_RANK() OVER (ORDER BY v DESC) AS dr FROM t;
```
```
a | 30 | 1
b | 20 | 2
c | 20 | 2
d | 10 | 3
```
Ask: what if there is no second value? A scalar subquery returns NULL, which is usually the expected answer. A bare `LIMIT 1 OFFSET 1` returns no row. Know both.

### 2.2 Duplicates
Find them with `GROUP BY ... HAVING COUNT(*) > 1`. Delete them by keeping one row per group: rank rows within each duplicate group, or keep `MIN(id)` per group, and delete the rest. Always say which row you keep and why.

```sql
WITH t(k, v) AS (VALUES ('x',1),('x',2),('y',5))
SELECT k, COUNT(*) AS n FROM t GROUP BY k HAVING COUNT(*) > 1;
```
```
x | 2
```

### 2.3 Top N per group
`ROW_NUMBER() OVER (PARTITION BY group ORDER BY metric DESC)` in a subquery, then filter `rn <= N`. Switch to `DENSE_RANK` if ties should all be included. A correlated count (`SELECT COUNT(DISTINCT ...) ... WHERE other > this`) is the pre-window alternative, and interviewers like to hear it.

### 2.4 Compare to a related row
Self-join (employee vs manager), or a window function (`LAG`, `LEAD`, `AVG() OVER`). Pick the self-join when the relation is a key, the window when it is order or a partition.

### 2.5 Relational division ("did X for every Y")
Count distinct matches per entity and compare to the total number of Ys:
`HAVING COUNT(DISTINCT y) = (SELECT COUNT(DISTINCT y) FROM ys)`. Watch for NULL and for duplicates, which is why the `DISTINCT` is there.

### 2.6 Median
SQLite has no `MEDIAN`. Number rows within each group with `ROW_NUMBER` and also compute the group's `COUNT(*) OVER (PARTITION BY ...)`. Keep the middle row (odd count) or the two middle rows (even count) and average them.

```sql
-- rows with rn IN ((cnt+1)/2, (cnt+2)/2) are the middle one or two (integer division)
```
Group a has 4 values 1..4, so the middle rows are 2 and 3. Group b has 3 values, so the middle row is 20.

### 2.7 Gaps and islands (consecutive runs)
Subtract `ROW_NUMBER()` from the value (or from a day number). Consecutive values give the same difference, so the difference identifies the island. Group by it.

```sql
WITH t(d) AS (VALUES (1),(2),(3),(7),(8),(10))
SELECT MIN(d) AS start, MAX(d) AS stop, COUNT(*) AS len
FROM (SELECT d, d - ROW_NUMBER() OVER (ORDER BY d) AS grp FROM t)
GROUP BY grp;
```
```
1 | 3 | 3
7 | 8 | 2
10 | 10 | 1
```
Duplicates break this. Deduplicate first. For dates use `julianday(date)`. The "gaps" are the spaces between one island's end and the next island's start; `LEAD` finds them too.

### 2.8 Sessionization
Sort events per user, compute the gap to the previous event with `LAG`, flag a new session when the gap exceeds the timeout (or there is no previous event), then take a running `SUM` of the flags to get a session number.

```sql
WITH t(u, ts) AS (VALUES ('u',0),('u',10),('u',50),('u',55))
SELECT u, ts,
       ts - LAG(ts) OVER (PARTITION BY u ORDER BY ts) AS gap
FROM t;
```
```
u | 0  | NULL
u | 10 | 10
u | 50 | 40
u | 55 | 5
```
With a 30 unit timeout the third row starts a new session. Flag, then running sum.

### 2.9 Running and rolling metrics
`SUM() OVER (ORDER BY ...)` for running totals. Remember the default frame is `RANGE ... CURRENT ROW`, which treats tied order values as peers; write `ROWS BETWEEN ...` when you mean physical rows. A rolling window of N days over data with missing days needs a calendar (recursive CTE) or a `RANGE` on a numeric day, otherwise "last 7 rows" is not "last 7 days". Decide what to do for the first days, where the window is not full.

### 2.10 Period over period
Aggregate to the period first (a CTE), then `LAG` over the aggregated rows. Guard the division: `NULLIF(prev, 0)`, and say what you return for the first period (NULL).

### 2.11 Retention and funnels
Join the table to itself on user with a date offset, or compare each user's first event date to later activity. Funnels: one conditional count per step (`COUNT(DISTINCT CASE WHEN step = 'x' THEN user END)`). Decide whether order of steps matters. Make the denominator explicit.

### 2.12 Pivot
Conditional aggregation: `SUM(CASE WHEN col = 'x' THEN val END)` per output column, grouped by the row key. The column list is fixed in SQL; dynamic pivots need generated SQL.

### 2.13 Percent of total
`value * 100.0 / SUM(value) OVER ()`. The `100.0` avoids integer division. Round at the end only.

### 2.14 Bucketing
Integer arithmetic (`salary / 10000 * 10000`) or `CASE`. Decide whether empty buckets must be shown; if so you need a generated list of buckets to `LEFT JOIN` from.

### 2.15 Adjacent row tricks
Swapping or pairing neighbours can be done with `CASE` on id parity plus a self-join or `LEAD`/`LAG`. Ask what happens when the row count is odd.

## 3. Common mistakes

- `RANK` when the question wants distinct values (use `DENSE_RANK`).
- `COUNT(*)` after a LEFT JOIN, counting the NULL-extended row.
- Filtering the right table of a LEFT JOIN in `WHERE`, which silently makes it an inner join.
- `NOT IN` with a subquery that can return NULL.
- Integer division in percentages and ratios.
- Joining before aggregating and multiplying rows (fan-out), then summing the inflated values.
- Dividing by zero in growth rates.
- Ignoring ties, duplicates and NULLs, then not saying so.
- Forgetting `ORDER BY` when the problem needs a particular order. Without it, row order is not guaranteed.
- Window functions in `WHERE`. They need a subquery or CTE.

## 4. How interviewers probe

- "What if two employees tie?" Know the exact behaviour of `ROW_NUMBER`, `RANK`, `DENSE_RANK`.
- "Can you do it without window functions?" Have a correlated subquery or self-join version ready.
- "What if the table has a billion rows?" Talk about indexes, partitions, pre-aggregation, and avoiding self-joins on huge tables.
- "What does your query return for an empty group or a NULL?" Walk through it.
- "Can you make it shorter or faster?" Remove a join, reuse a CTE, filter earlier.
- "Show me the query plan." Use `EXPLAIN QUERY PLAN` and name the index you would add.
- "How would you test this?" A tiny table with ties, NULLs, a duplicate and an empty group.

## 5. Study plan for the week

1. Do each family cold, no notes, then compare with your own earlier work only after the test passes.
2. For every problem, write a second solution with a different technique (window vs subquery).
3. Time yourself: 15 minutes per medium problem, 25 for a hard one.
4. Read `cheatsheet.md` the day before an interview.
