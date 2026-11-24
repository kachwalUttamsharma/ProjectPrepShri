# SQL cheat sheet (SQLite flavoured, notes for Postgres/MySQL)

## Logical order of execution
FROM / JOIN -> WHERE -> GROUP BY -> HAVING -> window functions -> SELECT -> DISTINCT -> ORDER BY -> LIMIT.
Consequence: you cannot use window functions or (in standard SQL) select aliases in `WHERE`; use a subquery or CTE.

## NULL rules
- Any comparison with NULL is unknown: `x = NULL` never true. Use `IS NULL`, `IS NOT NULL`.
- Null-safe equality: `IS` / `IS NOT` (SQLite), `IS NOT DISTINCT FROM` (Postgres), `<=>` (MySQL).
- `COUNT(*)` counts rows, `COUNT(col)` skips NULLs. `SUM`, `AVG`, `MIN`, `MAX` skip NULLs.
- `COALESCE(a, b, 0)`, `NULLIF(a, 0)` (turns 0 into NULL, avoids divide by zero).
- `NOT IN (subquery with NULL)` returns nothing. Prefer `NOT EXISTS`.
- NULLs group together in `GROUP BY` and `DISTINCT`.

## Joins
| Join | Keeps |
|------|-------|
| INNER | matching pairs only |
| LEFT | all left rows, NULLs for no match |
| RIGHT / FULL | SQLite 3.39+, otherwise swap tables or UNION |
| CROSS | every pair |
| Self | same table under two aliases |

- Anti-join: `LEFT JOIN ... WHERE right.key IS NULL` or `NOT EXISTS`.
- Semi-join: `EXISTS` or `IN` (no duplicates from the right side).
- Filter on the right table of a LEFT JOIN belongs in `ON`, not `WHERE`.
- Fan-out: joining a one-to-many then summing a parent column inflates it. Aggregate first, then join.

## Aggregation
`GROUP BY` columns must cover every non-aggregated select column. `HAVING` filters groups, `WHERE` filters rows. Conditional aggregation: `SUM(CASE WHEN cond THEN x ELSE 0 END)`. `COUNT(DISTINCT x)`.

## Set operations
`UNION` (dedupes) vs `UNION ALL` (faster, keeps all), `INTERSECT`, `EXCEPT`. Columns must match in count and type.

## Subqueries and CTEs
- Scalar: one value. Correlated: references the outer row, runs per row logically.
- `WITH name AS (...)` for readability. `WITH RECURSIVE t AS (anchor UNION ALL step)` needs a stop condition.

## Window functions
`fn() OVER (PARTITION BY a ORDER BY b ROWS BETWEEN x AND y)`
- Ranking: `ROW_NUMBER`, `RANK` (gaps after ties), `DENSE_RANK`, `NTILE(n)`.
- Offsets: `LAG(x, n, default)`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE` (mind the frame).
- Aggregates over windows: `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`.
- Default frame with `ORDER BY` is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` (ties are peers). Use `ROWS` for physical rows.

## Pattern templates
Replace the placeholders `t`, `grp`, `val`, `ts`, `id`.

- Nth highest value: rank distinct values with `DENSE_RANK() OVER (ORDER BY val DESC)`, filter rank = N.
- Duplicates: `SELECT cols, COUNT(*) FROM t GROUP BY cols HAVING COUNT(*) > 1`.
- Keep one per duplicate group: choose a survivor (`MIN(id)`) and delete rows not in the survivor set.
- Top N per group: `ROW_NUMBER() OVER (PARTITION BY grp ORDER BY val DESC)` in a subquery, filter `rn <= N`.
- Islands: `val - ROW_NUMBER() OVER (ORDER BY val)` gives a constant per consecutive run; group on it.
- Gaps: `LEAD(val) OVER (ORDER BY val) - val > 1`.
- Sessions: `LAG(ts)` gap, flag when gap > timeout or NULL, running `SUM(flag)` is the session number.
- Running total: `SUM(val) OVER (ORDER BY ts ROWS UNBOUNDED PRECEDING)`.
- Period over period: aggregate per period, then `LAG` over the aggregated rows, guard with `NULLIF`.
- Percent of total: `val * 100.0 / SUM(val) OVER ()`.
- Pivot: one `SUM(CASE WHEN key = 'x' THEN val END)` per output column.
- Division ("every"): `GROUP BY entity HAVING COUNT(DISTINCT y) = (SELECT COUNT(DISTINCT y) FROM ys)`.
- Median: row number plus group count, keep the middle one or two rows, average.
- Anti-join: `WHERE NOT EXISTS (SELECT 1 FROM other o WHERE o.k = t.k)`.
- Conditional upsert (SQLite/Postgres): `INSERT ... ON CONFLICT(key) DO UPDATE SET ...`.

## Dates (SQLite)
`date('now')`, `date(d, '+1 month')`, `strftime('%Y-%m', d)`, `julianday(a) - julianday(b)` for day difference. Store ISO `YYYY-MM-DD` text so comparisons and sorting work. Postgres: `date_trunc`, `age`, interval arithmetic. MySQL: `DATE_ADD`, `DATEDIFF`.

## Schema and constraints
`PRIMARY KEY`, `UNIQUE`, `NOT NULL`, `CHECK`, `FOREIGN KEY ... ON DELETE CASCADE`. SQLite needs `PRAGMA foreign_keys = ON` per connection. Normalize to remove redundancy (1NF atomic, 2NF no partial dependency, 3NF no transitive dependency); denormalize deliberately for read speed.

## Indexes
- B-tree helps equality, range, `ORDER BY`, and joins on the indexed columns.
- Composite index: leftmost-prefix rule; equality columns first, then range or sort column.
- Covering index: contains every column the query needs, so no table lookup.
- Not usable when you wrap the column in a function, use a leading wildcard `LIKE '%x'`, or compare with mismatched types.
- Every index slows writes and uses space.
- Check with `EXPLAIN QUERY PLAN`: `SEARCH ... USING INDEX` is good, `SCAN` on a big table is a warning.

## Transactions and isolation
- ACID: atomic, consistent, isolated, durable.
- Isolation levels: read uncommitted, read committed, repeatable read, serializable. Anomalies: dirty read, non-repeatable read, phantom read, write skew.
- Postgres default is read committed (MVCC). MySQL InnoDB default is repeatable read. SQLite is serializable with a single writer.
- Deadlock: two transactions wait on each other; avoid with a consistent lock order and short transactions; retry on failure.
- Optimistic locking: version column, `UPDATE ... WHERE id = ? AND version = ?`, check rows affected.

## SQL vs NoSQL, OLTP vs OLAP
- SQL: strong schema, joins, transactions. NoSQL: flexible schema, horizontal scale, often eventual consistency, access patterns known up front.
- OLTP: many small reads and writes, row stores, normalized. OLAP: large scans and aggregates, column stores, denormalized star schemas.

## Interview checklist
1. Clarify grain, ties, NULLs, duplicates, empty groups.
2. Build in CTEs and name steps.
3. Check fan-out after each join.
4. Alias everything, qualify columns.
5. Guard division, use `100.0` for percentages.
6. State the index you would add and the complexity.
