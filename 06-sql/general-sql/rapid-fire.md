# Rapid-fire: 20 mixed questions (parts 01-06)

Answer each in under 30 seconds out loud, then check. Non-SQLite facts: check current docs.

1. (01) Name the five SQL sub-languages. -- DDL, DML, DQL (often folded into DML), DCL (GRANT/REVOKE), TCL (COMMIT/ROLLBACK/SAVEPOINT).
2. (01) DELETE vs TRUNCATE? -- DELETE is row-by-row DML with WHERE, logged, fires row triggers. TRUNCATE empties the table quickly, no WHERE; transactional in Postgres, implicit commit in MySQL; resets identity depending on dialect.
3. (01) Upsert syntax in Postgres/SQLite vs MySQL? -- `INSERT ... ON CONFLICT (key) DO UPDATE SET ...` vs `INSERT ... ON DUPLICATE KEY UPDATE ...`; standard form is `MERGE`.
4. (01) What does `RETURNING` do and who supports it? -- Returns affected rows from INSERT/UPDATE/DELETE; Postgres, SQLite (3.35+); MariaDB for some; SQL Server uses `OUTPUT`; MySQL lacks it.
5. (02) UNION vs UNION ALL? -- UNION removes duplicates (sort/hash cost); UNION ALL keeps them and is faster.
6. (02) COALESCE vs NULLIF? -- COALESCE returns first non-NULL; NULLIF(a,b) returns NULL if a=b (classic: divide by NULLIF(x,0)).
7. (02) Why is OFFSET pagination slow on deep pages and what is the alternative? -- The engine reads and discards offset rows; use keyset: `WHERE (created_at,id) < (:last_created,:last_id) ORDER BY created_at DESC,id DESC LIMIT n`.
8. (02) What is LATERAL / CROSS APPLY? -- A join whose right side may reference columns of the left row (top-N per group, set-returning functions).
9. (02) Postgres JSON vs JSONB? -- JSON stores text as-is; JSONB is binary, indexable (GIN), no key order or duplicates.
10. (03) View vs materialized view? -- View is a stored query run every time; materialized view stores results and must be refreshed.
11. (03) Why prefer UUIDv7/bigint over random UUIDv4 as clustered PK in MySQL? -- Random keys cause page splits and poor locality in a clustered index; time-ordered ids append.
12. (03) What does `GRANT SELECT ON t TO role` do and what is row-level security? -- Grants privilege; RLS (Postgres policies) filters which rows a role can see/modify.
13. (04) Which is faster for a read-heavy range scan: B-tree or LSM, and write-heavy? -- B-tree good for reads and ranges; LSM favours high write throughput with compaction cost and read amplification.
14. (04) What does `EXPLAIN ANALYZE` add to `EXPLAIN` in Postgres? -- Actually executes the query and reports real times and row counts next to estimates; wrap writes in a transaction you roll back.
15. (04) Why might an index not be used? -- Function on the column, leading wildcard LIKE, type mismatch, low selectivity, stale statistics, wrong column order in composite index.
16. (04) Name the three join algorithms. -- Nested loop (good with index on inner), hash join (equality, big unsorted inputs), merge join (sorted inputs).
17. (05) Which anomaly does REPEATABLE READ in Postgres not stop? -- Write skew (SERIALIZABLE stops it). Postgres RR prevents phantoms by snapshot; MySQL RR uses next-key locks for locking reads.
18. (05) `SELECT ... FOR UPDATE SKIP LOCKED` is for? -- Job queues: workers claim different unlocked rows without waiting.
19. (05) How do you avoid a deadlock? -- Acquire locks in a consistent order, keep transactions short, retry on deadlock error.
20. (06) Why are PK/FK constraints "informational" in BigQuery/Snowflake and why does it matter? -- Not enforced, so duplicates and orphans can load; dedupe in the pipeline (ROW_NUMBER) and validate with tests.

Stretch: re-answer 13-17 using the part 04/05 lessons, with a concrete plan or table.
