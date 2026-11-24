# Week 2 interview Q&A: joins and subqueries

**1. Explain INNER, LEFT, RIGHT, FULL OUTER and CROSS joins.**
INNER: only rows with a match on both sides. LEFT: all left rows, right columns NULL when unmatched. RIGHT: mirror. FULL: unmatched rows from both sides. CROSS: Cartesian product (n x m), no condition.

**2. What is the difference between putting a condition in ON vs WHERE?**
For INNER joins nothing. For OUTER joins, ON decides which rows match (unmatched left rows survive with NULLs); WHERE filters the final result, so a condition on the right table discards the NULL-extended rows and effectively turns a LEFT JOIN into an INNER JOIN.

**3. Name the ways to express "rows with no match in another table".**
`NOT EXISTS` with a correlated subquery, a `LEFT JOIN` followed by a `IS NULL` test on the right table's key, or `NOT IN` (only if the subquery column can never be NULL). Which would you pick and why? `NOT EXISTS`.

**4. Why can `NOT IN (subquery)` return nothing?**
If the subquery yields any NULL, `x <> NULL` is unknown for every x, so the predicate is never true. `NOT EXISTS` has no such problem.

**5. EXISTS vs IN vs JOIN?**
All can express "has a match". EXISTS and IN do not duplicate left rows and are semi-joins; JOIN multiplies rows when the right side has several matches. Planners usually treat EXISTS and IN equivalently; NOT EXISTS is the safe negation. Use JOIN when you need right-side columns.

**6. What is a correlated subquery? Performance implications?**
A subquery referencing columns of the outer query, so it logically runs once per outer row. Can be O(n*m) without an index on the correlated column; often rewritten as a join to a pre-aggregated derived table or a window function.

**7. How do you model and query a hierarchy such as employee -> manager?**
Adjacency list: `manager_id` references the same table; one level via self-join; arbitrary depth via a recursive CTE (week 3).

**8. Self-join: list each unordered pair of rows that share an attribute once.**
Join the table to itself on the shared attribute and add an inequality on the key (`a.id < b.id`). The inequality removes (A,A) and the mirrored (B,A).

**9. What happens to the top of a hierarchy in a self-join on manager?**
The root has a NULL `manager_id`, so an inner join drops it; use a LEFT JOIN to keep it with a NULL manager. Any comparison between a row and its related row is then an ordinary `WHERE` over both aliases.

**10. Why does `COUNT(*)` after LEFT JOIN give 1 for an empty group?**
The unmatched left row is still one row (with NULLs on the right). Use `COUNT(right.pk)`, which ignores NULLs.

**11. What is join fan-out and how do you prevent it?**
Joining a parent to two independent child tables yields (children1 x children2) rows per parent, inflating SUM/COUNT. Pre-aggregate each child table to one row per parent in a subquery/CTE, then join; or use `COUNT(DISTINCT ...)` where valid (not for SUM).

**12. How many rows can A (n rows) JOIN B (m rows) return?**
INNER: 0 to n*m. LEFT: at least n. CROSS: exactly n*m. For a 1:N foreign key join with an inner join, at most the size of the N-side.

**13. What is a scalar subquery and what happens if it returns two rows?**
A subquery returning one row/one column, usable like a value. Two rows is an error in Postgres/MySQL; SQLite silently uses the first row, which hides bugs. Zero rows yields NULL.

**14. UNION vs UNION ALL?**
UNION removes duplicate rows (requires a sort/hash, slower); UNION ALL keeps all rows. Default to UNION ALL when duplicates are impossible or acceptable.

**15. How do you get rows present in A but not in B (whole row)?**
`EXCEPT` (or `MINUS` in Oracle), or `NOT EXISTS` for key-based comparison. EXCEPT treats NULLs as equal, which `NOT IN`/`=` do not.

**16. Scenario: "report units sold per product for all products, 0 for none."**
Start from the product table with a LEFT JOIN to the sales table, wrap the sum in `COALESCE(..., 0)`, and group by the product key. Filters on the sales table (e.g. a date range) must go in ON, not WHERE.

**17. Scenario: "list every entity with each period, even if nothing happened."**
CROSS JOIN the entities with a list of periods to build the grid, then LEFT JOIN the facts on (entity, period), COALESCE sums to 0.

**18. Scenario: you join orders to order_items and payments and your revenue doubled. Why?**
Fan-out: each order row is repeated for each (item, payment) pair. Aggregate items and payments separately per order first, then join.

**19. Can you join on a NULL key?**
`NULL = NULL` is unknown, so rows with NULL keys never match in an ordinary equi-join. Use a null-safe comparison (`IS`, `IS NOT DISTINCT FROM`, `<=>`) only when you mean it; usually it signals bad data.

**20. When would you use a derived table or CTE instead of a correlated subquery?**
When you need the aggregate for many rows at once (per-department average joined back), for readability, or when the planner does a poor job with the correlated form.
