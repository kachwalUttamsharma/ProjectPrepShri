# SQL Week 2: Joins and subqueries

Goal: combine tables correctly, spot fan-out and NULL traps, and pick between JOIN / IN / EXISTS.
Budget: ~2 h reading + REPL, ~3 h exercises, ~1 h interview Q&A.
Run tests: `.venv/bin/pytest 06-sql/week-02-joins-subqueries -v`

## 0. The data (see `schema.py`)
```
departments(id, name, location)      Engineering, Sales, HR, Legal (Legal is empty)
employees(id, name, dept_id, manager_id, salary)   Ian has dept_id NULL; Ava (CEO) has manager_id NULL
projects(id, name, dept_id)
assignments(emp_id, project_id, hours)             Fay, Gus, Hana have no assignment
customers(id, name, country)         Hooli and Stark never ordered
orders(id, customer_id, order_date, total)
```
Foreign key = a column that points at another table's primary key (`employees.dept_id -> departments.id`). A join matches rows on that relationship.

## 1. INNER JOIN: only matching rows
```sql
SELECT p.name AS project, d.name AS department
FROM projects p JOIN departments d ON d.id = p.dept_id;
```
```
project | department
Atlas   | Engineering
Beacon  | Engineering
Compass | Sales
```
Delta (dept_id NULL) vanished: NULL never equals anything, so no match. `JOIN` = `INNER JOIN`. Use table aliases (`e`, `d`) and qualify every column.

## 2. LEFT JOIN: keep every left row
```sql
SELECT p.name AS project, d.name AS department
FROM projects p LEFT JOIN departments d ON d.id = p.dept_id;
```
```
project | department
Atlas   | Engineering
Beacon  | Engineering
Compass | Sales
Delta   | NULL
```
Unmatched left rows get NULLs for all right columns. `RIGHT JOIN` is the mirror (SQLite supports it since 3.39; MySQL/Postgres always have). Most people just swap the table order and write LEFT. `FULL OUTER JOIN` keeps unmatched rows from both sides (SQLite >= 3.39, Postgres yes, MySQL no).
```sql
SELECT d.name, e.name AS employee FROM employees e RIGHT JOIN departments d ON d.id = e.dept_id WHERE d.id IN (3, 4);
```
```
name  | employee
HR    | Gus
HR    | Hana
Legal | NULL
```

### ON vs WHERE in outer joins (very common interview trap)
```sql
-- filter in ON: departments are kept, employees are matched only if rich
SELECT d.name, e.name FROM departments d
LEFT JOIN employees e ON e.dept_id = d.id AND e.salary > 100000
WHERE d.id IN (2, 3);
-- Sales | NULL
-- HR    | NULL

-- same condition in WHERE: NULL-extended rows fail it, so the LEFT JOIN degrades to an INNER JOIN
SELECT d.name, e.name FROM departments d
LEFT JOIN employees e ON e.dept_id = d.id
WHERE e.salary > 100000 AND d.id IN (1, 2);
-- Engineering | Ava / Ben / Cara / Jo      (Sales is gone)
```
Rule: conditions on the **right** table of a LEFT JOIN belong in `ON` if you want to keep unmatched left rows.

## 3. Anti-join: "rows with no match"
Three equivalent ways:
```sql
-- departments with no project.  (a) LEFT JOIN ... IS NULL
SELECT d.name FROM departments d LEFT JOIN projects p ON p.dept_id = d.id WHERE p.id IS NULL;
-- (b) NOT EXISTS   (preferred: NULL-safe, clear intent)
SELECT name FROM departments d WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.dept_id = d.id);
-- (c) NOT IN   (dangerous with NULLs)
SELECT name FROM departments WHERE id NOT IN (SELECT dept_id FROM projects);
```
(a) and (b) return HR and Legal. (c) returns **nothing**, because project Delta has `dept_id` NULL: that is the trap below in action. In (a) test a column that is NOT NULL in the right table (its primary key).

**NOT IN trap:** `SELECT name FROM employees WHERE id NOT IN (SELECT manager_id FROM employees)` returns **zero rows** because Ava's `manager_id` is NULL. Adding `WHERE manager_id IS NOT NULL` inside the subquery (or using NOT EXISTS) gives Cara, Eli, Fay, Hana, Ian, Jo (the non-managers).

## 4. Semi-join: "rows that have a match"
`EXISTS` / `IN` keep left rows that have at least one match **without duplicating** them:
```sql
SELECT name FROM departments d WHERE EXISTS (SELECT 1 FROM projects p WHERE p.dept_id = d.id);
-- Engineering, Sales
```
A plain JOIN would return Engineering once per project (fan-out). That's why "find X who have at least one Y" is a semi-join, not a join + DISTINCT.

## 5. Self-join
Join a table to itself using two aliases: hierarchy, comparing rows with each other.
```sql
SELECT e.name AS employee, m.name AS manager
FROM employees e LEFT JOIN employees m ON m.id = e.manager_id WHERE e.id <= 3;
```
```
employee | manager
Ava      | NULL
Ben      | Ava
Cara     | Ben
```
Self-joins also compare rows with each other. To list each unordered pair once, join on the shared attribute plus an inequality on the key (`a.id < b.id`): it removes self-pairs and mirrored (B,A) copies. To compare a row with its related row, put the comparison in `WHERE` after joining on the key.

