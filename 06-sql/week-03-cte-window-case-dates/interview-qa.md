# Week 3 interview Q&A: CTEs, window functions, CASE, dates

**1. What is a CTE and why use one?**
A named subquery defined with WITH, scoped to one statement. Gains readability, reuse within the statement, and enables recursion. It is not materialised by default in modern Postgres (inlined); it is not an index or table.

**2. CTE vs subquery vs view vs temp table?**
Subquery/CTE: exist only inside the statement. View: stored query definition, re-run each time (a materialised view stores results). Temp table: stored rows for the session, can be indexed and reused across statements, good for expensive intermediate results.

**3. How does a recursive CTE work?**
An anchor query seeds the working set; the recursive member joins the previous iteration's rows back to the data; iteration stops when no new rows are produced; results are unioned. Needs a termination condition (a bound or finite data); on cyclic graphs track the path or use UNION to dedupe.

**4. Give uses of recursive CTEs.**
Org charts/category trees (descendants or ancestors), bill of materials, generating number/date series, graph reachability, parsing hierarchical paths.

**5. Difference between window functions and GROUP BY?**
GROUP BY collapses rows to one per group. A window function computes over a set of rows related to the current row but keeps every row. Windows are evaluated after WHERE/GROUP BY/HAVING and before ORDER BY/LIMIT.

**6. ROW_NUMBER vs RANK vs DENSE_RANK on the values 100, 90, 90, 80?**
ROW_NUMBER 1,2,3,4 (arbitrary among ties); RANK 1,2,2,4; DENSE_RANK 1,2,2,3.

**7. How do you get the second-highest salary? What about when there are ties or fewer than two distinct salaries?**
Rank the distinct values with `DENSE_RANK` (not `RANK`, not `ROW_NUMBER`) and keep rank 2. If there is no second value the result is empty; wrap it as a scalar subquery if the spec requires NULL. There is also a no-window alternative built from the maximum of the values below the maximum, which naturally returns NULL when absent.

**8. Top 3 earners per department, including ties?**
DENSE_RANK (or RANK) partitioned by dept ordered by salary DESC in a subquery, filter `<= 3`. Use ROW_NUMBER if you need exactly 3 rows per group. Ask which the interviewer wants.

**9. Why can't you use a window function in WHERE?**
WHERE is evaluated before windows are computed. Put the window in a subquery/CTE and filter in the outer query (or use QUALIFY where supported: Snowflake, BigQuery, Teradata, DuckDB).

**10. What does LAG do and what are its arguments?**
`LAG(expr, offset=1, default=NULL) OVER (PARTITION BY ... ORDER BY ...)` returns expr from the row `offset` rows earlier in the partition, or default when none exists. LEAD looks forward.

**11. How do you compute a running total? What is the default frame pitfall?**
`SUM(x) OVER (PARTITION BY g ORDER BY t)`. The default frame with ORDER BY is RANGE ... CURRENT ROW, so rows tying on t share the same running value. Add a unique tiebreaker or use `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.

**12. ROWS vs RANGE frames?**
ROWS counts physical rows relative to the current one; RANGE groups rows by value of the ORDER BY key (peers included, can use value offsets such as `RANGE BETWEEN INTERVAL '7 day' PRECEDING AND CURRENT ROW` in Postgres).

**13. What does LAST_VALUE return by default and why is it surprising?**
With the default frame it ends at the current row (including peers), so it often returns the current row's value. Specify `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` or use FIRST_VALUE with reversed ordering.

**14. Compute month-over-month growth percentage.**
Aggregate to monthly totals in a CTE, then use `LAG` over the aggregated rows to get the previous month, compute the change over the previous value as a percentage, protect the division with `NULLIF`, and use `100.0` to avoid integer division. First month is NULL by design. Mention months with no sales require a calendar join.

**15. How do you pivot rows into columns?**
Conditional aggregation: `SUM(CASE WHEN region='East' THEN amount END) AS east`, grouped by the row key. Columns must be known in advance (dynamic SQL otherwise). Postgres `crosstab`, SQL Server/Oracle `PIVOT` exist.

**16. How does CASE evaluate? What if no branch matches?**
Top to bottom; first true WHEN wins; no match and no ELSE gives NULL. Types of the branches must be compatible.

**17. How do you de-duplicate rows keeping the latest per key?**
`ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC, id DESC) = 1` in an outer filter. To delete duplicates, delete where the id is in the set of rn > 1.

**18. How do you find the number of days between two dates in SQLite, Postgres and MySQL?**
SQLite `julianday(b) - julianday(a)`; Postgres `b::date - a::date`; MySQL `DATEDIFF(b, a)`.

**19. Why is `BETWEEN` risky for timestamps and what do you use instead?**
It is inclusive of the upper bound at exact equality, so end-of-day values are missed or midnight values double counted across buckets. Use half-open ranges: `>= start AND < next_start`.

**20. Scenario: a report must show every day in March, even days with zero orders. How?**
Build a calendar (recursive CTE, `generate_series`, or a date dimension table), `LEFT JOIN` orders on the date, `COALESCE(COUNT(o.id), 0)` with the date filter in ON. Using COUNT(*) would report 1 for empty days.

**21. Scenario: the 7-day rolling average of daily active users.**
Aggregate to one row per day first (and fill missing days via a calendar), then an `AVG` window with a `ROWS` frame covering the current row and the 6 before it. Missing days with ROWS frames silently stretch the window, hence the calendar.

**22. Scenario: your window query is slow on 100M rows. What do you check?**
EXPLAIN; sort cost on PARTITION BY/ORDER BY columns (a composite index on (partition_cols, order_cols) can avoid the sort); reduce rows before the window via WHERE/pre-aggregation; avoid repeating identical OVER clauses with different sorts; consider materialising intermediate results.
