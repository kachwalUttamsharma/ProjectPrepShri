# Part 01: SQL language map, DDL and DML

Goal: see SQL as a language with sub-languages and dialects (not "a Python thing"), and master the statements that
change schema and data. Weeks 1-4 covered SELECT, joins, CTEs, windows, basic constraints and transactions; this part
fills in what they skipped: dialect differences, ALTER/DROP, upsert, MERGE, TRUNCATE, RETURNING.

Already covered (read, do not repeat): SELECT/WHERE/NULL/GROUP BY in
[week-01](../../week-01-select-filter-aggregate/lesson.md); keys, constraints, normalization, indexes, transactions in
[week-04](../../week-04-schema-indexes-transactions/lesson.md).

Setup: `sqlite3 mydb.db < setup.sql` then `sqlite3 mydb.db`. All outputs below were produced with SQLite 3.54 on this
machine. Snippets marked **(not run here, verify)** are Postgres/MySQL/SQL Server syntax; `psql` and `mysql` are not
installed here. Version-dependent facts: check current docs.

## 1. SQL is a family of sub-languages

| Sub-language | Purpose | Statements | Notes |
|---|---|---|---|
| DDL (Data Definition) | define structure | CREATE, ALTER, DROP, TRUNCATE, RENAME | MySQL commits implicitly after DDL; Postgres and SQL Server DDL is transactional; SQLite DDL is transactional too |
| DML (Data Manipulation) | change rows | INSERT, UPDATE, DELETE, MERGE | |
| DQL (Data Query) | read rows | SELECT | some books fold this into DML |
| DCL (Data Control) | permissions | GRANT, REVOKE | see part 03; SQLite has none (file permissions only) |
| TCL (Transaction Control) | group statements | BEGIN/START TRANSACTION, COMMIT, ROLLBACK, SAVEPOINT | see part 05 |

Interview shortcut: DDL = shape, DML = data, DQL = read, DCL = who, TCL = when it becomes permanent.

## 2. Standard SQL vs dialects

SQL is an ISO/ANSI standard (SQL-92, SQL:1999 added CTEs/triggers, SQL:2003 windows/MERGE, SQL:2016 JSON, and later
revisions). No engine implements all of it and every engine adds extensions. Typical dialect splits:

- Quoting identifiers: `"name"` standard (Postgres, SQLite, Oracle); `` `name` `` MySQL; `[name]` SQL Server (and SQLite tolerates all three).
- String literals always use single quotes: `'abc'`. Double quotes are identifiers in standard SQL (MySQL treats them as strings by default unless ANSI_QUOTES).
- Row limiting: `LIMIT n` (Postgres, MySQL, SQLite), `FETCH FIRST n ROWS ONLY` (standard, Postgres, Oracle 12c+, SQL Server with OFFSET), `TOP n` (SQL Server).
- String concat: `||` (standard, Postgres, SQLite); `CONCAT()` (MySQL; `||` means OR there by default); `+` or CONCAT in SQL Server.
- Identity columns: see section 5.

More in [../cheatsheet.md](../cheatsheet.md).

## 3. Data types across dialects

| Concept | Standard / Postgres | MySQL | SQLite | SQL Server |
|---|---|---|---|---|
| Small/normal/big int | SMALLINT / INTEGER / BIGINT | TINYINT.. BIGINT | INTEGER (1-8 bytes, dynamic) | TINYINT.. BIGINT |
| Exact decimal | NUMERIC(p,s) | DECIMAL(p,s) | NUMERIC affinity (stored as int or float!) | DECIMAL(p,s) |
| Float | REAL, DOUBLE PRECISION | FLOAT, DOUBLE | REAL | REAL, FLOAT |
| Text | TEXT, VARCHAR(n), CHAR(n) | VARCHAR(n), TEXT | TEXT | VARCHAR(n), NVARCHAR(n) (Unicode) |
| Boolean | BOOLEAN | BOOLEAN = TINYINT(1) alias | no type; 0/1 integers (TRUE/FALSE keywords exist) | BIT |
| Date/time | DATE, TIME, TIMESTAMP [WITH TIME ZONE] | DATE, DATETIME, TIMESTAMP | no type; store TEXT ISO-8601, REAL or INTEGER | DATE, DATETIME2, DATETIMEOFFSET |
| JSON | JSON, JSONB | JSON | TEXT + json1 functions | NVARCHAR + JSON functions (newer versions add a native type; check current docs) |
| UUID | UUID | CHAR(36) or BINARY(16) | TEXT/BLOB | UNIQUEIDENTIFIER |
| Binary | BYTEA | BLOB, VARBINARY | BLOB | VARBINARY |
| Auto id | GENERATED ... AS IDENTITY, SERIAL | AUTO_INCREMENT | INTEGER PRIMARY KEY (rowid alias) | IDENTITY(1,1) |

