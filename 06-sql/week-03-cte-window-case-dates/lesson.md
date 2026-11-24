# SQL Week 3: CTEs, window functions, CASE, dates

Goal: write readable multi-step queries, solve "per group" and "compare to neighbour row" problems with window functions, and handle dates.
Budget: ~2.5 h reading + REPL, ~3 h exercises, ~1 h interview Q&A. This is the most interview-heavy week.
Run tests: `.venv/bin/pytest 06-sql/week-03-cte-window-case-dates -v`
SQLite 3.25+ is needed for window functions, 3.8.3+ for CTEs (your install is 3.53).

## 0. Data (see `schema.py`)
```
employees(id, name, dept, salary, manager_id, hire_date)   Ava is the root; Ben=Cara tie; Fay=Gus tie
sales(id, sale_date, region, amount)                       9 sales, Jan-Mar 2024, East/West
tickets(id, opened_at, closed_at, priority)                closed_at NULL = still open
```

## 1. CTEs (WITH)
A CTE gives a name to a subquery so the main query reads top to bottom.
```sql
WITH c AS (SELECT region, SUM(amount) AS total FROM sales GROUP BY region)
SELECT region, total FROM c WHERE total > (SELECT AVG(total) FROM c);
```
```
region | total
East   | 850
```
- Chain several: `WITH a AS (...), b AS (SELECT ... FROM a) SELECT ... FROM b`.
- Scope is a single statement. A CTE is not a table and is not stored.
- Postgres 12+ inlines non-recursive CTEs (before that they were optimisation fences; `MATERIALIZED`/`NOT MATERIALIZED` hints exist). MySQL 8+ supports CTEs.
- CTE vs subquery vs view vs temp table: CTE/subquery = same statement only; view = stored query definition; temp table = materialised, can be indexed, lives for the session.

## 2. Recursive CTEs
Two parts joined with `UNION ALL`: an **anchor** (non-recursive seed) and a **recursive step** that references the CTE itself. It repeats until the step returns no new rows.
```sql
-- Org chart with depth
WITH RECURSIVE s(id, name, level) AS (
    SELECT id, name, 0 FROM employees WHERE manager_id IS NULL          -- anchor
    UNION ALL
    SELECT e.id, e.name, s.level + 1 FROM employees e JOIN s ON e.manager_id = s.id   -- step
)
SELECT name, level FROM s ORDER BY level, name;
```
```
name | level
Ava  | 0
Ben  | 1
Fay  | 1
Jo   | 1
Cara | 2
Dan  | 2
Gus  | 2
Hana | 2
Kim  | 2
Eli  | 3
Ian  | 3
```
Uses: hierarchies (down: join `e.manager_id = s.id`; up: join `e.id = c.manager_id`), bill of materials, graph reachability, **generating series** (numbers, and the same idea for consecutive dates) so gaps show up in reports:
```sql
WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 5)
SELECT i, i * i AS square FROM n;
```
```
i | square
1 | 1
2 | 4
3 | 9
4 | 16
5 | 25
```
Always include a termination condition. For cyclic graphs track visited ids (a path string) or use `UNION` (dedupes) so it stops. Postgres: `WITH RECURSIVE` is required; Postgres has `generate_series` for series; MySQL needs `cte_max_recursion_depth` (default 1000).

## 3. Window functions
A window function computes a value for **each row** from a set of related rows (its window) **without collapsing rows** (unlike GROUP BY).
```sql
function(...) OVER (PARTITION BY cols ORDER BY cols  frame)
```
- `PARTITION BY`: restart per group (optional; omitted = whole result).
- `ORDER BY`: ordering inside the partition (required for ranking, LAG/LEAD).
- frame: which rows around the current one are aggregated.

They run after WHERE/GROUP BY/HAVING, so **you cannot filter on them in the same SELECT's WHERE**. Wrap in a subquery/CTE and filter outside. (Snowflake/BigQuery have `QUALIFY`; SQLite/Postgres/MySQL do not.)

### 3.1 Aggregate over partition
```sql
SELECT id, region, amount, AVG(amount) OVER (PARTITION BY region) AS region_avg
FROM sales WHERE id <= 4;
```
```
id | region | amount | region_avg
1  | East   | 100    | 125.0
3  | East   | 150    | 125.0
2  | West   | 200    | 160.0
4  | West   | 120    | 160.0
```
Every row keeps its identity and also sees the group average (compare with the correlated subquery of week 2).

