# General SQL: the language beyond the weekly exercises

Weeks 1-5 (`../week-01..05`) taught querying through Python + SQLite. This track
covers SQL as a database language in its own right: DDL/DML, dialects, database
objects, internals, concurrency, and engine/warehouse differences. No Python needed.

Prerequisite: finish at least weeks 1-4 (SELECT, joins, CTE/window, indexes, ACID basics).
Parts link back to those lessons instead of repeating them.

## Study order

| Part | Folder | Topic |
|------|--------|-------|
| 01 | `01-language-map-ddl-dml/` | Sub-languages, types, DDL, constraints, DML, upsert, MERGE, RETURNING |
| 02 | `02-set-ops-functions-json/` | Set operations, functions by dialect, pagination, LATERAL, pivot, JSON |
| 03 | `03-objects-programmability/` | Views, sequences, triggers, procedures, schemas, roles, RLS |
| 04 | `04-how-databases-work/` | Storage, WAL, MVCC, planner, EXPLAIN, index types, join algorithms |
| 05 | `05-concurrency-reliability/` | Isolation anomalies, locks, deadlocks, replication, backups, migrations |
| 06 | `06-engines-warehouses-modeling/` | Engine comparison, OLTP vs OLAP, columnar, partitioning, star schema, SCD |

Then: `rapid-fire.md` (20 mixed questions) and `cheatsheet.md` (dialect differences).

Per part, in this order: read `lesson.md`, run `setup.sql`, attempt `practice.sql`,
quiz yourself with `interview-qa.md`. Solutions are deliberately not in this repo
(`/tmp/ref-generalsql/<part>/solutions.sql` on the machine that generated them;
it may be wiped on reboot, so try the tasks first and ask for them if missing).

## Practising with the sqlite3 CLI

```
sqlite3 :memory:                      # scratch database
sqlite3 practice.db                   # persistent file
```
Inside the shell:
```
.read setup.sql        -- load a part's schema and data
.headers on
.mode column           -- or: .mode box / .mode markdown
.tables
.schema employees
.read my_answers.sql
.quit
```
Tips: write answers in a scratch file and `.read` it repeatedly. Enable
`PRAGMA foreign_keys = ON;` per connection (SQLite leaves it off by default).
Some tasks (Postgres/MySQL-only features) cannot run in SQLite; those are marked,
and the lessons label snippets "not run here, verify" when they were not executed.

## Optional: real Postgres and MySQL via Docker

```
docker run --name pg -e POSTGRES_PASSWORD=pw -p 5432:5432 -d postgres
docker exec -it pg psql -U postgres

docker run --name my -e MYSQL_ROOT_PASSWORD=pw -p 3306:3306 -d mysql
docker exec -it my mysql -uroot -ppw
```
Load a script: `docker exec -i pg psql -U postgres < setup.sql` (setup scripts are
written for SQLite; small edits such as `AUTOINCREMENT` vs `SERIAL`/`GENERATED ... AS IDENTITY`
may be needed, see part 01). Clean up with `docker rm -f pg my`. Image tags and
defaults change between versions: check current docs.

## Conventions
- Verified in SQLite: examples with pasted output. Everything else is flagged "not run here, verify".
- Version-dependent facts say "check current docs".
