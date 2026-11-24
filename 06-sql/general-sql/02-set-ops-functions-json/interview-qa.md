# Part 02 interview Q&A: set operations, functions, pagination, JSON

Version-dependent claims: check current docs. Related: [lesson.md](lesson.md), week-01/03 Q&A for NULL and windows.

**1. UNION vs UNION ALL?**
UNION removes duplicate rows (needs a sort or hash over the combined result); UNION ALL just concatenates. Default to UNION ALL; use UNION only when dedup is required or the branches may overlap.

**2. What are the rules for combining queries with set operators?**
Same number of columns, positionally matched compatible types, column names taken from the first query, a single ORDER BY at the end that refers to output columns.

**3. INTERSECT and EXCEPT: how do they treat NULLs and duplicates?**
They compare whole rows and treat two NULLs as equal (not distinct), and return distinct rows. That differs from `=` and from `NOT IN`. Oracle calls EXCEPT MINUS; MySQL added both only in 8.0.31; INTERSECT/EXCEPT ALL exist in Postgres only (among the common ones).

**4. How would you find rows in A not in B in three ways?**
`EXCEPT`, `NOT EXISTS (correlated)`, and `LEFT JOIN ... WHERE b.key IS NULL`. Avoid `NOT IN (subquery)` if the subquery can return NULL: it yields no rows.

**5. How do you compare two columns when either can be NULL?**
`a IS NOT DISTINCT FROM b` (standard; Postgres, SQLite 3.39+, SQL Server 2022+), MySQL `a <=> b`, SQLite also `a IS b`. Fallback: `a = b OR (a IS NULL AND b IS NULL)`.

**6. COALESCE vs NULLIF vs IFNULL/ISNULL/NVL?**
COALESCE is standard, n-ary, returns the first non-NULL. IFNULL (MySQL/SQLite), ISNULL (SQL Server), NVL (Oracle) are two-argument vendor versions (ISNULL also takes the first argument's type, a trap). NULLIF(a,b) returns NULL when a=b; used for `x / NULLIF(y,0)` and turning sentinels like '' into NULL.

**7. Does AVG(COALESCE(x,0)) equal AVG(x)?**
No. AVG ignores NULLs; COALESCE turns them into zeros that are counted, lowering the average. Choose deliberately.

**8. Why is OFFSET pagination slow on deep pages?**
The engine must generate and discard the first N rows, so cost is O(offset + limit). It is also unstable under concurrent inserts/deletes (skips or duplicates) and needs a deterministic ORDER BY.

**9. Explain keyset pagination and its trade-offs.**
Return the last row's sort key(s) as a cursor and query `WHERE (k, id) > (:k, :id) ORDER BY k, id LIMIT n`. With a matching index it is an index seek: constant cost, stable under writes. Drawbacks: no random page jump, needs a unique total ordering (add id as tiebreaker), more complex with NULLs and mixed ASC/DESC, row-value comparison unsupported in SQL Server (expand into OR).

**10. What is LATERAL / CROSS APPLY and when use it?**
A subquery in FROM allowed to reference earlier FROM items, evaluated per outer row. Use for top-N per group (with LIMIT/TOP inside, can use an index), set-returning functions per row, and reusing computed values. LEFT JOIN LATERAL ... ON TRUE / OUTER APPLY keep outer rows with no match. Postgres, MySQL 8.0.14+, Oracle 12c+ have LATERAL; SQL Server has APPLY; SQLite has neither (use ROW_NUMBER).

**11. Top-N per group: options?**
ROW_NUMBER() over partition filtered to rn <= N (portable); LATERAL/APPLY with LIMIT (index friendly, small N); Postgres `DISTINCT ON` for N=1 (not run here, verify). Use RANK/DENSE_RANK if ties should be kept.

**12. How do you pivot rows to columns in SQL?**
Conditional aggregation: `SUM(CASE WHEN region='N' THEN qty END)` grouped by the row key; works everywhere. Native: SQL Server/Oracle/Snowflake `PIVOT`, Postgres `crosstab` or `FILTER`. Columns must be known at write time; truly dynamic pivots need dynamic SQL or should happen in the application/BI tool.

**13. How do you unpivot?**
`UNION ALL` of one SELECT per column, or `CROSS JOIN LATERAL (VALUES ...)` / `CROSS APPLY (VALUES ...)`, or native `UNPIVOT`. Needing it often hints at a denormalised design.

**14. json vs jsonb in Postgres?**
`json` stores the text verbatim (preserves whitespace, key order, duplicates), reparsed on each access; `jsonb` is a parsed binary format: slightly slower to write, much faster to query, supports GIN indexes, `@>`, `?`. Prefer `jsonb` unless you need exact text.

**15. How do you index JSON fields?**
Postgres: GIN on the jsonb column (containment/key-exists queries) or a btree on an expression like `((payload->>'user'))` for one hot key. MySQL: index a generated column or a functional index; multi-valued indexes for arrays (check docs). SQLite: index on an expression `json_extract(payload,'$.user')`, and queries must use the same expression.

**16. `->` vs `->>`?**
`->` returns JSON (strings quoted); `->>` returns text/SQL value. In MySQL `->` is `JSON_EXTRACT` and `->>` is `JSON_UNQUOTE(JSON_EXTRACT())`. Comparing `->` output to a plain string is a common bug.

**17. How do you turn a JSON array into rows?**
Postgres `jsonb_array_elements(_text)`, MySQL 8 `JSON_TABLE`, SQLite `json_each`, SQL Server `OPENJSON`, Snowflake `FLATTEN`. Empty arrays and NULLs yield no rows in an inner/cross join; use a LEFT JOIN to keep them.

**18. When should you NOT store data as JSON?**
When you need foreign keys, constraints, type safety, frequent filtering/joining/aggregating on the keys, or the shape is the same for every row. Use columns for the stable core and JSON for sparse extras.

**19. Why does `7/2` return 3 in some databases and 3.5 in others?**
Integer division in SQLite, Postgres, SQL Server (both operands integer); MySQL `/` returns a decimal and uses `DIV` for integer division. Cast one operand to numeric to be portable.

**20. LENGTH differences across dialects?**
MySQL `LENGTH` counts bytes (use `CHAR_LENGTH` for characters); SQL Server `LEN` ignores trailing spaces and `DATALENGTH` counts bytes; Postgres/SQLite `length` count characters (SQLite counts blobs in bytes).
