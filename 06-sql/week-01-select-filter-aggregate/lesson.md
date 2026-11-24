# SQL Week 1: SELECT, filtering, NULL, aggregates, GROUP BY

Goal: write correct single-table queries and never be fooled by NULL.
Budget: ~2 h reading + trying examples, ~3 h exercises, ~1 h interview Q&A.

## 0. Setup
Everything runs on SQLite (`sqlite3` is in the Python standard library).
```
.venv/bin/python -i 06-sql/week-01-select-filter-aggregate/schema.py
>>> db = make_db()
>>> db.execute("SELECT name, salary FROM employees LIMIT 2").fetchall()
```
Tables for this week (see `schema.py`): `employees(id, name, dept, salary, hire_date, city, bonus)`
(13 rows, with NULLs in `dept`, `salary`, `city`, `bonus`) and `orders(id, customer, amount, status, order_date)`.

Run tests: `.venv/bin/pytest 06-sql/week-01-select-filter-aggregate -v`.
Each exercise function **returns a SQL string**; the test executes it and compares rows and column names.

## 1. Anatomy of a query
```sql
SELECT   name, salary          -- 5. which columns / expressions to output
FROM     employees             -- 1. which table
WHERE    dept = 'Sales'        -- 2. filter ROWS
GROUP BY dept                  -- 3. collapse rows into groups
HAVING   COUNT(*) > 2          -- 4. filter GROUPS
ORDER BY salary DESC           -- 6. sort
LIMIT 3 OFFSET 0;              -- 7. cut
```
You *write* SELECT first, but the database *logically evaluates* in the numbered order
FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT.
This explains most beginner errors (e.g. WHERE cannot use aggregates or, in standard SQL, SELECT aliases).
(SQLite is lenient and allows aliases in WHERE/GROUP BY; Postgres is not. Do not rely on it.)

## 2. SELECT, aliases, expressions
```sql
SELECT name, salary, salary / 12 AS monthly FROM employees WHERE id = 1;
```
`AS` renames an output column. Avoid `SELECT *` in real code (breaks when columns change, wastes I/O); fine for exploring.
Integer division trap: in SQLite and Postgres `7 / 2` is `3`. Use `7 / 2.0` or `CAST(x AS REAL)`.

## 3. WHERE: filtering rows
Operators: `= <> < <= > >=`, `AND OR NOT`, `IN (...)`, `BETWEEN a AND b` (inclusive both ends), `LIKE`.
```sql
SELECT name FROM employees WHERE city = 'NYC' AND salary >= 70000;
SELECT name FROM employees WHERE dept IN ('HR', 'Marketing');
SELECT name FROM employees WHERE hire_date BETWEEN '2021-01-01' AND '2022-12-31';
SELECT name FROM employees WHERE name LIKE 'M%';      -- % = any chars, _ = exactly one char
```
- **Precedence**: `AND` binds tighter than `OR`. `salary > 100000 OR dept = 'HR' AND city = 'NYC'` means
  `salary > 100000 OR (dept = 'HR' AND city = 'NYC')` and returns Alice, Carol, Heidi. Use parentheses.
- String literals use **single quotes**. Double quotes are identifiers (SQLite forgives, others do not).
- `LIKE` is case-insensitive for ASCII in SQLite and MySQL, case-sensitive in Postgres (use `ILIKE`).
- Dates: SQLite has no date type; store ISO-8601 text `YYYY-MM-DD` so string order equals date order.

## 4. ORDER BY, LIMIT, OFFSET
```sql
SELECT name, hire_date FROM employees ORDER BY hire_date DESC LIMIT 2;
```
```
name  | hire_date
Oleg  | 2024-03-01
Niaj  | 2024-02-01
```
- Without `ORDER BY` row order is **undefined**. Never assume "insertion order".
- Add a **tie-breaker** (`ORDER BY salary DESC, name`) so the result is deterministic. Bob and Ivan both earn 95000.
- `LIMIT n OFFSET m` paginates (`LIMIT 4 OFFSET 4` = page 2 of size 4). Large offsets are slow (the DB still walks the skipped rows); production uses keyset pagination (`WHERE id > last_seen_id ORDER BY id LIMIT n`).
- NULL ordering: SQLite treats NULL as smallest (first in ASC, last in DESC). Postgres treats NULL as largest. Both accept `NULLS FIRST/LAST` (SQLite >= 3.30).
  `ORDER BY salary DESC LIMIT 1` may therefore return NULL in Postgres! Filter `WHERE salary IS NOT NULL`.

