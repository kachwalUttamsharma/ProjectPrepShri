# Part 04: How databases work

Goal: know what happens between `SELECT` and rows coming back, so you can read a plan, pick an index, and explain slow queries.
Prerequisite: index basics and the SQLite plan introduction in [week-04 lesson](../../week-04-schema-indexes-transactions/lesson.md) (sections "Indexes" and "Reading plans"). This part goes deeper and covers Postgres/MySQL.

Legend: snippets marked **(run)** were executed here against `setup.sql` with SQLite 3.54. Snippets marked **(not run here, verify)** are Postgres/MySQL, where `psql`/`mysql` were not installed; plan output shown for them is **illustrative** and your numbers/format will differ. Version-dependent facts: check current docs.

Setup: `sqlite3 :memory:` then `.read setup.sql` (500 customers, 5000 orders, 15000 items, no secondary indexes).

## 1. Storage: pages and files
Databases do not read single rows from disk. Data lives in fixed-size **pages** (blocks): Postgres 8 KB by default, InnoDB 16 KB by default, SQLite 4 KB by default (check current docs; configurable). A page holds many rows. A query's cost is mostly "how many pages must I touch, and are they in memory".
- **Buffer pool / shared buffers**: RAM cache of pages. A cache hit costs microseconds; a miss costs a disk read (SSD ~100 us, spinning disk ~ms).
- **Heap vs clustered**: Postgres stores rows in an unordered **heap**; every index (including the PK) points to a heap location (TID). InnoDB (MySQL) stores the table *as* the primary-key B-tree (**clustered index**); secondary indexes store the PK value, so a secondary lookup does a second descent through the PK tree. SQL Server can choose one clustered index per table. SQLite stores rowid tables as a B-tree keyed by rowid.
- Consequence: wide random PKs (random UUID v4) in a clustered engine cause page splits and poor locality; time-ordered keys (UUIDv7, bigint sequences) insert at the right edge.

## 2. B-tree vs LSM
| | B-tree (Postgres, MySQL InnoDB, SQLite, SQL Server, Oracle) | LSM tree (RocksDB, Cassandra, ScyllaDB, LevelDB; MySQL via MyRocks) |
|---|---|---|
| Write path | Find page, modify in place (after WAL write); may split pages | Append to memtable + WAL, flush as immutable sorted files (SSTables) |
| Read path | Descend tree: O(log n) page reads, usually 3-4 levels | Check memtable, then several levels; bloom filters skip files |
| Write amplification | Moderate (page rewrites, WAL) | Compaction rewrites data repeatedly |
| Read amplification | Low | Higher (multiple files) |
| Range scans | Excellent (leaf pages linked, sorted) | Good, merge across files |
| Strength | Read-heavy and mixed OLTP, predictable latency | Very high write throughput, ingest, time-series |
A B-tree with fan-out of hundreds means 3-4 page reads find a row among hundreds of millions.

## 3. WAL (write-ahead log) and durability
Rule: **log the change before changing the data page**. On COMMIT the database fsyncs the WAL (sequential, cheap) rather than all dirty data pages (random, expensive). Dirty pages are written later by a background writer/checkpoint.
- Crash recovery: replay WAL from the last checkpoint (redo), roll back uncommitted work.
- Names: Postgres WAL; InnoDB redo log (plus undo log for rollback/MVCC) and binlog at the server layer; SQLite WAL mode (`PRAGMA journal_mode=WAL`) or rollback journal; SQL Server transaction log.
- The WAL is also the basis for replication and point-in-time recovery (see part 05).
- Durability knobs trade safety for speed: Postgres `synchronous_commit`, InnoDB `innodb_flush_log_at_trx_commit`, SQLite `PRAGMA synchronous`. Check current docs for defaults.

## 4. MVCC (multi-version concurrency control)
Readers should not block writers. Each row has versions; a transaction sees a **snapshot** of versions committed before it (or its statement) started.
- **Postgres**: an UPDATE writes a *new row version* into the heap and marks the old one dead (xmin/xmax transaction ids). Dead versions pile up until **VACUUM** reclaims them (autovacuum). Symptoms of neglect: table/index bloat, slow scans. Long-running transactions hold back cleanup.
- **MySQL InnoDB**: updates change the row in place; old versions are rebuilt from the **undo log**. A very long transaction makes the undo/history list grow.
- **SQLite**: single writer at a time; WAL mode lets readers proceed during a write.
- Writers still block writers on the same row (row locks). Isolation details: part 05.
Experiment **(run)** - snapshot reading in SQLite needs two connections, so try it in two terminals with a file DB and `PRAGMA journal_mode=WAL;`.