### 3.2 ROW_NUMBER vs RANK vs DENSE_RANK
```sql
WITH t(name, score) AS (VALUES ('a', 90), ('b', 85), ('c', 85), ('d', 70))
SELECT name, score,
       ROW_NUMBER() OVER (ORDER BY score DESC, name) AS rn,
       RANK()       OVER (ORDER BY score DESC) AS rnk,
       DENSE_RANK() OVER (ORDER BY score DESC) AS drnk
FROM t;
```
```
name | score | rn | rnk | drnk
a    | 90    | 1  | 1   | 1
b    | 85    | 2  | 2   | 2
c    | 85    | 3  | 2   | 2
d    | 70    | 4  | 4   | 3
```
- `ROW_NUMBER`: unique 1..n; ties broken arbitrarily unless ORDER BY is made unique (add `, id`).
- `RANK`: ties share a rank, then **gaps** (1,2,2,4).
- `DENSE_RANK`: ties share a rank, **no gaps** (1,2,2,3).
- "Nth highest salary" -> `DENSE_RANK() = N`. "Top N rows" -> `ROW_NUMBER() <= N`. "Top N including ties" -> `RANK() <= N`.
- Top-N per group pattern:
```sql
SELECT id, region, amount FROM (
  SELECT id, region, amount,
         ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn
  FROM sales
) WHERE rn <= 2 ORDER BY region, amount DESC;
```
```
id | region | amount
5  | East   | 300
7  | East   | 250
8  | West   | 400
2  | West   | 200
```
- `NTILE(n)` splits into n buckets; `PERCENT_RANK`, `CUME_DIST` give relative position.

### 3.3 LAG / LEAD
Value from a previous/next row in the window (default offset 1, optional default value `LAG(x, 1, 0)`):
```sql
SELECT sale_date, amount, LAG(amount) OVER (ORDER BY sale_date) AS prev,
       LEAD(amount) OVER (ORDER BY sale_date) AS next
FROM sales WHERE id <= 4;
```
```
sale_date  | amount | prev | next
2024-01-03 | 100    | NULL | 200
2024-01-15 | 200    | 100  | 150
2024-01-28 | 150    | 200  | 120
2024-02-02 | 120    | 150  | NULL
```
Use for month-over-month change, time between events, "is this value higher than the previous one", and for **gaps and islands** (week 5). `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE` read other rows in the frame.

### 3.4 Running totals and frames
```sql
SELECT name, hire_date, salary, SUM(salary) OVER (ORDER BY hire_date) AS payroll_so_far
FROM employees WHERE id IN (1, 2, 3, 4, 6);
```
```
name | hire_date  | salary | payroll_so_far
Ava  | 2015-01-10 | 200000 | 200000
Ben  | 2016-03-01 | 150000 | 350000
Fay  | 2017-05-05 | 90000  | 440000
Cara | 2018-06-15 | 150000 | 590000
Dan  | 2019-09-01 | 120000 | 710000
```
Frames: `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` (3-row moving average), `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` (whole partition).
**Default frame trap:** with `ORDER BY` and no frame the default is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, which treats rows with equal ORDER BY values (peers) as one unit:
```sql
WITH t(v) AS (VALUES (10),(10),(20))
SELECT v, SUM(v) OVER (ORDER BY v) AS range_default, SUM(v) OVER (ORDER BY v ROWS UNBOUNDED PRECEDING) AS rows_frame FROM t;
```
```
v  | range_default | rows_frame
10 | 20            | 10
10 | 20            | 20
20 | 40            | 40
```
For a true row-by-row running total add a unique tie-breaker to ORDER BY or specify `ROWS`. Also, `LAST_VALUE` with the default frame returns the current row's value, not the partition's last: specify the full frame.

### 3.5 Window vs GROUP BY
GROUP BY reduces to one row per group; windows keep all rows. Typical combo: aggregate in a CTE first, then window over the aggregated rows (`LAG(revenue) OVER (ORDER BY month)` on monthly totals).
You may reuse a definition: `WINDOW w AS (PARTITION BY dept ORDER BY salary DESC)` then `OVER w`.