## 5. NULL: the single most tested concept
NULL means **unknown / missing**, not zero or empty string. Any comparison with NULL yields NULL (unknown), and `WHERE` keeps only rows where the condition is TRUE.
```sql
SELECT 1 = NULL, NULL = NULL, NULL IS NULL, 1 IN (2, NULL), 1 NOT IN (2, NULL);
```
```
1 = NULL | NULL = NULL | NULL IS NULL | 1 IN (2, NULL) | 1 NOT IN (2, NULL)
NULL     | NULL        | 1            | NULL           | NULL
```
Rules:
1. Test with `IS NULL` / `IS NOT NULL`, never `= NULL`.
2. Three-valued logic: `TRUE AND NULL = NULL`, `FALSE AND NULL = FALSE`, `TRUE OR NULL = TRUE`, `NOT NULL = NULL`.
3. Arithmetic with NULL gives NULL: `bonus + 100` is NULL when bonus is NULL.
4. `COALESCE(x, default)` returns the first non-NULL argument. `IFNULL(x, d)` is the SQLite/MySQL two-arg version. `NULLIF(a, b)` returns NULL when a = b (classic divide-by-zero guard: `x / NULLIF(y, 0)`).
5. **`NOT IN` with a NULL in the list returns no rows** (shown above). This is the #1 NULL trap; prefer `NOT EXISTS` (week 2).
6. Aggregates (except `COUNT(*)`) **ignore** NULLs.
7. `DISTINCT`, `GROUP BY` and `UNION` treat all NULLs as equal (one group), even though `NULL = NULL` is unknown.

The classic filter trap:
```sql
SELECT COUNT(*) FROM employees WHERE city <> 'NYC';       -- 7: Oleg (city NULL) silently missing
SELECT COUNT(*) FROM employees WHERE city IS NOT 'NYC';   -- 8 (SQLite's null-safe <>)
-- portable: WHERE city <> 'NYC' OR city IS NULL      (Postgres: city IS DISTINCT FROM 'NYC'; MySQL: NOT (city <=> 'NYC'))
```
```sql
SELECT name, bonus, bonus + 100 AS plus100, COALESCE(bonus, 0) AS safe
FROM employees WHERE id IN (1, 2, 11);
```
```
name    | bonus | plus100 | safe
Alice   | 5000  | 5100    | 5000
Bob     | NULL  | NULL    | 0
Mallory | 0     | 100     | 0
```
Note Mallory: bonus 0 is a *known* zero; Bob's bonus is unknown. `WHERE bonus IS NULL` finds Bob, not Mallory.

## 6. Aggregate functions
`COUNT(*)`, `COUNT(col)`, `COUNT(DISTINCT col)`, `SUM`, `AVG`, `MIN`, `MAX`. They collapse many rows into one value.
```sql
SELECT COUNT(*) AS n_rows, COUNT(amount) AS n_amount, SUM(amount) AS s,
       AVG(amount) AS a, AVG(COALESCE(amount, 0)) AS a0 FROM orders;
```
```
n_rows | n_amount | s      | a                  | a0
12     | 11       | 1780.5 | 161.86363636363637 | 148.375
```
- `COUNT(*)` counts rows; `COUNT(amount)` counts non-NULL amounts.
- `AVG(amount)` = 1780.5 / 11, **not** / 12. Whether to treat missing as 0 is a business decision. State your choice in an interview.
- `SUM` over zero rows (or all NULL) is NULL, not 0: use `COALESCE(SUM(x), 0)`.
- `COUNT(DISTINCT city)` ignores NULL (so 3 for our data).
- Without GROUP BY, an aggregate query returns exactly **one** row (even on an empty table).