Rules of thumb:
- Money: exact decimals (NUMERIC/DECIMAL) or integer cents. Never FLOAT.
- Postgres: prefer TEXT or VARCHAR (same speed); `TIMESTAMPTZ` for instants. Postgres is strictly typed.
- MySQL: `TIMESTAMP` has a limited range and time-zone conversion semantics, `DATETIME` does not; check current docs for ranges.
- SQLite is dynamically typed: the declared type is only an "affinity". Real output:

```sql
CREATE TABLE t (n INTEGER);
INSERT INTO t VALUES (42), ('abc'), ('7');
SELECT n, typeof(n) AS type FROM t;
```
```
 n    type
---  -------
 42  integer
abc  text
  7  integer
```
`'abc'` was happily stored in an INTEGER column; `'7'` was converted. Postgres would reject `'abc'`. (Newer SQLite supports `CREATE TABLE ... STRICT` to enforce types; check current docs.)

## 4. CREATE, ALTER, DROP

```sql
CREATE TABLE courses (
    id      INTEGER PRIMARY KEY,
    code    TEXT NOT NULL UNIQUE,
    title   TEXT NOT NULL,
    credits INTEGER NOT NULL DEFAULT 3 CHECK (credits BETWEEN 1 AND 10)
);
CREATE TABLE IF NOT EXISTS ...;          -- idempotent scripts
CREATE TABLE copy AS SELECT ...;         -- CTAS: copies data, NOT constraints/indexes (SQL Server: SELECT ... INTO)
```

### ALTER TABLE
```sql
ALTER TABLE students ADD COLUMN phone TEXT;            -- works everywhere
ALTER TABLE students RENAME COLUMN phone TO mobile;    -- Postgres, MySQL 8, SQLite 3.25+
SELECT name, type FROM pragma_table_info('students');  -- SQLite introspection
```
```
  name      type
---------  -------
id         INTEGER
email      TEXT
full_name  TEXT
city       TEXT
joined_on  TEXT
mobile     TEXT
```
Dialect-specific (not run here, verify):
```sql
-- Postgres
ALTER TABLE students ALTER COLUMN city SET NOT NULL;
ALTER TABLE students ALTER COLUMN city TYPE VARCHAR(100);
ALTER TABLE students DROP COLUMN mobile;
ALTER TABLE students ADD CONSTRAINT uq_email UNIQUE (email);
-- MySQL
ALTER TABLE students MODIFY COLUMN city VARCHAR(100) NOT NULL;
ALTER TABLE students DROP COLUMN mobile;
-- SQL Server
ALTER TABLE students ALTER COLUMN city NVARCHAR(100) NOT NULL;
EXEC sp_rename 'students.mobile', 'phone', 'COLUMN';
```
SQLite supports ADD/RENAME/DROP COLUMN (DROP since 3.35) but cannot change a column's type or constraints; the recipe is: create new table, copy rows, drop old, rename new.

Operational warning: some ALTERs rewrite the whole table and hold a strong lock (changing a type; in older Postgres adding a column with a DEFAULT; many MySQL operations unless ALGORITHM=INSTANT/INPLACE). Which are cheap depends on the version: check current docs. See part 05 (migrations without downtime).

### DROP
```sql
DROP TABLE IF EXISTS t;
DROP TABLE parent CASCADE;     -- Postgres: also drops dependent objects (views, FKs). Dangerous.
```
Dropping a table referenced by a foreign key fails (Postgres/MySQL) unless you CASCADE or drop the FK first.

## 5. Constraints (beyond week 4)

Week 4 introduced PK / UNIQUE / NOT NULL / CHECK / FK; here are the details people miss. Real error messages from SQLite:

```sql
INSERT INTO courses (code,title,credits) VALUES ('X1','Bad',99);
-- CHECK constraint failed: credits BETWEEN 1 AND 10
INSERT INTO enrollments VALUES (1, 99, 50);
-- FOREIGN KEY constraint failed
INSERT INTO students (email, full_name) VALUES ('z@example.com', NULL);
-- NOT NULL constraint failed: students.full_name
DELETE FROM courses WHERE id = 1;        -- ON DELETE RESTRICT, course 1 has enrollments
-- FOREIGN KEY constraint failed
```