## 4. CASE
```sql
CASE WHEN salary >= 150000 THEN 'High' WHEN salary >= 90000 THEN 'Mid' ELSE 'Low' END   -- searched
CASE dept WHEN 'Eng' THEN 1 WHEN 'Sales' THEN 2 ELSE 0 END                               -- simple
```
First matching WHEN wins, so order conditions from most to least specific. No ELSE gives NULL. Works in SELECT, WHERE, ORDER BY, and inside aggregates.
**Conditional aggregation / pivot:**
```sql
SELECT strftime('%Y-%m', opened_at) AS month,
       SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) AS high,
       SUM(CASE WHEN priority = 'low'  THEN 1 ELSE 0 END) AS low
FROM tickets GROUP BY 1 ORDER BY 1;
```
```
month   | high | low
2024-03 | 2    | 1
2024-04 | 1    | 1
```
Counting with a condition: `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` or `COUNT(CASE WHEN cond THEN 1 END)` (COUNT ignores the NULLs from the missing ELSE). Postgres also has `FILTER (WHERE ...)`; the number of pivot columns must be known at query time (no dynamic pivot in plain SQL).

## 5. Dates and times (SQLite; others differ)
SQLite stores dates as TEXT (`'YYYY-MM-DD'` or `'YYYY-MM-DD HH:MM:SS'`), REAL (Julian day) or INTEGER (unix time). ISO text sorts correctly. Main functions:
```sql
SELECT date('2024-01-31','+1 month'),                         -- 2024-03-02 (Feb 31 overflows!)
       date('2024-03-15','start of month'),                   -- 2024-03-01
       date('2024-03-15','start of month','+1 month','-1 day'), -- 2024-03-31 (month end)
       strftime('%w','2024-03-15'),                           -- 5 (0 = Sunday)
       strftime('%Y-%m','2024-03-15'),                        -- 2024-03
       julianday('2024-03-15') - julianday('2024-03-01'),     -- 14.0 (days)
       strftime('%s','2024-03-15 00:00:00');                  -- 1710460800 (unix seconds)
```
- Difference in days: `julianday(b) - julianday(a)`; hours: `* 24`. Cast if you want integers.
- Group by month: `strftime('%Y-%m', ts)`.
- Half-open ranges for timestamps: `ts >= '2024-03-01' AND ts < '2024-04-01'`.
- `'now'` is UTC. Keep timestamps in UTC in storage; convert at the edge.

Other engines (be ready to translate):
| Task | SQLite | Postgres | MySQL |
|---|---|---|---|
| truncate to month | `date(d,'start of month')` | `date_trunc('month', d)` | `DATE_FORMAT(d,'%Y-%m-01')` |
| add days | `date(d,'+7 day')` | `d + INTERVAL '7 day'` | `DATE_ADD(d, INTERVAL 7 DAY)` |
| day difference | `julianday(b)-julianday(a)` | `b::date - a::date` | `DATEDIFF(b, a)` |
| extract | `strftime('%Y', d)` | `EXTRACT(YEAR FROM d)` | `YEAR(d)` |
| series | recursive CTE | `generate_series` | recursive CTE |
Time zones (`timestamptz`), DST, leap years, and month-end arithmetic are classic edge cases to mention.

## Common mistakes
1. Filtering on a window function in WHERE (error): wrap it in a subquery/CTE.
2. `RANK` when you wanted `DENSE_RANK` for "Nth highest" (gaps break N).
3. Non-unique ORDER BY in `ROW_NUMBER` or running totals (nondeterministic; peer rows share the RANGE frame).
4. Forgetting PARTITION BY (one big window).
5. `LAST_VALUE` with the default frame.
6. Recursive CTE without a stopping condition.
7. CASE branches in the wrong order; missing ELSE producing NULLs that break sums.
8. `date('2024-01-31','+1 month')` surprises; integer division when computing percentages (use `* 100.0`).
9. Grouping by a datetime instead of a date/month.
10. Using GROUP BY + self join where one window function would be simpler and faster.

## How interviewers probe this topic
- "Second highest salary", "Nth highest", "top 3 per department including ties" -> RANK family and ties.
- "Month-over-month growth", "difference from previous row" -> LAG.
- "Running total / moving average / cumulative percentage" -> frames.
- "What is the difference between ROW_NUMBER, RANK and DENSE_RANK?" with a tie example, then "which do you use for dedup" (ROW_NUMBER = 1).
- "Explain the order in which a query is evaluated; where do window functions run?"
- "Walk me through a recursive CTE" (anchor, step, termination) and "how would you prevent infinite loops on cyclic data?"
- "Pivot rows to columns" -> CASE + aggregate.
- "Rewrite this correlated subquery with a window function" and "what are the trade-offs?"
- Dates: "users active in the last 7 days", "first day of the month", "orders per week" and "what about time zones/months with no data?" (calendar table + LEFT JOIN).

## Your task
1. Run every example in the REPL.
2. Fill in `exercises.py` (21 functions) until green.
3. Do `interview-qa.md` aloud.
