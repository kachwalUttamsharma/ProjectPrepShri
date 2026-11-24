# SQL Week 4: Schema design, indexes, transactions

Goal: design tables that stay correct, make queries fast with the right index, and explain transactions, isolation and trade-offs like an engineer who ships to production. Much of this week is *conceptual*: interviews for backend/forward-deployed roles ask "why", not just "how".
Budget: ~3 h reading + running the demos, ~2.5 h exercises, ~1.5 h interview Q&A.
Run tests: `.venv/bin/pytest 06-sql/week-04-schema-indexes-transactions -v`

SQLite vs Postgres vs MySQL notes appear as **[PG]**, **[MySQL]**, **[SQLite]** tags. Learn the concepts on SQLite; know where the big engines differ.

## 1. Modelling: tables, keys, relationships
- **Primary key (PK):** uniquely identifies a row, NOT NULL. **Surrogate key** = meaningless generated id (`INTEGER PRIMARY KEY` in SQLite, `BIGINT GENERATED ... AS IDENTITY` or `uuid` in PG, `AUTO_INCREMENT` in MySQL). **Natural key** = real-world attribute (email, ISBN). Common practice: surrogate PK plus a UNIQUE constraint on the natural key (emails change; ids should not).
- **Foreign key (FK):** column referencing another table's key; guarantees *referential integrity*. `ON DELETE CASCADE | SET NULL | RESTRICT | NO ACTION`. **[SQLite]** FKs are OFF per connection until `PRAGMA foreign_keys = ON`.
- **Candidate key / composite key / unique constraint:** any minimal column set that identifies a row; a table has one PK but many UNIQUE constraints.
- **Relationships:** 1:1 (FK with UNIQUE), 1:N (FK on the many side), M:N (junction table with composite PK, e.g. `enrollments(student_id, course_id)`).
- Data types: money -> integer cents or `NUMERIC/DECIMAL`, never float. Timestamps in UTC. **[SQLite]** uses *type affinity*: an INTEGER column happily stores `'abc'` as text unless the table is `STRICT`:
```
CREATE TABLE a(n INTEGER); INSERT INTO a VALUES ('abc'),('12');  ->  [('abc','text'), (12,'integer')]
CREATE TABLE s(n INTEGER) STRICT; INSERT INTO s VALUES ('abc')   ->  IntegrityError: cannot store TEXT value in INTEGER column s.n
```

## 2. Constraints: let the database defend the data
```sql
CREATE TABLE members (
  id     INTEGER PRIMARY KEY,
  handle TEXT NOT NULL UNIQUE,
  city   TEXT NOT NULL,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5)   -- NULL passes CHECK (unknown is not false)
);
CREATE TABLE loans (
  id        INTEGER PRIMARY KEY,
  member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
  fee       REAL NOT NULL CHECK (fee >= 0),
  state     TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','returned','lost')),
  loaned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```
`NOT NULL`, `UNIQUE`, `CHECK`, `DEFAULT`, `PRIMARY KEY`, `FOREIGN KEY`. Application-level validation is not enough: races between two requests break "check then insert"; a UNIQUE constraint cannot be raced. A UNIQUE column allows multiple NULLs in SQLite/PG/MySQL (SQL Server allows one).
Violations raise `sqlite3.IntegrityError` in Python; catch it and report conflict instead of pre-checking.
**Partial unique index:** "at most one open loan per book" = `CREATE UNIQUE INDEX uq ON loans(book_id) WHERE state = 'open'` (SQLite and PG; MySQL lacks partial indexes).

