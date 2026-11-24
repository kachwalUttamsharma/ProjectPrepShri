# Week 1 interview Q&A: filtering, NULL, aggregates

Try answering aloud first. Model answers are deliberately concise.

**1. What is the logical order of evaluation of a SELECT statement?**
FROM (and joins) -> WHERE -> GROUP BY -> HAVING -> SELECT list (window functions, aliases) -> DISTINCT -> ORDER BY -> LIMIT/OFFSET. That is why WHERE cannot reference aggregates, and why ORDER BY can use SELECT aliases.

**2. WHERE vs HAVING?**
WHERE filters individual rows before grouping and cannot use aggregates. HAVING filters groups after aggregation and can. Put non-aggregate conditions in WHERE: fewer rows to group, and indexes can be used.

**3. What does NULL mean and how does it behave in comparisons?**
Unknown/missing. Any comparison (`=`, `<>`, `<`) with NULL yields NULL, which WHERE treats as not-true, so the row is dropped. Use `IS NULL`, `IS NOT NULL`, or null-safe operators (`IS DISTINCT FROM` in Postgres, `<=>` in MySQL, `IS` in SQLite).

**4. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`?**
`COUNT(*)` counts rows. `COUNT(col)` counts rows where col is not NULL. `COUNT(DISTINCT col)` counts distinct non-NULL values.

**5. What happens with `x NOT IN (SELECT y ...)` if y contains a NULL?**
It returns no rows: `x <> NULL` is unknown for every x, so the whole predicate can never be TRUE. Use `NOT EXISTS`, or filter `WHERE y IS NOT NULL` inside the subquery.

**6. Does AVG include NULL rows? How would you treat NULL as zero?**
No, AVG and SUM skip NULLs, so the denominator is the non-NULL count. For missing=0 use `AVG(COALESCE(x, 0))`. Which is right is a business decision; state it.

**7. What does SUM return on an empty set?**
NULL, not 0. Use `COALESCE(SUM(x), 0)`. `COUNT` returns 0.

**8. Why does `SELECT dept, name, COUNT(*) FROM employees GROUP BY dept` behave differently across databases?**
`name` is neither grouped nor aggregated. Postgres (and MySQL with ONLY_FULL_GROUP_BY) reject it; SQLite returns an arbitrary row's value. Standard rule: every non-aggregated select column must appear in GROUP BY (or be functionally dependent on a grouped primary key, which Postgres allows).

**9. How do you get a deterministic result from `ORDER BY ... LIMIT`?**
Add a unique tie-breaker (e.g. `ORDER BY salary DESC, id`). Without it, ties may come back in any order and different runs can differ.

**10. How do NULLs sort?**
It is database specific: SQLite and MySQL treat NULL as smaller than any value (first in ASC). Postgres and Oracle treat it as larger (last in ASC). `NULLS FIRST/LAST` makes it explicit (Postgres, SQLite 3.30+; MySQL lacks it).

**11. Is `BETWEEN` inclusive? Any pitfall?**
Inclusive at both ends. For timestamps, `BETWEEN '2024-01-01' AND '2024-01-31'` excludes most of Jan 31; use `>= '2024-01-01' AND < '2024-02-01'` (half-open interval).

**12. What is `LIMIT/OFFSET` pagination's weakness?**
The DB must scan and discard OFFSET rows, so deep pages are slow, and concurrent inserts shift pages (duplicates/skips). Keyset pagination (`WHERE (created_at, id) < (:last_ts, :last_id) ORDER BY created_at DESC, id DESC LIMIT n`) is stable and uses an index.

**13. Does DISTINCT apply to one column or the whole row?**
The whole selected row. `SELECT DISTINCT(a), b` is the same as `SELECT DISTINCT a, b`.

**14. Difference between `DISTINCT` and `GROUP BY` without aggregates?**
Same result; both dedupe. GROUP BY is needed when you also aggregate; DISTINCT states intent more clearly. Optimizers often produce the same plan.

**15. Scenario: "Find the employees with no bonus." The table has bonus = 0 for some people and NULL for others. What do you ask/do?**
Clarify whether 0 and NULL mean the same. `WHERE bonus IS NULL` means "not recorded"; `bonus IS NULL OR bonus = 0` means "gets nothing". Asking this shows you understand NULL semantics.

**16. Scenario: monthly revenue for the last 3 months, but your boss says some orders have NULL amounts. What do you do?**
Filter or `COALESCE` depending on meaning, group by month (`strftime('%Y-%m', d)` in SQLite, `date_trunc('month', d)` in Postgres), and note that months with no orders are absent unless you join from a calendar table (week 3 recursive CTE).

**17. Scenario: "Top 3 highest paid." What edge cases do you raise?**
Ties at the boundary (LIMIT 3 cuts arbitrarily; use `DENSE_RANK() <= 3` if the intent is top 3 salary values), NULL salaries sorting first/last, and determinism.

**18. What does `WHERE a = 1 OR b = 2 AND c = 3` mean?**
`a = 1 OR (b = 2 AND c = 3)`, because AND binds tighter than OR. Always parenthesise mixed conditions.

**19. `LIKE '%abc'` vs `LIKE 'abc%'` and indexes?**
A prefix pattern (`'abc%'`) can use a B-tree index (with the right collation in some DBs); a leading wildcard cannot, forcing a scan. Full-text search or trigram indexes handle the rest.

**20. How do you avoid division by zero in `SUM(a) / SUM(b)`?**
`SUM(a) * 1.0 / NULLIF(SUM(b), 0)` returns NULL instead of an error (and avoids integer division).