## 5. What the planner does
Pipeline: parse -> rewrite (views expanded) -> **plan/optimize** -> execute. The optimizer is **cost-based**: it enumerates plans (access paths, join order, join algorithm), estimates cost from **statistics**, and picks the cheapest estimate.
- **Statistics**: row counts, distinct counts, value histograms, most-common values, correlation. Postgres: `ANALYZE` (autovacuum runs it), view `pg_stats`, `default_statistics_target`, extended stats via `CREATE STATISTICS` for correlated columns. MySQL: `ANALYZE TABLE`, persistent stats, optional histograms (8.0+; check current docs). SQLite: `ANALYZE` fills `sqlite_stat1`.
- **Selectivity**: fraction of rows a predicate matches. Low selectivity (matches most rows) -> scanning beats an index. The planner can pick a sequential scan on purpose even when an index exists.
- Bad plans usually come from bad estimates: stale stats, correlated columns, skewed values, functions/casts hiding columns, parameters (generic plans; check current docs on `plan_cache_mode`).
- Hints exist in MySQL (`USE INDEX`, optimizer hints) and SQL Server; Postgres core has none (extensions like pg_hint_plan). Prefer fixing stats/indexes first.

## 6. Reading EXPLAIN
### SQLite (run)
```
sqlite> EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 42;
`--SCAN orders
sqlite> CREATE INDEX idx_orders_customer ON orders(customer_id);
sqlite> EXPLAIN QUERY PLAN SELECT * FROM orders WHERE customer_id = 42;
`--SEARCH orders USING INDEX idx_orders_customer (customer_id=?)
```
Vocabulary: `SCAN` = read whole table (or whole index); `SEARCH ... (col=?)` = B-tree lookup; `COVERING INDEX` = answered from the index alone; `USE TEMP B-TREE FOR ORDER BY` = an explicit sort.

### Postgres (not run here, verify; illustrative output)
`EXPLAIN` shows the chosen plan with estimates only. `EXPLAIN (ANALYZE, BUFFERS)` **executes the query** (wrap writes in a transaction you roll back) and adds actuals.
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders WHERE customer_id = 42;
```
```
-- illustrative, not run here
Index Scan using idx_orders_customer on orders  (cost=0.28..12.5 rows=10 width=40)
                                                (actual time=0.03..0.05 rows=10 loops=1)
  Index Cond: (customer_id = 42)
  Buffers: shared hit=4