- **FK actions**: `ON DELETE CASCADE | RESTRICT | NO ACTION | SET NULL | SET DEFAULT`. Delete a student and their enrollments vanish:
```sql
DELETE FROM students WHERE id = 3 RETURNING id, full_name;
SELECT count(*) AS enrollments_left FROM enrollments;
```
```
id  full_name
--  ---------
 3  Chen Li
enrollments_left
----------------
               4
```
(it was 5; student 3's row was cascaded.)
- **SQLite FK gotcha**: enforcement is off unless `PRAGMA foreign_keys = ON` on each connection. Postgres/MySQL(InnoDB) always enforce.
- **NULL and UNIQUE**: NULLs are distinct, so a UNIQUE column may hold many NULLs (SQLite, Postgres by default, MySQL). Real output with two NULL inserts into a UNIQUE column: `null_rows_in_unique = 2`. SQL Server allows only one NULL in a UNIQUE constraint. Postgres 15+ has `UNIQUE NULLS NOT DISTINCT` (check current docs).
- **CHECK passes on NULL**: a CHECK evaluating to UNKNOWN is accepted (the grade column accepts NULL despite `BETWEEN 0 AND 100`). Add NOT NULL if you mean it. MySQL enforces CHECK only from 8.0.16; older versions parse and ignore it.
- **Composite keys**: `PRIMARY KEY (student_id, course_id)` in `enrollments` makes duplicate pairs impossible.
- **Deferrable constraints** (Postgres, SQLite, Oracle): `DEFERRABLE INITIALLY DEFERRED` checks the FK at COMMIT, handy for circular inserts. Not in MySQL.
- **Exclusion constraints** (Postgres only): "no two bookings overlap" via `EXCLUDE USING gist`. Not run here, verify.
- **DEFAULT**: constant or expression (`DEFAULT CURRENT_TIMESTAMP`). Postgres `DEFAULT now()`.
- **Generated columns**: `full AS (a || b) STORED` in several engines; syntax differs, check current docs.

Auto-generated keys, by dialect (not run here, verify):
```sql
-- Postgres / standard (preferred over SERIAL on new schemas)
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
-- MySQL
id BIGINT AUTO_INCREMENT PRIMARY KEY
-- SQL Server
id BIGINT IDENTITY(1,1) PRIMARY KEY
-- SQLite
id INTEGER PRIMARY KEY            -- alias of rowid; AUTOINCREMENT only prevents id reuse
```
Sequences and UUIDs are explored in part 03.

## 6. INSERT, UPDATE, DELETE

```sql
INSERT INTO students (email, full_name) VALUES ('eve@example.com', 'Eve');          -- always list columns
INSERT INTO students (email, full_name) VALUES ('a@x.com','A'), ('b@x.com','B');    -- multi-row: one statement, much faster
INSERT INTO archive_students SELECT * FROM students WHERE joined_on < '2024-03-01'; -- INSERT ... SELECT
```
Column omitted => its DEFAULT (or NULL). `INSERT ... VALUES` without a column list breaks when someone adds a column.

```sql
UPDATE courses SET credits = credits + 1 WHERE code = 'PY101';
UPDATE enrollments SET grade = grade + 5 WHERE course_id = 1 AND grade IS NOT NULL;
```
**Always write the WHERE first.** `UPDATE`/`DELETE` without WHERE touches every row. Habit: run a `SELECT` with the same WHERE, then change the verb; or wrap in a transaction and check the "rows affected" count:

```sql
BEGIN;
DELETE FROM enrollments;
SELECT count(*) AS inside_tx FROM enrollments;   -- 0
ROLLBACK;
SELECT count(*) AS after_rollback FROM enrollments;  -- 4 here (5 in a fresh setup.sql)
```
(Real output: `inside_tx 0`, `after_rollback 4` in the session where student 3 had already been deleted.)

UPDATE with data from another table (dialects differ, not run here, verify):
```sql
-- Postgres / SQL Server-ish
UPDATE enrollments e SET grade = 0 FROM students s WHERE s.id = e.student_id AND s.city IS NULL;   -- Postgres
-- MySQL
UPDATE enrollments e JOIN students s ON s.id = e.student_id SET e.grade = 0 WHERE s.city IS NULL;
-- Portable: correlated subquery
UPDATE enrollments SET grade = 0 WHERE student_id IN (SELECT id FROM students WHERE city IS NULL);
```

### RETURNING
Get the affected rows back without a second query. Postgres, SQLite 3.35+, MariaDB 10.5+ (INSERT/DELETE); not in MySQL. SQL Server uses `OUTPUT inserted.col`. Real output:
```sql
UPDATE courses SET credits = credits + 1 WHERE code='PY101' RETURNING code, credits;
```
```
code   credits
-----  -------
PY101        4
```
```sql
INSERT INTO students (email, full_name) VALUES ('eve@example.com','Eve') RETURNING id, joined_on;
```
```
id  joined_on
--  ----------
 5  2024-01-01
```
This is the right way to get a generated id (not `SELECT MAX(id)`, which races). MySQL: `LAST_INSERT_ID()`. SQL Server: `INSERT ... OUTPUT inserted.id VALUES ...` (not run here, verify).

## 7. Upsert

"Insert, or if the key already exists, update." Never implement as SELECT-then-INSERT in application code: two concurrent sessions both see "missing" and one fails (or duplicates).

Postgres and SQLite (identical syntax; real output from SQLite):
```sql
INSERT INTO students (id, email, full_name, city) VALUES (9, 'asha@example.com', 'Asha R. Rao', 'Mumbai')
ON CONFLICT (email) DO UPDATE SET full_name = excluded.full_name, city = excluded.city;
```
```
id  email             full_name    city
--  ----------------  -----------  ------
 1  asha@example.com  Asha R. Rao  Mumbai
 2  ben@example.com   Ben Carter   Austin
 3  chen@example.com  Chen Li
 4  dina@example.com  Dina Ortiz   Austin
```
The conflict on `email` was detected, row 1 updated in place, no id 9 created. `excluded` = the row you tried to insert.
`ON CONFLICT DO NOTHING` skips silently (real output: student count stays at 4).

MySQL (not run here, verify):
```sql
INSERT INTO students (email, full_name, city) VALUES ('asha@example.com','Asha R. Rao','Mumbai')
ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), city = VALUES(city);   -- newer: use a row alias, check current docs
INSERT IGNORE INTO ...;    -- ignores ALL errors of certain kinds, not just duplicates: prefer ON DUPLICATE KEY UPDATE id=id
```
MySQL fires on ANY unique key, you cannot name which one. Rows-affected quirk: 1 = inserted, 2 = updated, 0 = unchanged.

## 8. MERGE

Standard SQL:2003. Supported by SQL Server, Oracle, and Postgres 15+ (check current docs). Not in MySQL or SQLite. Not run here, verify:
```sql
MERGE INTO students AS t
USING staging_students AS s ON t.email = s.email
WHEN MATCHED AND s.full_name <> t.full_name THEN UPDATE SET full_name = s.full_name, city = s.city
WHEN NOT MATCHED THEN INSERT (email, full_name, city) VALUES (s.email, s.full_name, s.city)
WHEN NOT MATCHED BY SOURCE THEN DELETE;      -- BY SOURCE is SQL Server only
```
Use for bulk sync from a staging table. SQL Server's MERGE has a history of concurrency bugs; many teams prefer separate statements there (check current guidance). In Postgres MERGE, concurrent inserts may still raise unique violations; ON CONFLICT is safer for single-row upserts.

## 9. DELETE vs TRUNCATE vs DROP

| | DELETE | TRUNCATE | DROP TABLE |
|---|---|---|---|
| Category | DML | DDL (treated as DDL) | DDL |
| WHERE clause | yes | no | no |
| Removes | chosen rows | all rows, keeps table | rows and table |
| Speed on big tables | slow (row by row, logs each) | fast (deallocates pages, minimal logging) | fast |
| Triggers fire | yes (row triggers) | no (Postgres has TRUNCATE triggers only) | no |
| Resets identity/auto-increment | no | yes in MySQL, SQL Server; Postgres only with `RESTART IDENTITY` | n/a |
| Transactional / rollback | yes | Postgres, SQL Server: yes; MySQL, Oracle: implicit commit, no | Postgres: yes; MySQL: no |
| With FK references | works if children handled | fails (MySQL, SQL Server) unless `CASCADE` (Postgres) | needs CASCADE |
| Locks | row locks | table lock (Postgres ACCESS EXCLUSIVE) | table lock |

SQLite has no TRUNCATE; `DELETE FROM t;` is optimized into a truncate when there's no WHERE (and triggers).
Postgres: `TRUNCATE a, b RESTART IDENTITY CASCADE;` (not run here, verify).

## 10. Transactions around DDL/DML (recap + dialect hooks)

Concept in [week-04 section 5](../../week-04-schema-indexes-transactions/lesson.md). New points: Postgres and SQLite allow DDL inside a transaction, so a failed migration rolls back wholly; MySQL commits implicitly before and after most DDL, so a half-applied migration is possible. Always run migrations in a tool that records versions (Flyway, Liquibase, Alembic, Prisma Migrate).

## Common mistakes
- `UPDATE`/`DELETE` without WHERE; not checking "rows affected".
- `INSERT` without a column list.
- FLOAT for money; storing dates as free-form text.
- Relying on SQLite's leniency (types, FK off, aliases in WHERE) then deploying on Postgres.
- `SELECT MAX(id)` instead of RETURNING / LAST_INSERT_ID.
- App-level check-then-insert instead of a UNIQUE constraint plus upsert.
- Thinking CHECK rejects NULL.
- Expecting TRUNCATE to roll back on MySQL.

## Your task
1. `sqlite3 mydb.db < setup.sql`.
2. Work through `practice.sql` (write each query under its task, run with `sqlite3 mydb.db < practice.sql` or paste into the shell).
3. Read `interview-qa.md` aloud, answering before reading the model answer.
4. Optional: run Postgres via Docker (see ../README.md) and retype the dialect snippets above; note what differs.
