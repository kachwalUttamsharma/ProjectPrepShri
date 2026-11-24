# Part 05: Concurrency and reliability

Goal: predict what two simultaneous sessions will see, pick the right lock or isolation level, and know how data survives crashes and deploys.
ACID basics, BEGIN/COMMIT/ROLLBACK, and a first look at isolation and deadlocks are already in
[week-04 lesson](../../week-04-schema-indexes-transactions/lesson.md) (sections 5-6). Read that first; this part goes deeper.

Snippets marked "not run here, verify" were not executed (no `psql`/`mysql` installed). Version-dependent behaviour: check current docs.
Setup: `sqlite3 bank.db < setup.sql`. For real two-session work, use Postgres via Docker (see ../README.md).

## 1. Transactions, a bit deeper
- A transaction is a unit of atomicity AND the scope of isolation. Keep them short: long transactions hold locks, block vacuum/purge (bloat, long undo history), and hold connections.
- Autocommit: most clients commit each statement unless you `BEGIN`. Postgres `psql` and MySQL default to autocommit; Python drivers often open a transaction implicitly (sqlite3, psycopg2) - know which one you have.
- Errors inside a transaction: in Postgres, after an error the whole transaction is aborted ("current transaction is aborted") until ROLLBACK or ROLLBACK TO SAVEPOINT. MySQL lets you continue after a failed statement.
- Savepoints: `SAVEPOINT s1; ... ROLLBACK TO s1; RELEASE s1;` (all three engines).
- DDL: Postgres and SQLite have transactional DDL (CREATE/ALTER can roll back). MySQL DDL causes an implicit commit.
- SQLite specifics: `BEGIN` is DEFERRED (lock taken on first read/write); `BEGIN IMMEDIATE` takes the write lock up front; one writer at a time per database file. Default journal is rollback journal; WAL mode (`PRAGMA journal_mode=WAL`) lets readers not block the writer.

## 2. Anomalies (concrete)
Two accounts: alice 100, bob 50.

| Anomaly | Story |
|---|---|
| Dirty read | T1 updates alice to 0, not committed. T2 reads 0. T1 rolls back. T2 acted on data that never existed. |
| Non-repeatable read | T1 reads alice = 100. T2 sets 70 and commits. T1 reads again: 70. Same row, different value. |
| Phantom | T1 `SELECT COUNT(*) WHERE balance > 40` = 2. T2 inserts a matching row, commits. T1 repeats: 3. Different set of rows. |
| Lost update | T1 and T2 both read 100, T1 writes 100-30, T2 writes 100-10 (computed in the app). Final 90; T1's change is gone. |
| Write skew | Rule: at least one doctor on call. T1 and T2 each see both on call, T1 sets dr_a off, T2 sets dr_b off. Different rows written, so no row conflict; rule broken (see `oncall` table in setup.sql). |

Lost update fix options: atomic `UPDATE ... SET balance = balance - 30`; `SELECT ... FOR UPDATE`; optimistic version column; or a stricter isolation level (Postgres REPEATABLE READ aborts the second writer with a serialization error).

## 3. Isolation levels: who prevents what
The SQL standard defines four levels by which anomalies they allow; real engines differ. Summary (check current docs for your version):

| Level | PostgreSQL | MySQL InnoDB |
|---|---|---|
| READ UNCOMMITTED | Accepted but behaves as READ COMMITTED: no dirty reads ever | Real: dirty reads possible |
| READ COMMITTED | Each statement sees a fresh snapshot. Dirty read: prevented. Non-repeatable, phantom, write skew, lost update (read-modify-write in app): allowed | Same semantics (snapshot per statement). Same allowed anomalies |
| REPEATABLE READ | Snapshot isolation (one snapshot per transaction). Dirty, non-repeatable, phantom (for plain reads): prevented. Write skew: ALLOWED. Concurrent update of the same row: second writer gets "could not serialize access" error | **Default.** Consistent snapshot for plain SELECT; locking reads and writes use next-key/gap locks which block many phantoms. Lost update possible if you read with a plain SELECT then write (writes see latest committed data). Write skew: possible |
| SERIALIZABLE | SSI (serializable snapshot isolation): optimistic, detects dangerous patterns, aborts with SQLSTATE 40001; you must retry. Prevents all of the above | Plain SELECTs become locking reads (shared locks), so more blocking and deadlocks; prevents the anomalies by locking |