## 7. GROUP BY and HAVING
```sql
SELECT city, COUNT(*) AS n, MAX(salary) AS top_salary
FROM employees GROUP BY city;
```
```
city   | n | top_salary
NULL   | 1 | 50000
Austin | 4 | 70000
NYC    | 5 | 120000
SF     | 3 | 95000
```
(NULL forms its own group.)

Rule: every column in SELECT must be either in GROUP BY or inside an aggregate. SQLite will let you break this (returns an arbitrary row's value!); Postgres errors; MySQL depends on `ONLY_FULL_GROUP_BY`.

`WHERE` filters rows **before** grouping; `HAVING` filters groups **after** aggregation:
```sql
SELECT city, COUNT(*) AS n FROM employees GROUP BY city HAVING COUNT(*) >= 4;
```
```
city   | n
Austin | 4
NYC    | 5
```
Rule of thumb: if the condition does not need an aggregate, put it in WHERE (it is cheaper: fewer rows to group).

Group by several columns, and by expression:
```sql
SELECT customer, substr(order_date, 1, 7) AS month, COUNT(*) AS n
FROM orders GROUP BY customer, month ORDER BY customer, month;
```
```
customer | month   | n
acme     | 2024-01 | 2
acme     | 2024-03 | 1
globex   | 2024-01 | 1
globex   | 2024-02 | 1
globex   | 2024-03 | 1
hooli    | 2024-03 | 2
initech  | 2024-02 | 2
umbrella | 2024-03 | 2
```
Another: a per-customer summary, sorted by an aggregate:
```sql
SELECT customer, COUNT(*) AS n, SUM(amount) AS total FROM orders GROUP BY customer ORDER BY total DESC;
```
```
customer | n | total
acme     | 3 | 750.0
globex   | 3 | 375.5
umbrella | 2 | 240.0
hooli    | 2 | 240.0
initech  | 2 | 175.0
```
(hooli and umbrella tie at 240, so add a tie-breaker in real code.)

## 8. DISTINCT
`SELECT DISTINCT dept, city FROM employees WHERE dept = 'Sales'` removes duplicate **rows** (the whole selected tuple), giving (Sales, Austin) and (Sales, NYC). `DISTINCT` is not a function: `SELECT DISTINCT(dept), city` still dedups the pair.
Use `COUNT(DISTINCT x)` for unique counts. Reaching for DISTINCT to "fix" duplicates after a join usually hides a wrong join (week 2).

## Common mistakes
1. `WHERE col = NULL` (always empty). Use `IS NULL`.
2. `<>` / `NOT IN` silently dropping NULL rows.
3. Aggregate in WHERE (`WHERE COUNT(*) > 2` is an error). Use HAVING.
4. Selecting a non-grouped column and trusting the value.
5. Relying on row order without ORDER BY, or ordering by a non-unique column and expecting stable results.
6. Integer division (`1 / 2 = 0`).
7. Using `LIMIT 1` with `ORDER BY` on a nullable column (NULL may win).
8. `COUNT(col)` when you meant `COUNT(*)` (or vice versa).
9. `BETWEEN` on timestamps: `BETWEEN '2024-01-01' AND '2024-01-31'` misses `'2024-01-31 15:00'`. Prefer `>= start AND < next_start`.
10. Double-quoted string literals.

## How interviewers probe this topic
- "What is the difference between WHERE and HAVING?" followed by "can I put the filter in either?" (yes if non-aggregate; WHERE is cheaper).
- "What does `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)` return?" with a table that has NULLs and duplicates.
- A table with NULL: "What does `SELECT * FROM t WHERE x NOT IN (SELECT y FROM u)` return if u.y has a NULL?"
- "Why is my row missing?" (`<>` with NULL).
- "Write a query for the top 3 salaries" then "what about ties?" (leads to week 3 `DENSE_RANK`).
- "Order of evaluation of a SQL query?" and "why can't I use an alias in WHERE?"
- "Is `AVG` ignoring NULLs correct for this business question?" (communicating assumptions is graded).
- They watch for: thinking out loud about NULLs, naming columns explicitly, deterministic ORDER BY, asking clarifying questions about ties and NULLs.

## Your task
1. Read and run every example above in the REPL.
2. Fill in `exercises.py` (18 functions), run the tests until green.
3. Answer `interview-qa.md` out loud without looking, then compare.