## 3. Normalization
Goal: one fact stored in one place, to avoid *update, insert and delete anomalies*.
Start from a flat table `flat_enrollments(student_name, student_email, course_title, grade)`: a student's email is repeated on every enrollment; changing it means updating many rows (miss one and the data disagrees).
- **1NF:** atomic values (no lists in a cell, no repeating column groups like `phone1, phone2`), each row unique.
- **2NF:** (1NF +) no non-key column depends on only *part* of a composite key. Matters only with composite keys: in `order_items(order_id, product_id, product_name, qty)`, `product_name` depends only on `product_id`, so move it to `products`.
- **3NF:** (2NF +) no non-key column depends on another non-key column (transitive): `employees(id, dept_id, dept_name)` -> `dept_name` depends on `dept_id`; split `departments`. Slogan: "every non-key attribute depends on the key, the whole key and nothing but the key".
- **BCNF:** every determinant is a candidate key (a slightly stricter 3NF).
Result for the example: `students(id, name, email UNIQUE)`, `courses(id, title UNIQUE)`, `enrollments(student_id, course_id, grade, PRIMARY KEY (student_id, course_id))`. A snapshot such as a price at purchase time is a *historical fact*, not a duplicate of the current price, so it stays on the line item.
```sql
CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL UNIQUE);
INSERT INTO courses (title) SELECT DISTINCT course_title FROM flat_enrollments;
```
**Denormalization** is a deliberate trade for read speed: precomputed counters, copied columns, summary tables, star schemas in warehouses. Costs: extra writes and a risk of inconsistency. Normalise first, denormalise with a measured reason.

## 4. Indexes
An index is a separate sorted structure (almost always a **B-tree**; leaf entries point to rows) that lets the database *seek* instead of scanning every row. Lookup O(log n) instead of O(n); range scans and ORDER BY on the indexed order are cheap.
```sql
CREATE INDEX idx_cust ON requests(customer_id);
```
Sample plans on a 3000-row `requests(id, customer_id, status, created_at, body)` table (`EXPLAIN QUERY PLAN`):
```
SELECT * FROM requests WHERE customer_id = 5
  before:  SCAN requests
  after:   SEARCH requests USING INDEX idx_cust (customer_id=?)
SELECT * FROM requests WHERE id = 10
           SEARCH requests USING INTEGER PRIMARY KEY (rowid=?)
```
Key ideas:
- **Clustered vs secondary.** In InnoDB (MySQL) the table *is* the PK B-tree (clustered); secondary indexes store the PK and need a second lookup. In SQLite a rowid table is a B-tree keyed on rowid, and `INTEGER PRIMARY KEY` aliases it. In PG the table is a heap and every index is secondary (extra heap fetch, avoided with index-only scans).
- **Composite index, leftmost prefix rule.** Index `(customer_id, created_at)` helps filters on `customer_id` and on `customer_id AND created_at`, **not** on `created_at` alone. Order columns: equality columns first, then the range/sort column. With only `idx(user_id)` the query below needs a sort; with the composite it does not:
```
SELECT id FROM requests WHERE customer_id = 5 AND created_at >= '2024-01-05' ORDER BY created_at
  idx(customer_id):              SEARCH requests USING INDEX idx_cust (customer_id=?)
                                 USE TEMP B-TREE FOR ORDER BY
  idx(customer_id, created_at):  SEARCH requests USING COVERING INDEX idx_cust_ts (customer_id=? AND created_at>?)
```
- **Covering index.** If the index contains every column the query needs, the table is never touched (`COVERING INDEX`; PG "Index Only Scan", MySQL "Using index"):
```
SELECT status, created_at FROM requests WHERE customer_id = 7
  idx(customer_id):                      SEARCH requests USING INDEX idx_cust (customer_id=?)
  idx(customer_id, status, created_at):  SEARCH requests USING COVERING INDEX idx_cov (customer_id=?)
```
  [PG] `CREATE INDEX ... INCLUDE (col)` adds payload columns without making them part of the key.
- **Selectivity/cardinality.** Indexes pay off when the predicate filters out most rows. An index on a boolean flag (50/50) is rarely used; the planner may prefer a scan. Partial indexes (`WHERE active = 1`) fix skewed data.
- **When an index is NOT used:** function on the column (`WHERE substr(created_at,1,7) = '2024-01'` -> SCAN; use a range or an *expression index* `CREATE INDEX ... ON requests(substr(created_at,1,7))`), leading wildcard `LIKE '%x'`, type mismatch/implicit casts, `OR` across columns, non-leftmost composite column, small tables, low selectivity, stale statistics (`ANALYZE`).
- **Cost.** Every INSERT/UPDATE/DELETE must maintain every index: more indexes = slower writes and more disk. Index for your real query patterns; drop unused ones. UNIQUE and PK constraints create indexes automatically. **FK columns are not auto-indexed in PG/SQLite** (MySQL does): index them or joins and cascading deletes scan.
- **Other index types.** Hash (equality only), GIN/GiST (PG: arrays, JSONB, full text, geometry), full-text, bitmap (warehouses), LSM trees (RocksDB/Cassandra: write-optimised alternatives to B-trees).