Defaults: Postgres READ COMMITTED; MySQL InnoDB REPEATABLE READ; SQLite is effectively SERIALIZABLE (single writer) for connections not in WAL-with-read-uncommitted modes.
Set per transaction: `BEGIN ISOLATION LEVEL REPEATABLE READ;` (Postgres) or `SET TRANSACTION ISOLATION LEVEL ...;` before `START TRANSACTION` (MySQL). Not run here, verify.

Rule of thumb: any level above READ COMMITTED means your code must handle aborts and retry.

## 4. MVCC in one paragraph
Readers do not block writers and writers do not block readers; each row version carries visibility info and each transaction reads a snapshot (see part 04). Writers still block writers on the same row. Hence locks matter only for write-write conflicts, explicit locking reads, and DDL.

## 5. Locks
- Row locks: taken by UPDATE/DELETE automatically; held until COMMIT/ROLLBACK.
- Explicit row locks (Postgres and MySQL 8+): 
```sql
BEGIN;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;   -- not run here, verify (SQLite has no FOR UPDATE)
UPDATE accounts SET balance = balance - 30 WHERE id = 1;
COMMIT;
```
  `FOR SHARE` (Postgres; `LOCK IN SHARE MODE` / `FOR SHARE` in MySQL) blocks writers but not other share-lockers. Postgres also has `FOR NO KEY UPDATE`, `FOR KEY SHARE` (used by foreign key checks).
- `NOWAIT`: error immediately instead of waiting. `SKIP LOCKED`: skip rows locked by others - the standard job-queue pattern:
```sql
-- not run here, verify (Postgres 9.5+, MySQL 8.0+)
WITH next AS (
  SELECT id FROM jobs WHERE status = 'queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED
)
UPDATE jobs SET status = 'running', claimed_by = 'w1' FROM next WHERE jobs.id = next.id RETURNING jobs.*;
```
  SKIP LOCKED gives an inconsistent view by design: fine for queues, wrong for reports.
- Table locks: `LOCK TABLE t IN ... MODE` (Postgres), `LOCK TABLES` (MySQL). ALTER TABLE usually takes a strong lock; a queued ALTER behind a long transaction blocks every later query on that table (lock queue pile-up). Use `SET lock_timeout = '2s'` (Postgres) before DDL.
- Advisory locks: application-defined mutexes held by the database. Postgres: `pg_advisory_lock(key)`, `pg_try_advisory_lock(key)`, `pg_advisory_xact_lock(key)` (released at transaction end). MySQL: `GET_LOCK('name', timeout)` / `RELEASE_LOCK`. Use for "only one cron instance runs this".
- InnoDB gap/next-key locks: in REPEATABLE READ, `SELECT ... WHERE id BETWEEN 10 AND 20 FOR UPDATE` locks the gaps too, so inserts into that range block. Surprising source of lock waits.

## 6. Deadlocks
T1 locks row A then wants B; T2 locks B then wants A. Engines detect cycles (Postgres after `deadlock_timeout`, default 1s; InnoDB immediately) and abort one victim with an error (Postgres 40P01, MySQL 1213).
Prevention: always lock in a consistent order (e.g. `ORDER BY id`), keep transactions short, lock up front with `SELECT ... FOR UPDATE ORDER BY id`, retry the victim. Diagnose: Postgres log with `log_lock_waits`, `pg_locks`/`pg_stat_activity`; MySQL `SHOW ENGINE INNODB STATUS`.