## 6. CROSS JOIN: every combination
```sql
SELECT s.size, c.color
FROM (SELECT 'S' AS size UNION ALL SELECT 'M') s
CROSS JOIN (SELECT 'red' AS color UNION ALL SELECT 'blue') c;
```
```
size | color
S    | red
S    | blue
M    | red
M    | blue
```
n x m rows. Use deliberately for report skeletons / calendar x entity grids, then LEFT JOIN the facts onto it so missing combinations show 0. Accidental cross joins (forgetting the ON clause, or `FROM a, b` with a forgotten WHERE) are a classic performance bug.

## 7. Joins with aggregation: fan-out and COUNT
```sql
SELECT d.name AS department, COUNT(*) AS wrong, COUNT(p.id) AS right_
FROM departments d LEFT JOIN projects p ON p.dept_id = d.id GROUP BY d.id, d.name;
```
```
department  | wrong | right_
Engineering | 2     | 2
Sales       | 1     | 1
HR          | 1     | 0
Legal       | 1     | 0
```
`COUNT(*)` counts the NULL-extended row for HR and Legal. Count a column of the optional table.

**Fan-out (join multiplication):** joining a "one" row to two different "many" tables multiplies rows. Customer Acme has 3 orders; joining 2 other rows to it yields 6 rows and `SUM(o.total)` becomes 1000 instead of 500. Fix: aggregate each many-side separately in a subquery/CTE first, then join the results.

## 8. Subqueries
A subquery is a SELECT nested in another statement. Four places:
1. **Scalar subquery** (1 row, 1 column) used as a value:
   `SELECT id, total FROM orders WHERE total = (SELECT MAX(total) FROM orders)` (order 5, total 400). Returning 2+ rows is an error in most DBs (SQLite silently takes the first).
2. **IN / NOT IN** (a column of values): `WHERE id IN (SELECT emp_id FROM assignments ...)`.
3. **EXISTS / NOT EXISTS** (does any row exist?): boolean, the selected columns do not matter (`SELECT 1`).
4. **Derived table** in FROM: `SELECT ... FROM (SELECT dept_id, AVG(salary) a FROM employees GROUP BY dept_id) t JOIN ...` (needs an alias).

### Correlated subqueries
A subquery that references the outer row; conceptually re-evaluated per outer row.
```sql
SELECT id, customer_id, total FROM orders o
WHERE total > (SELECT AVG(total) FROM orders x WHERE x.customer_id = o.customer_id);
```
```
id | customer_id | total
1  | 1           | 250.0
3  | 2           | 300.0
5  | 3           | 400.0
```
If the correlation column were NULL for some row, `x.customer_id = NULL` would match nothing, the AVG would be NULL, and `total > NULL` is not true: that row silently drops out.
Optimizers often decorrelate these, but on a big table a window function (week 3: `AVG(total) OVER (PARTITION BY customer_id)`) or a join to a pre-aggregated derived table is usually better.

### IN vs EXISTS vs JOIN
- Semantically the same for positive checks; modern optimizers (Postgres, MySQL 8, SQLite) usually plan them alike.
- `EXISTS` can stop at the first match and is NULL-safe in the negative form. Prefer `NOT EXISTS` over `NOT IN`.
- `JOIN` can duplicate rows; use it when you need columns from the other table.
- `IN` with a literal list or a small subquery reads well.

## 9. Set operators (brief)
`UNION` (dedupes), `UNION ALL` (keeps duplicates, faster), `INTERSECT`, `EXCEPT` (Oracle: `MINUS`). Both queries must return the same number of compatible columns. `EXCEPT` is another way to write an anti-join on whole rows.

## Common mistakes
1. Forgetting the `ON` condition (accidental cross join).
2. Filtering the right table in `WHERE` after a LEFT JOIN (kills the unmatched rows).
3. `COUNT(*)` after a LEFT JOIN instead of `COUNT(right.col)`.
4. `NOT IN` when the subquery column can be NULL.
5. Join fan-out inflating `SUM`/`COUNT`; fixing it with `DISTINCT` instead of fixing the join.
6. Ambiguous column names (`id` in both tables): always prefix with the alias.
7. Joining on a nullable column and expecting NULLs to match.
8. Scalar subquery returning multiple rows.
9. `SELECT *` over a join returns duplicate column names; downstream code (e.g. a dict row factory) silently overwrites one.

## How interviewers probe this topic
- "Customers with no orders" in three ways, then "which do you prefer and why?" (NOT EXISTS; NOT IN NULL trap).
- "Employees who earn more than their manager" / "manager names" (self-join).
- "Departments with their headcount including empty ones" (LEFT JOIN + COUNT(col)).
- "Explain the difference between INNER, LEFT, RIGHT, FULL, CROSS" with Venn-diagram-free reasoning about rows.
- "What is the difference between `ON` and `WHERE` in a LEFT JOIN?"
- "What happens to row counts when you join two one-to-many tables?" (fan-out).
- "Correlated vs uncorrelated subquery? When would you rewrite it?" (window functions / join to aggregate).
- "How many rows come out of a join of table A (n rows) and B (m rows)?" Answer by relationship: between 0 and n*m depending on the key; 1:N never loses left rows in LEFT JOIN, never fewer than n.

## Your task
1. Run each example above in the REPL (use `schema.make_db()`).
2. Fill in `exercises.py` (21 functions) until the tests pass.
3. Do `interview-qa.md` aloud.
