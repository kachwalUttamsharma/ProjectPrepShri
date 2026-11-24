# Week 4 interview Q&A: schema design, indexes, transactions

**1. Primary key vs unique key vs foreign key?**
PK: uniquely identifies a row, NOT NULL, one per table. UNIQUE: no duplicates among non-NULL values, many per table. FK: column(s) that must match an existing key in another table (or be NULL), enforcing referential integrity with a chosen ON DELETE action.

**2. Natural vs surrogate keys?**
Natural keys are real attributes (email, ISBN) and can change or be non-unique in practice. Surrogate keys (auto-increment, UUID) are stable and compact. Common compromise: surrogate PK + UNIQUE constraint on the natural key. UUIDs avoid central coordination but fragment B-tree indexes if random (prefer time-ordered UUIDs like UUIDv7).

**3. Explain 1NF, 2NF, 3NF in one sentence each.**
1NF: atomic values and no repeating groups. 2NF: no non-key attribute depends on part of a composite key. 3NF: no non-key attribute depends on another non-key attribute: "the key, the whole key and nothing but the key".

**4. Why normalise? Why denormalise?**
Normalising removes redundancy and update/insert/delete anomalies, improves integrity. Denormalising (copied columns, counters, summary tables, star schemas) speeds reads and avoids joins at the cost of extra writes and potential inconsistency, so do it with measurements, and keep a source of truth.

**5. How do you model a many-to-many relationship?**
A junction table with FKs to both sides and a composite PK (or a UNIQUE pair) preventing duplicates, plus any relationship attributes (enrolled_on, role, quantity).

**6. What does an index do and what does it cost?**
A sorted B-tree structure that finds rows in O(log n) without scanning, and supports range queries and ordered output. Costs: disk space, slower INSERT/UPDATE/DELETE (every index maintained), more planner choices and write amplification.

**7. Composite index (a, b, c): which queries can use it?**
Filters on `a`, `a,b`, `a,b,c` (leftmost prefix), and `a` equality plus range on `b`. A filter only on `b` or `c` cannot seek. Put equality columns first, then the range or sort column; after a range column the following columns cannot be used for seeking.

**8. What is a covering index?**
An index that contains every column the query reads, so the engine never visits the table (SQLite "COVERING INDEX", PG "Index Only Scan", MySQL "Using index"). Trade-off: bigger index, more write cost.

**9. Why might the database ignore an index?**
Function/expression on the column, implicit type cast, leading wildcard LIKE, low selectivity (planner decides a scan is cheaper), tiny table, OR conditions, stale statistics, non-leftmost column of a composite, or the query returns most of the table anyway.

**10. Clustered vs non-clustered index?**
Clustered: table rows are stored in index order (InnoDB PK; SQLite rowid tables), one per table; lookups by PK hit the data directly. Non-clustered/secondary: separate structure storing key + pointer (PK or row id); needs an extra lookup unless covering. PG heap tables have only secondary indexes (CLUSTER is a one-time sort).

**11. How do you find why a query is slow?**
Run EXPLAIN (ANALYZE in PG/MySQL 8.0.18+): look for full scans on large tables, sorts/temp tables, bad join order or estimates far from actual rows, large rows removed by filter. Then fix with an index, query rewrite (sargable predicates), pre-aggregation, or statistics refresh. Verify with timing and the plan afterwards.

**12. Explain ACID.**
Atomicity (all-or-nothing, undo/rollback), Consistency (constraints and invariants hold across the transaction), Isolation (concurrent transactions do not interfere beyond what the level allows), Durability (committed data survives crashes via WAL/fsync).

**13. List the isolation levels and anomalies each one prevents.**
READ UNCOMMITTED: nothing (dirty reads possible). READ COMMITTED: prevents dirty reads. REPEATABLE READ: also non-repeatable reads (phantoms depend on engine). SERIALIZABLE: also phantoms and write skew; behaves as if transactions ran one at a time.

**14. What is MVCC?**
Multi-version concurrency control: writers create new row versions while readers keep reading the version visible to their snapshot, so readers do not block writers. Old versions are reclaimed later (PG VACUUM, InnoDB purge). Cost: bloat and long-transaction problems.

**15. What are the defaults in Postgres, MySQL and SQLite?**
PG: READ COMMITTED. MySQL InnoDB: REPEATABLE READ. SQLite: effectively SERIALIZABLE (single writer; in WAL mode readers see a snapshot and do not block the writer).

**16. What is a deadlock and how do you handle it?**
Two or more transactions each hold a lock the other needs. The DB detects the cycle and aborts a victim. Handle: catch the error and retry; prevent via consistent lock ordering, short transactions, fewer rows locked, proper indexes on updated/locked columns.

**17. Two users try to buy the last item simultaneously. How do you prevent overselling?**
Make the check and the decrement a single atomic statement: `UPDATE inventory SET stock = stock - 1 WHERE id = ? AND stock > 0` and check rowcount; or `SELECT ... FOR UPDATE` in a transaction; or optimistic version check with retry; plus a `CHECK (stock >= 0)` as the backstop. A read-then-write in application code is a race.

**18. What is a lost update and how do you prevent it?**
Two transactions read the same value and both write based on it; one write overwrites the other. Fix with atomic updates (`x = x + 1`), row locks, optimistic locking (version column), SERIALIZABLE/REPEATABLE READ with retry (PG aborts the second writer).

**19. What is write skew?**
Each of two concurrent transactions reads an overlapping set, then updates different rows so that together they violate an invariant (e.g. both doctors go off-call). Snapshot isolation allows it; SERIALIZABLE, explicit locking of the read set, or a constraint prevents it.

**20. Optimistic vs pessimistic locking?**
Pessimistic: lock rows up front (`FOR UPDATE`) so others wait; good under high contention, risk of blocking/deadlocks. Optimistic: no lock, detect conflict at write time via version/timestamp and retry; best when conflicts are rare and transactions are long (user think time).

**21. SQL vs NoSQL: how do you choose?**
Start from access patterns, consistency and scale. Relational for structured data, joins, transactions, ad-hoc queries (default). NoSQL when you need horizontal write scale, key-based access at very low latency, flexible documents, graph/time-series shapes, and can accept limited joins/transactions and eventual consistency. Many systems use both (Postgres + Redis + a warehouse).

**22. OLTP vs OLAP?**
OLTP: many short transactions touching few rows, normalised row stores with B-trees, latency-sensitive. OLAP: few large scans/aggregations, columnar storage, denormalised star schemas, batch loading. Keep analytics off the OLTP primary (replica or warehouse via ETL/CDC).

**23. How would you add a NOT NULL column to a 500M-row production table safely?**
Add it nullable (or with a constant default on engines where that is metadata-only, e.g. PG 11+), backfill in small batches, add the NOT NULL/CHECK constraint (in PG as NOT VALID then VALIDATE), deploy code that writes the column before and reads after. Avoid long exclusive locks; test the migration on a copy.

**24. Why must you use parameterised queries?**
To prevent SQL injection and let the driver/DB reuse plans. Values go through placeholders (`?`, `:name`, `%s`); identifiers (table/column names) cannot be parameterised, so whitelist them.

**25. Name three differences between SQLite and Postgres that could bite you.**
Dynamic typing (affinity) vs strict types; foreign keys off by default in SQLite; single-writer locking vs MVCC concurrency; weaker ALTER TABLE; no real user/permission model; some functions (date handling) differ. Prototyping in SQLite and deploying on Postgres requires testing the real engine.