## 7. Optimistic vs pessimistic locking
- Pessimistic: lock first (`FOR UPDATE`), then change. Good under high contention; holds locks across user think-time (bad for web forms).
- Optimistic: read a `version`, update with `WHERE id = ? AND version = ?`, check rows affected; 0 rows means someone else changed it, so re-read and retry. No locks held between read and write. Good under low contention. SQLite-runnable (this is practice tasks 5-6):
```sql
UPDATE accounts SET balance = balance - 30, version = version + 1 WHERE id = 1 AND version = 1;
SELECT changes();   -- 1 on success; a second writer holding version=1 gets 0
```
Verified output: first update `1`, stale repeat `0`.
- Atomic relative updates (`balance = balance - 30`) are the simplest lost-update fix when the logic fits in one statement.
- Idempotency keys: a unique constraint on a request id turns client retries into safe no-ops.

## 8. Reliability: durability, replication, backups
- WAL / redo log: changes are logged and fsynced before COMMIT returns (see part 04). `synchronous_commit = off` (Postgres) or `innodb_flush_log_at_trx_commit` != 1 trade durability for speed.
- Replication: physical/streaming (Postgres WAL shipping, byte-for-byte replica) vs logical (row changes, per-table, cross-version; Postgres publications/subscriptions) vs MySQL binlog-based (statement/row/mixed; GTIDs). Async replicas can lag: read-your-writes bugs; sync replication costs commit latency. Failover tools (Patroni, managed services) promote a replica; risk is split-brain and lost last commits if async.
- Backups: logical (`pg_dump`, `mysqldump`: portable, slow to restore) vs physical (`pg_basebackup`, Percona XtraBackup: fast, same version). Not run here, verify:
```
pg_dump -Fc mydb > mydb.dump
pg_restore -d mydb_new mydb.dump
```
- PITR (point-in-time recovery): base backup plus continuously archived WAL (Postgres) or binlogs (MySQL); restore the base, replay logs up to a timestamp just before the bad `DELETE`. A backup you have never restored is not a backup; test restores. Replicas are not backups (a DROP replicates).
- RPO (how much data you can lose) and RTO (how long to recover) drive the design.

## 9. Connection pooling
Each Postgres connection is a process (several MB); thousands of direct connections hurt. Use an app-side pool (HikariCP, SQLAlchemy pool) and/or PgBouncer. PgBouncer modes: session, transaction (most common; breaks session state such as `SET`, advisory session locks, prepared statements in some setups), statement. Size pools small: roughly cores x 2 plus disks as a starting point, then measure. Pool exhaustion shows as requests waiting for a connection; a leaked or idle-in-transaction connection is the usual cause (set `idle_in_transaction_session_timeout`).

## 10. Migrations without downtime
Principle: every deploy step must work with both old and new application code (expand / contract).
1. Expand: add new column nullable (fast, metadata-only in modern Postgres; `ADD COLUMN ... DEFAULT const` is fast in PG 11+, MySQL 8 INSTANT in many cases - check current docs).
2. Deploy code that writes both old and new.
3. Backfill in small batches (`UPDATE ... WHERE id BETWEEN a AND b`), not one giant transaction.
4. Deploy code that reads new.
5. Contract: drop old column later.
Other tricks: `CREATE INDEX CONCURRENTLY` (Postgres; not inside a transaction), add constraints as `NOT VALID` then `VALIDATE CONSTRAINT`, MySQL online DDL (`ALGORITHM=INPLACE, LOCK=NONE`) or tools like gh-ost/pt-online-schema-change, rename via add+copy+swap rather than `RENAME COLUMN` while old code runs. Always set lock timeouts and have a rollback plan. All not run here, verify.

## Common mistakes
- Read-modify-write in application code without a lock or version check.
- Assuming REPEATABLE READ means the same thing in Postgres and MySQL.
- Not retrying on 40001 / 40P01 / 1213 / 1205 (lock wait timeout).
- Holding a transaction open across an HTTP call or user prompt.
- Treating replicas as backups; never test-restoring.
- Running ALTER TABLE without a lock timeout during peak traffic.

## Your task
Do `practice.sql`, then answer `interview-qa.md` aloud.