### Reading plans
- **[SQLite]** `EXPLAIN QUERY PLAN <query>`: look for `SCAN` (full) vs `SEARCH ... USING INDEX`, `USE TEMP B-TREE FOR ORDER BY` (extra sort).
- **[PG]** `EXPLAIN (ANALYZE, BUFFERS) <query>`: Seq Scan vs Index Scan / Index Only Scan / Bitmap Heap Scan; join types Nested Loop / Hash Join / Merge Join; compare estimated vs actual rows (bad estimates = stale stats).
- **[MySQL]** `EXPLAIN` / `EXPLAIN ANALYZE`: `type` (ALL = full scan, ref, range, const), `key`, `rows`, `Extra` (Using filesort, Using temporary, Using index).
- Process: measure, read the plan, add/adjust one index, re-check, confirm with real timings.
- Two classic app-level problems: **N+1 queries** (one query for the list, then one per row: replace with a join or `IN (...)`), and **`SELECT *`** defeating covering indexes.

## 5. Transactions and ACID
A transaction groups statements into one all-or-nothing unit.
```sql
BEGIN;
INSERT INTO purchases (item_id, qty) VALUES (7, 2);
UPDATE items SET on_hand = on_hand - 2 WHERE id = 7;
COMMIT;            -- or ROLLBACK; to undo both
```
- **Atomicity:** all or nothing (a crash between the two statements leaves neither applied; implemented with undo logs / WAL).
- **Consistency:** a transaction moves the DB from one valid state to another; constraints hold at commit (consistency is partly the *application's* job: CHECKs, FKs, invariants).
- **Isolation:** concurrent transactions do not see each other's partial work (degree depends on level).
- **Durability:** once COMMIT returns, the data survives crashes (write-ahead log fsync'd; `synchronous` settings trade this for speed).
Demo of atomic rollback and visibility (SQLite file DB, two connections):
```
A: BEGIN IMMEDIATE; INSERT INTO t VALUES (1);
B: INSERT INTO t VALUES (2)        -> OperationalError: database is locked   (one writer at a time)
B: SELECT COUNT(*) FROM t          -> 0   (B does not see A's uncommitted row)
A: COMMIT;   B: SELECT COUNT(*)    -> 1
A: BEGIN; DELETE FROM t; (count inside = 0); ROLLBACK; (count after = 1)
```
**Savepoints** give partial rollback inside a transaction (`SAVEPOINT s1; ... ROLLBACK TO s1;`); ORMs use them for nested transactions.
In Python: with `sqlite3` use `with conn:` (commit on success, rollback on exception); with SQLAlchemy `with engine.begin() as conn:`. Keep transactions short: long ones hold locks, bloat undo/MVCC history, and block vacuum.
Idempotency/upserts: `INSERT INTO page_views(url, hits) VALUES (:url, 1) ON CONFLICT(url) DO UPDATE SET hits = hits + 1` (PG and SQLite; MySQL `ON DUPLICATE KEY UPDATE`). `ON CONFLICT DO NOTHING` makes retries safe.

## 6. Isolation levels and anomalies
Anomalies:
- **Dirty read:** reading another transaction's uncommitted data.
- **Non-repeatable read:** same row read twice in one transaction gives different values (someone committed an UPDATE between).
- **Phantom read:** same range query returns different *sets* of rows (someone committed an INSERT/DELETE).
- **Lost update:** two transactions read a value, both write; one overwrite is lost (`read balance; balance+10; write`).
- **Write skew:** two transactions read overlapping data, each updates a *different* row, jointly breaking an invariant (two on-call doctors both go off-call because each saw the other still on).

| Level (SQL standard) | Dirty read | Non-repeatable | Phantom |
|---|---|---|---|
| READ UNCOMMITTED | possible | possible | possible |
| READ COMMITTED | no | possible | possible |
| REPEATABLE READ | no | no | possible (but not in PG or MySQL InnoDB snapshots, mostly) |
| SERIALIZABLE | no | no | no |

Reality check:
- **[PG]** default READ COMMITTED; implements MVCC (each statement sees a snapshot of committed data). REPEATABLE READ = snapshot isolation for the whole transaction (no phantoms, but write skew possible). SERIALIZABLE uses SSI and may abort with a serialization failure: **retry the transaction**. READ UNCOMMITTED behaves as READ COMMITTED.
- **[MySQL InnoDB]** default REPEATABLE READ with MVCC + gap/next-key locks to limit phantoms; `SELECT ... FOR UPDATE` reads latest committed data and locks.
- **[SQLite]** effectively SERIALIZABLE: a single writer at a time. In WAL mode readers do not block the writer and the writer does not block readers (readers see a snapshot). Great for embedded/single-node use, not for high write concurrency.
**MVCC** keeps multiple versions of rows so readers do not block writers; old versions are cleaned up (PG VACUUM, InnoDB purge).

### Preventing lost updates
1. Atomic statement: `UPDATE accounts SET balance = balance + 10 WHERE id = 1` (no read-modify-write in the app).
2. Pessimistic lock: `SELECT ... FOR UPDATE` [PG/MySQL] (SQLite: `BEGIN IMMEDIATE`).
3. **Optimistic locking:** version column; `UPDATE documents SET body = :body, rev = rev + 1 WHERE id = :id AND rev = :rev`; rowcount 0 means someone else won, so re-read and retry.
4. Higher isolation level + retry on failure.
5. Unique constraints for "at most one" rules (race-proof).

### Deadlocks
T1 locks row A then wants B; T2 locks B then wants A: each waits forever. Databases detect cycles (PG after `deadlock_timeout`; InnoDB immediately) and abort one victim (error 40P01 / 1213): **the app must retry**. Prevent by: acquiring locks in a consistent order (always lower id first), keeping transactions short, touching fewer rows, indexing the columns used in locking reads/updates (so fewer rows are locked), lower isolation where safe. Diagnose with `pg_locks`/`pg_stat_activity` [PG], `SHOW ENGINE INNODB STATUS` [MySQL].

## 7. SQL vs NoSQL, OLTP vs OLAP
**SQL (relational):** schema, joins, ACID, strong consistency, ad-hoc queries; scales up well and out with read replicas/sharding at effort. **NoSQL** families: key-value (Redis, DynamoDB), document (MongoDB), wide-column (Cassandra), graph (Neo4j). Choose them for: massive write scale/horizontal partitioning, flexible/evolving schemas, simple access by key, very low latency, specific data shapes (graphs, time series). Cost: weaker/no joins, eventual consistency (CAP/PACELC trade-offs), you model data around your queries, transactions are limited or per-item. Modern relational DBs also do JSON (`JSONB` in PG). Default answer: start with Postgres unless you can name the requirement it fails.
**OLTP** (online transaction processing): many small reads/writes, point lookups, row-oriented storage, normalised schema, B-tree indexes, ACID, latency in ms (Postgres, MySQL). **OLAP** (analytics): few huge scans/aggregations over history, **column-oriented** storage (reads only needed columns, compresses well), denormalised star schema (fact table + dimension tables), batch/ELT loads (BigQuery, Snowflake, Redshift, ClickHouse, DuckDB). Pipeline: OLTP -> CDC/ETL -> warehouse. Do not run heavy reports on the primary OLTP database; use a replica or warehouse.

## 8. Other practical topics
- **Views:** stored named query (`CREATE VIEW dept_payroll AS SELECT dept, SUM(salary) AS payroll FROM staff GROUP BY dept`), always up to date; **materialized views** [PG] store results and must be refreshed.
- **Migrations:** schema changes versioned in code (Alembic, Flyway). `ALTER TABLE ADD COLUMN archived INTEGER NOT NULL DEFAULT 0` is cheap in SQLite and modern PG (11+); on big tables avoid long locks: add nullable column, backfill in batches, then add the constraint. **[SQLite]** cannot drop/alter most column constraints in place (rebuild the table).
- **Connection pooling:** opening connections is expensive; apps use a pool (PgBouncer, SQLAlchemy pool). Pool size x app instances must stay below the DB's max connections.
- **Replication & scaling:** read replicas (replication lag = stale reads), partitioning (split a table by range/hash), sharding (split across servers; cross-shard joins/transactions are hard).
- **Backups:** logical dumps vs physical + WAL archiving (point-in-time recovery).
- **SQL injection:** never format values into SQL; use parameters (`conn.execute("... WHERE id = ?", (x,))` or `:name`). Identifiers cannot be parameterised: whitelist them.

## SQLite vs Postgres vs MySQL cheat table
| Topic | SQLite | Postgres | MySQL (InnoDB) |
|---|---|---|---|
| Typing | dynamic (affinity), STRICT optional | strict | strict (mode dependent) |
| Foreign keys | OFF by default (`PRAGMA`) | on | on |
| Concurrency | 1 writer, WAL helps readers | MVCC, many writers | MVCC, row locks |
| Default isolation | serializable (effectively) | READ COMMITTED | REPEATABLE READ |
| Partial/expr indexes | yes | yes | no / functional only (8.0) |
| Window fns, CTEs | 3.25+/3.8+ | yes | 8.0+ |
| FULL OUTER JOIN | 3.39+ | yes | no |
| Upsert | `ON CONFLICT` | `ON CONFLICT` | `ON DUPLICATE KEY UPDATE` |
| Auto id | `INTEGER PRIMARY KEY` | `IDENTITY`/`SERIAL` | `AUTO_INCREMENT` |
| Case-sensitive LIKE | no (ASCII) | yes (`ILIKE`) | depends on collation |
| `ALTER` support | limited | rich, transactional DDL | rich, DDL auto-commits |

## Common mistakes
1. Storing money as floating point; storing lists in a column.
2. No FK or UNIQUE constraints ("the app will check").
3. Indexing every column, or never indexing FK / filter / join columns.
4. Composite index in the wrong column order; expecting it to serve the second column alone.
5. Wrapping an indexed column in a function in WHERE.
6. Reading in the app, then writing back (lost updates) without lock/version/atomic UPDATE.
7. Holding a transaction open while calling an external API or waiting for a user.
8. Not retrying on deadlock/serialization errors.
9. Assuming SQLite behaviour (FKs, typing, locking) carries over to production databases.
10. Treating EXPLAIN on a tiny dev table as representative of production data volume.

## How interviewers probe this topic
- "Design the schema for X" (Twitter follows, library, ride sharing, URL shortener): entities, keys, relationships, constraints, indexes for the main queries, then "how does it scale?"
- "Is this table in 3NF? Why would you denormalize?"
- "Why is this query slow? What index would you add and what's the column order?" Often with an EXPLAIN output.
- "What does an index cost?" and "when would the database ignore your index?"
- "Explain ACID with an example," "isolation levels and the anomalies each prevents," "what is MVCC?"
- "Two users buy the last item at once. How do you prevent overselling?" (atomic UPDATE with `WHERE stock > 0`, row lock, optimistic version, constraint).
- "How would you transfer money between accounts safely? What if the process dies midway? What about deadlocks?"
- "SQL or NoSQL for X? OLTP or OLAP?" (reason from access patterns, consistency needs and scale; avoid dogma).
- For forward-deployed roles: how you would model a customer's messy data, migrate it safely (idempotent loads, upserts, constraints), and diagnose slow queries live.

## Your task
1. Run the lesson snippets in a REPL with `schema.db_events()` etc.
2. Fill in `exercises.py` (16 functions) until green. The tests check behaviour (constraint violations, query plans, transaction results).
3. Do `interview-qa.md` aloud.
