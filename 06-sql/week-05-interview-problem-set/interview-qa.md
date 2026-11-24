# Week 5 interview Q&A: problem solving in SQL

**1. How do you approach an unfamiliar SQL problem in an interview?**
Clarify the grain of input and output, ask about NULLs, ties, duplicates and empty groups, sketch the output columns, build in named CTE steps, check row counts after joins, and test on a few rows. Say what you are doing as you go.

**2. RANK vs DENSE_RANK vs ROW_NUMBER?**
`ROW_NUMBER` gives unique numbers with arbitrary tie order. `RANK` gives ties the same number and skips after them (1,2,2,4). `DENSE_RANK` gives ties the same number without gaps (1,2,2,3). "Nth highest value" wants `DENSE_RANK`; "pick exactly one row per group" wants `ROW_NUMBER`.

**3. How do you find the Nth highest value if there may be fewer than N?**
Use `DENSE_RANK` in a subquery and filter, or a scalar subquery over `DISTINCT` values with `LIMIT 1 OFFSET N-1` wrapped so it yields NULL when missing. State what you return when it does not exist.

**4. How do you find duplicates, and how do you delete all but one?**
Find with `GROUP BY` on the identifying columns and `HAVING COUNT(*) > 1`. Delete by choosing which row survives (usually the lowest id) and removing the others, via a window rank or a `MIN(id)` per group. Always preview with a `SELECT` first.

**5. How do you get the top N rows per group?**
Rank within each partition using `ROW_NUMBER` or `DENSE_RANK` in a subquery, then filter on the rank. Choose by whether ties should be included. Without windows: a correlated count of better rows below N.

**6. What is the gaps and islands technique?**
Subtract a `ROW_NUMBER` from a sequential value. Within a consecutive run the difference is constant, so it labels the run. Group by it for start, end and length. Deduplicate first, and convert dates to day numbers.

**7. How do you compute sessions from event logs?**
Order events per user, use `LAG` for the time gap, flag rows that start a new session (no previous row, or gap over the timeout), then running-sum the flags to get a session id. Aggregate by user and session id.

**8. How do you compute a median in SQL?**
Number rows per group, count rows per group, keep the middle one (odd) or two (even) rows, and average. Some databases have `PERCENTILE_CONT`; SQLite and MySQL do not.

**9. How do you handle "did X for every Y"?**
Relational division: group by the entity, count distinct Ys it has, and compare to the total number of Ys. Alternatively a double `NOT EXISTS`. The count method is shorter; the double negation is more general.

**10. Running total vs rolling average. What are the pitfalls?**
The default window frame with `ORDER BY` is `RANGE`, which groups ties as peers. Use `ROWS` for physical rows. A rolling N-day average on data with missing days needs a calendar or a value-based frame. Decide how to treat the first days when the window is not full.

**11. How do you calculate month over month growth safely?**
Aggregate to months first, use `LAG` over the aggregated rows, guard divide by zero with `NULLIF`, return NULL for the first month, and avoid integer division.

**12. How do you build a retention metric?**
Pick the cohort (users by first activity date), define the return event and the offset (day 1, day 7), count cohort users with a return event, and divide by cohort size. Be explicit about the denominator and time zone.

**13. How do you build a funnel?**
Count distinct users per step. Decide if order matters (then compare timestamps) and whether a user must complete earlier steps. Report step to step and overall conversion.

**14. How do you pivot rows to columns?**
Conditional aggregation: one `SUM(CASE WHEN ...)` or `COUNT(CASE ...)` per output column grouped by the row key. For unknown column values you must generate the SQL dynamically.

**15. How do you compute percent of total?**
Divide by a window sum over the whole set (`SUM(x) OVER ()`) or over a partition for percent within group. Multiply by `100.0` to avoid integer division and round at the end.

**16. Self-join vs window function for comparing rows?**
Self-join when rows relate by a key (employee to manager). Window functions when the relation is order or partition (previous row, group average). Windows avoid a second scan and the fan-out risk.

**17. Your query is slow on a huge table. What do you check?**
`EXPLAIN` for scans and sorts, indexes on join and filter columns, whether a join multiplies rows, whether filtering can happen earlier, pre-aggregation or summary tables, and partitioning for time-series data.

**18. How do you test a query you cannot run on production data?**
Build a tiny fixture with a tie, a NULL, a duplicate, an empty group and a boundary date, work out the expected answer by hand, and compare. This is exactly what the tests in this repo do.

**19. What are the most common mistakes in interview SQL?**
Ignoring ties and NULLs, `NOT IN` with NULLs, filtering the outer table of a LEFT JOIN in `WHERE`, counting with `COUNT(*)` after an outer join, fan-out before aggregation, integer division, missing `ORDER BY`, and using window functions in `WHERE`.

**20. You finish early. What do you do?**
Offer the alternative technique, discuss complexity and indexes, point out edge cases the problem statement did not specify, and say what you would do with them in production.