Planning Time: 0.1 ms
Execution Time: 0.08 ms
```
How to read:
- Read the tree **inside-out**: the most indented node runs first and feeds its parent.
- `cost=startup..total` is in arbitrary planner units, not milliseconds. `rows` is the *estimate*; `actual rows` is reality. **A large gap between them (10x+) is the first thing to look for**: it means stale or insufficient stats.
- `loops=N`: actual time and rows are **per loop**; multiply for totals (key for nested loops).
- Node types: `Seq Scan`, `Index Scan`, `Index Only Scan` (needs visibility map; vacuum helps), `Bitmap Heap Scan` + `Bitmap Index Scan` (many matches, sort heap visits), `Nested Loop`, `Hash Join`, `Merge Join`, `Sort`, `HashAggregate`, `Gather` (parallel).
- `Rows Removed by Filter: 99000` on a Seq Scan means a lot of wasted reads -> index candidate.
- `Buffers: shared hit` (cache) vs `read` (disk). `Sort Method: external merge Disk:` means `work_mem` too small for that sort.

### MySQL (not run here, verify; illustrative output)
```sql
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 42;   -- 8.0.18+, executes; check current docs
```
```
-- illustrative, not run here
+----+-------------+--------+------+---------------------+---------------------+---------+-------+------+-------+
| id | select_type | table  | type | possible_keys       | key                 | key_len | ref   | rows | Extra |
| 1  | SIMPLE      | orders | ref  | idx_orders_customer | idx_orders_customer | 4       | const | 10   | NULL  |
```
Key columns: `type` from best to worst: `system/const` > `eq_ref` > `ref` > `range` > `index` (full index scan) > `ALL` (full table scan). `key` = index actually chosen; `rows` = estimate; `Extra`: `Using index` (covering), `Using filesort` (explicit sort, may not touch disk despite the name), `Using temporary`, `Using where`, `Using index condition`. `EXPLAIN FORMAT=TREE` / `EXPLAIN ANALYZE` give a tree like Postgres.

## 7. Index types
(Index basics: week-04.) Beyond a plain B-tree:
| Type | Where | Good for | Notes |
|---|---|---|---|
| B-tree | all | `=`, ranges, `ORDER BY`, prefix `LIKE 'abc%'` | default everywhere |
| Hash | Postgres (`USING hash`), MySQL MEMORY/NDB, InnoDB adaptive hash (internal) | equality only | no range/sort; crash-safe in Postgres since 10 |
| GIN | Postgres | many keys per row: JSONB `@>`, arrays, full text `tsvector`, trigram `pg_trgm` for `LIKE '%x%'` | slower writes, fast contains-queries |
| GiST / SP-GiST | Postgres | geometry (PostGIS), ranges, nearest-neighbour, exclusion constraints | |
| BRIN | Postgres | huge naturally-ordered tables (timestamps in append-only logs) | tiny, coarse |
| Full-text / Spatial | MySQL `FULLTEXT`, `SPATIAL` | text search, geo | |
| Composite | all | multi-column predicates | **leftmost-prefix rule**: `(a,b,c)` serves `a`, `a,b`, `a,b,c`; not `b` alone. Equality columns first, then range, order matches `ORDER BY` |
| Covering | Postgres `INCLUDE (cols)`; SQL Server `INCLUDE`; MySQL/SQLite: put columns in the key | avoid table visits | |
| Partial (filtered) | Postgres, SQLite, SQL Server; **not MySQL** | index only the rows you query (`WHERE status='pending'`) | small and fast |
| Functional / expression | Postgres, SQLite, MySQL 8.0.13+ | `WHERE lower(email)=...` | query expression must match exactly |
| Unique | all | enforce + lookup | |

Verified in SQLite **(run)**:
```
-- covering: composite index contains everything the query needs
CREATE INDEX idx_orders_cust_total ON orders(customer_id, total_cents);
EXPLAIN QUERY PLAN SELECT SUM(total_cents) FROM orders WHERE customer_id = 42;
`--SEARCH orders USING COVERING INDEX idx_orders_cust_total (customer_id=?)

-- functional index
EXPLAIN QUERY PLAN SELECT * FROM customers WHERE lower(email) = 'user7@example.com';
`--SCAN customers
CREATE INDEX idx_cust_lower_email ON customers(lower(email));
`--SEARCH customers USING INDEX idx_cust_lower_email (<expr>=?)

-- partial index (on a fresh DB with only this index)
CREATE INDEX ip ON orders(created_at) WHERE status='pending';
EXPLAIN QUERY PLAN SELECT id FROM orders WHERE status='pending' AND created_at > '2024-12-01';
`--SEARCH orders USING COVERING INDEX ip (created_at>?)

-- ORDER BY ... LIMIT served by index order: no sort
before:  |--SCAN orders
         `--USE TEMP B-TREE FOR ORDER BY
after CREATE INDEX i1 ON orders(created_at):
         `--SCAN orders USING COVERING INDEX i1
