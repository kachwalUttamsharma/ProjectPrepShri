# Part 04 interview Q&A: how databases work

Back to [lesson](lesson.md). Postgres/MySQL specifics: check current docs for version details.

**1. What is a page and why does it matter?**
The fixed-size unit of disk/memory I/O (Postgres 8 KB, InnoDB 16 KB by default). Cost of a query is roughly pages touched, not rows. Hence locality, covering indexes, and caching matter.

**2. B-tree vs LSM tree?**
B-tree updates pages in place, gives stable read latency and good range scans; used by Postgres, InnoDB, SQLite. LSM buffers writes in memory, flushes sorted immutable files and compacts later: much higher write throughput, but read and write amplification via compaction (RocksDB, Cassandra).

**3. What is a WAL and why write it first?**
Write-ahead log: changes are logged sequentially and fsynced at commit before data pages are modified. Sequential log writes are cheap; data pages are flushed lazily. After a crash, replay the log. It also powers replication and PITR.

**4. What does a checkpoint do?**
Flushes dirty pages to data files and records a point from which recovery needs to start, bounding recovery time.

**5. Explain MVCC.**
Rows have multiple versions; each transaction reads a snapshot, so readers do not block writers and vice versa. Postgres stores new versions in the heap and needs VACUUM; InnoDB updates in place and reconstructs old versions from undo logs.

**6. Why does Postgres need VACUUM?**
Updates/deletes leave dead tuples; VACUUM marks the space reusable, updates the visibility map (enabling index-only scans), and prevents transaction-id wraparound. Long transactions block cleanup, causing bloat.

**7. Clustered vs heap tables?**
InnoDB's table is the PK B-tree; secondary indexes hold PK values (extra lookup, PK size inflates all indexes). Postgres uses a heap with all indexes pointing to tuple ids. Implication: choose short, mostly sequential PKs in InnoDB.

**8. How does a cost-based optimizer choose a plan?**
It enumerates access paths, join orders and algorithms, estimates cost using statistics (row counts, distinct values, histograms), and picks the lowest estimate. Bad estimates give bad plans.

**9. A query was fast yesterday and slow today. Causes?**
Stale statistics or data growth changing selectivity, plan flip, parameter-sensitive plan, bloat, lock waits, cache eviction, new missing index, a long transaction. Start with EXPLAIN (ANALYZE) and compare estimated vs actual rows.

**10. EXPLAIN vs EXPLAIN ANALYZE?**
EXPLAIN shows the plan and estimates without running. EXPLAIN ANALYZE executes it and shows actual time and rows (Postgres; MySQL 8.0.18+). Beware it really executes DML; use a rolled-back transaction.

**11. How do you read a Postgres plan?**
Inside-out (deepest node first), compare estimated rows with actual, remember actuals are per loop, check node types (Seq Scan, Index Scan, Bitmap, joins), `Rows Removed by Filter`, buffers hit vs read, and sort spill to disk.

**12. MySQL EXPLAIN `type` values?**
Best to worst: system/const, eq_ref, ref, range, index, ALL. `ALL` is a full table scan. `Extra` with `Using filesort`/`Using temporary` signals extra work; `Using index` means covering.

**13. When does the planner ignore an index?**
Low selectivity (most rows match), tiny table, predicate not sargable (function on column, implicit cast, leading wildcard), stale stats, wrong column order in a composite, or the index type does not support the operator.

**14. Composite index column order?**
Leftmost-prefix rule. Put equality columns first, then the range column, then ones serving ORDER BY; consider selectivity and which queries must be supported. `(a,b)` does not serve `WHERE b=?` efficiently.

**15. What is a covering index?**
An index containing all columns the query needs, so the table is never visited (`Index Only Scan`, `Using index`, `COVERING INDEX`). Postgres: `INCLUDE`; others add columns to the key.

**16. When use a partial or functional index?**
Partial: only a small hot subset is queried (`WHERE status='pending'`), saving space and write cost (not in MySQL). Functional: queries filter on an expression like `lower(email)`; the query must use the same expression.

**17. Postgres index types beyond B-tree?**
Hash (equality), GIN (JSONB, arrays, full-text, trigrams), GiST/SP-GiST (geometry, ranges, nearest neighbour), BRIN (huge, naturally ordered tables).

**18. Compare nested loop, hash and merge join.**
Nested loop: outer small plus index on inner key. Hash: build table on smaller side, great for large equality joins, memory-bound. Merge: both sides sorted, good for big sorted inputs. MySQL gained hash joins in 8.0.18 and has no merge join (check current docs).

**19. What is the N+1 problem and how do you fix it?**
One query for parents, then one per parent for children, so many round trips. Fix with a JOIN, batched `IN`/`ANY` loading (select-in eager loading), and an index on the FK. Detect with query counts and `pg_stat_statements`.

**20. Why is `OFFSET 100000` slow and what is the alternative?**
The database must produce and discard all skipped rows, so cost grows with offset. Use keyset pagination: `WHERE (sort_col, id) < (:last_sort, :last_id) ORDER BY sort_col DESC, id DESC LIMIT n`, backed by a matching index.

**21. Name five quick fixes for a slow query.**
Make predicates sargable, add/adjust composite or covering index, select fewer columns, keyset pagination, refresh statistics, eliminate N+1, rewrite correlated subquery or `NOT IN`, batch writes.
