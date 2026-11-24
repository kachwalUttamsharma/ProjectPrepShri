# Part 01 interview Q&A: SQL language map, DDL, DML

Answer aloud first, then compare. Version-dependent details: check current docs.

**1. What are the SQL sub-languages?**
DDL (CREATE/ALTER/DROP/TRUNCATE) defines structure; DML (INSERT/UPDATE/DELETE/MERGE) changes rows; DQL (SELECT) reads; DCL (GRANT/REVOKE) controls permissions; TCL (BEGIN/COMMIT/ROLLBACK/SAVEPOINT) controls transactions.

**2. Is SQL one language? What does "standard SQL" mean in practice?**
It is an ISO/ANSI standard, but each engine implements a subset plus extensions (LIMIT vs TOP vs FETCH FIRST, concatenation operators, auto-increment syntax, RETURNING vs OUTPUT). Core SELECT/JOIN/GROUP BY is portable; DDL details, date functions, upsert and procedural code are not.

**3. DELETE vs TRUNCATE vs DROP?**
DELETE: DML, row by row, WHERE allowed, fires triggers, fully logged, rollbackable. TRUNCATE: removes all rows quickly by deallocating storage, no WHERE, usually resets identity, takes a stronger lock, restricted with FKs; rollbackable in Postgres/SQL Server but implicitly commits in MySQL/Oracle. DROP removes the table itself.

**4. Why is MySQL DDL "not transactional" and why does it matter?**
MySQL implicitly commits around most DDL, so a migration that fails halfway leaves a half-applied schema. Postgres, SQL Server and SQLite can roll back DDL. Practical consequence: make MySQL migrations small and idempotent.

**5. How do you do an upsert in Postgres, MySQL, SQL Server, and SQLite?**
Postgres/SQLite: `INSERT ... ON CONFLICT (key) DO UPDATE SET ... = excluded....` or `DO NOTHING`. MySQL: `INSERT ... ON DUPLICATE KEY UPDATE ...`. SQL Server/Oracle: `MERGE` (Postgres 15+ also). Requires a unique constraint/index as the conflict target.

**6. Why not SELECT then INSERT/UPDATE in application code?**
Race condition: two sessions both see "missing" and both insert, giving a duplicate or an error. A unique constraint plus an atomic upsert pushes the decision into the database.

**7. What does MERGE do, and what are its caveats?**
Joins a source to a target and applies WHEN MATCHED / NOT MATCHED actions in one statement; good for staging-table syncs. Not in MySQL/SQLite. SQL Server's implementation has known concurrency pitfalls; in Postgres, concurrent inserts can still hit unique violations.

**8. What is RETURNING and which databases support it?**
Returns columns of affected rows from INSERT/UPDATE/DELETE in one round trip. Postgres, SQLite 3.35+, MariaDB (insert/delete). SQL Server uses OUTPUT; MySQL has none (use LAST_INSERT_ID()). Use it instead of SELECT MAX(id), which is racy.

**9. How do you get the generated id after an insert in each database?**
Postgres/SQLite: RETURNING id. MySQL: LAST_INSERT_ID() (per connection). SQL Server: OUTPUT inserted.id (or SCOPE_IDENTITY()).

**10. What happens to NULLs in UNIQUE columns?**
In SQLite, Postgres (default) and MySQL, NULLs are treated as distinct, so many NULLs are allowed. SQL Server permits only one NULL. Postgres 15+ can opt in to NULLS NOT DISTINCT.

**11. Does a CHECK constraint reject NULL?**
No. CHECK passes when the expression is TRUE or UNKNOWN. `CHECK (grade BETWEEN 0 AND 100)` accepts NULL; add NOT NULL if required. Also note MySQL enforces CHECK only from 8.0.16.

**12. Explain ON DELETE CASCADE, RESTRICT, NO ACTION, SET NULL.**
CASCADE deletes children; RESTRICT blocks the parent delete immediately; NO ACTION blocks at statement end (can be deferred in Postgres); SET NULL nulls child FK (column must be nullable). Choose CASCADE for owned data (order lines), RESTRICT for reference data.

**13. Name data type pitfalls: money, dates, booleans, strings.**
Money: DECIMAL/NUMERIC or integer cents, never FLOAT. Dates: use real types; in Postgres prefer TIMESTAMPTZ for instants. Booleans: BOOLEAN in Postgres, TINYINT(1) alias in MySQL, BIT in SQL Server, 0/1 in SQLite. Strings: VARCHAR(n) vs TEXT is the same performance in Postgres; SQL Server needs NVARCHAR for Unicode; MySQL needs utf8mb4 for full Unicode.

**14. What is SQLite's type affinity and why can it hurt?**
Declared types are hints; any value can be stored in any column unless the table is STRICT. `'abc'` goes into an INTEGER column. Code that works on SQLite may fail on Postgres, so validate with the production engine.

**15. Why is `INSERT INTO t VALUES (...)` without column list bad?**
It depends on column order, so adding or reordering columns silently breaks or corrupts data. Always name columns.

**16. How do you safely run a risky UPDATE or DELETE in production?**
Write the SELECT with the same WHERE first and count; run in a transaction; check rows affected before COMMIT; have a backup/PITR; for huge changes, batch by key range to avoid long locks and bloat.

**17. Can you change a column type online?**
Depends on engine and change. Many type changes rewrite the table under a heavy lock. Safe pattern: add new column, backfill in batches, dual-write, switch reads, drop old (see part 05). Check current docs for what your version does in place.

**18. What does CREATE TABLE AS SELECT copy and not copy?**
Columns and data, not primary keys, indexes, defaults or FKs (details vary; SQL Server uses SELECT INTO). Re-add constraints explicitly.

**19. What is the difference between a PRIMARY KEY and a UNIQUE NOT NULL column?**
Practically close: both enforce uniqueness and identify rows. A table has one primary key, FKs conventionally reference it, and engines may use it as the clustered index (InnoDB, SQL Server by default). UNIQUE can be several and may allow NULL.

**20. Why use IDENTITY/GENERATED instead of SERIAL in Postgres?**
GENERATED ... AS IDENTITY is the SQL-standard form, ties the sequence to the column, and `ALWAYS` prevents accidental manual overrides; SERIAL is legacy shorthand with looser ownership and permissions behaviour.