```
Leading-wildcard `LIKE '%99@example.com'` cannot use a B-tree (it scans). In Postgres use `pg_trgm` + GIN; in MySQL use FULLTEXT or reverse-string tricks.

Index costs: every index slows INSERT/UPDATE/DELETE, uses disk/RAM, and may be unused. Find unused ones (`pg_stat_user_indexes.idx_scan`, MySQL `sys.schema_unused_indexes`; not run here, verify).

## 8. Join algorithms
| Algorithm | How | Best when | Needs |
|---|---|---|---|
| Nested loop | for each outer row, probe inner | outer small, inner indexed on join key | index on inner join column |
| Hash join | build hash table on smaller input, probe with the other | large unsorted inputs, equality joins | memory (`work_mem` / `join_buffer_size`) |
| Merge (sort-merge) join | sort both on key, walk together | both inputs already sorted (index order) or huge; also handles ranges | sort or ordered indexes |
Postgres has all three. MySQL used nested loop (with block-nested-loop) historically and added hash join in 8.0.18 (check current docs); no merge join. SQLite uses nested loops (sometimes with an automatic index or Bloom filter).
SQLite **(run)** - join with no index on `orders.customer_id`, then with it:
```
|--SCAN o
|--BLOOM FILTER ON c (id=?)
`--SEARCH c USING INTEGER PRIMARY KEY (rowid=?)
-- after CREATE INDEX io ON orders(customer_id):
|--SCAN c
`--SEARCH o USING INDEX io (customer_id=?)
```
Notice the planner flipped join order: it starts from the filtered table (`c.country='US'`) and probes the indexed side. Join order is the planner's decision, not the order you wrote (for inner joins).

## 9. N+1 queries
Pattern: 1 query fetches N parents, then N queries fetch children one by one (typical ORM lazy loading).
```python
orders = db.execute("SELECT id FROM orders WHERE customer_id=42").fetchall()   # 1
for (oid,) in orders:
    db.execute("SELECT * FROM order_items WHERE order_id=?", (oid,))             # N
```
Each query is fast, yet network round trips (~0.2-2 ms each) dominate: 10,000 parents = 10,000 trips. Fixes:
1. **JOIN** (one query, aggregate or flatten): `SELECT o.id, COUNT(i.id) FROM orders o LEFT JOIN order_items i ON i.order_id=o.id WHERE o.customer_id=42 GROUP BY o.id;`
2. **Batch**: `WHERE order_id IN (...)` / `= ANY(array)` (2 queries total; ORM "eager/select-in loading").
3. Ensure an index on the FK (`order_items.order_id`) - databases other than MySQL InnoDB do not create FK indexes automatically (InnoDB does).
Detect: query logs showing identical statements differing only in a parameter; ORM query counters; `pg_stat_statements` with huge `calls`.

## 10. Common slow-query fixes (checklist)
1. `EXPLAIN` first; compare estimated vs actual rows.
2. **Sargable predicates**: don't wrap the column. `WHERE date(created_at)='2024-06-01'` -> `WHERE created_at >= '2024-06-01' AND created_at < '2024-06-02'`. `WHERE col+1=5` -> `col=4`. Implicit casts (comparing varchar column to number) can disable indexes.
3. Add/adjust composite index to match filter + sort (equality cols, then range, then order).
4. Select only needed columns; enable covering indexes.
5. `OFFSET 100000` is O(offset): use **keyset pagination** (`WHERE (created_at,id) < (?,?) ORDER BY created_at DESC,id DESC LIMIT 10`; row-value syntax works in SQLite, Postgres, MySQL).
6. `SELECT COUNT(*)` on huge tables is a scan (MVCC); use estimates or counters when exact is not needed.
7. `OR` across different columns and `NOT IN` with NULLs hurt; use `UNION ALL` / `NOT EXISTS`.
8. Correlated subqueries -> joins or window functions (planners often, not always, decorrelate).
9. Refresh stats (`ANALYZE`), vacuum/bloat, enough memory (`work_mem`, buffer pool).
10. Stop N+1; batch writes (multi-row INSERT, `COPY`/`LOAD DATA`) and wrap in one transaction.
11. Find the real offenders first: Postgres `pg_stat_statements`, MySQL slow query log / `performance_schema`, `auto_explain` (check current docs).
12. Still slow: denormalise, materialized view, cache, partition, or read replica (parts 03, 05, 06).

## Common mistakes
- Adding an index for every column "just in case".
- Trusting `EXPLAIN` without `ANALYZE` on estimates that are wrong.
- Reading `EXPLAIN ANALYZE` of an `UPDATE`/`DELETE` and forgetting it really ran.
- Assuming a seq scan is always bad (small tables, or low-selectivity predicates, it is right).
- Testing on tiny data: plans change with row counts.

## Your task
`practice.sql` after `.read setup.sql`. Solutions are kept outside the repo; attempt first, then compare with your own plan output.
