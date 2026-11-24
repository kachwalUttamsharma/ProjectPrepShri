# Part 03: Database objects and programmability

Goal: know every kind of object a database holds besides tables, what each is for, and how the major dialects differ.
Prerequisites: [week-01 lesson](../../week-01-select-filter-aggregate/lesson.md) (querying), [week-04 lesson](../../week-04-schema-indexes-transactions/lesson.md) (constraints, indexes, transactions). Not repeated here.

Setup: `sqlite3 part03.db ".read setup.sql"`, then `sqlite3 part03.db`. Sections marked **SQLite (run)** were executed; sections marked **not run here, verify** (Postgres/MySQL/SQL Server) were not, because `psql` and `mysql` are not installed on this machine. Version-dependent details: check current docs.

## 1. Views
A view is a stored, named SELECT. It stores no rows (in the ordinary kind); each query on it expands the definition (the optimizer usually inlines it).

Uses: hide join complexity, give a stable interface when tables change, restrict columns/rows for security, name a business concept once.

**SQLite (run):**
```sql
CREATE VIEW order_totals AS
SELECT o.id AS order_id, c.name AS customer, o.status, SUM(oi.qty*oi.unit_price) AS total
FROM orders o JOIN customers c ON c.id=o.customer_id JOIN order_items oi ON oi.order_id=o.id
GROUP BY o.id, c.name, o.status;
SELECT * FROM order_totals ORDER BY order_id;
```
```
order_id  customer  status   total
--------  --------  -------  -----
       1  Asha      paid        90
       2  Asha      shipped    200
       3  Ben       paid        45
       4  Chen      new        100
```
Views can be built on views (`customer_spend` over `order_totals` gives Asha 290, Ben 45). Deep stacks hurt readability and plans.

Updatable views: a simple view (one table, no aggregates/DISTINCT/GROUP BY) is auto-updatable in Postgres and MySQL; `WITH CHECK OPTION` rejects writes that would make the row vanish from the view. Complex views are read-only unless you add `INSTEAD OF` triggers (Postgres, SQL Server, SQLite). SQLite views are always read-only without them.

Postgres extras (not run here, verify): `CREATE OR REPLACE VIEW`, `security_barrier` views, `security_invoker` option (recent versions; check current docs). Dropping a table used by a view fails unless `CASCADE`.

## 2. Materialized views
A view whose result is physically stored and refreshed on demand. Trade: fast reads, stale data.

- Postgres (not run here, verify): `CREATE MATERIALIZED VIEW mv AS SELECT ...; REFRESH MATERIALIZED VIEW mv;` and `REFRESH MATERIALIZED VIEW CONCURRENTLY mv;` (needs a unique index on the mv; avoids blocking readers). No automatic incremental refresh in core Postgres.
- Oracle: rich support (fast refresh, query rewrite). SQL Server: "indexed views" are the analogue and are maintained automatically (with restrictions). 
- MySQL and SQLite: no native materialized views. Emulate with a summary table refreshed by a job or triggers.
- Warehouses (BigQuery, Snowflake) have materialized views with automatic refresh and limits on allowed SQL; check current docs.

Rule of thumb: use when an expensive aggregate is read far more than the source changes and staleness is acceptable.

## 3. Generating keys: sequences, auto-increment, identity, UUIDs
| Mechanism | Where | Notes |
|---|---|---|
| `INTEGER PRIMARY KEY` | SQLite | alias of rowid; reuses max+1. `AUTOINCREMENT` guarantees never reusing ids, costs a bookkeeping table |
| `AUTO_INCREMENT` | MySQL | per-table counter; InnoDB may leave gaps (rolled-back inserts, bulk inserts) |
| `GENERATED ... AS IDENTITY` | Postgres 10+, Oracle, SQL Server (`IDENTITY(1,1)`) | SQL-standard form; preferred over `SERIAL` in new Postgres code |
| `SEQUENCE` object | Postgres, Oracle, SQL Server, MariaDB | independent counter: `CREATE SEQUENCE s; SELECT nextval('s');` |
| UUID | all (type differs) | Postgres `uuid`, MySQL `BINARY(16)`/`CHAR(36)`, SQL Server `UNIQUEIDENTIFIER` |

Postgres sequences (not run here, verify):
```sql
CREATE SEQUENCE invoice_no START 1000 INCREMENT 1;
SELECT nextval('invoice_no');
CREATE TABLE t (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, v text);
```
Key facts interviewers like: sequences are non-transactional (a rollback does not give the number back), so gaps are normal; never promise gapless numbers from a sequence. After insert, fetch the new id with `RETURNING id` (Postgres, SQLite 3.35+), `LAST_INSERT_ID()` (MySQL), `OUTPUT inserted.id` (SQL Server).

UUID trade-offs: globally unique, can be generated client-side, no hot spot on the last page, hard to guess. Cost: 16 bytes, poor locality. Random UUIDv4 as a clustered primary key in MySQL InnoDB fragments the B-tree and bloats secondary indexes (they carry the PK). Time-ordered variants (UUIDv7, ULID) reduce this; Postgres native support for generating v7 depends on version, check current docs.

SQLite demo (run): a random 16-byte hex token default and autoincrement id:
```sql
CREATE TABLE ids_demo (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       token TEXT DEFAULT (lower(hex(randomblob(16)))));
INSERT INTO ids_demo DEFAULT VALUES; INSERT INTO ids_demo DEFAULT VALUES;
SELECT id, length(token) AS toklen FROM ids_demo;   -- (1,32) and (2,32)
```

## 4. Triggers
A trigger runs a body automatically on INSERT/UPDATE/DELETE, `BEFORE`, `AFTER`, or `INSTEAD OF` (views). Granularity: row-level (all three major open-source DBs) vs statement-level (Postgres, SQL Server, Oracle; MySQL and SQLite are row-level only).

Typical uses: audit trails, maintaining derived/denormalised columns, enforcing rules a CHECK cannot express, making views writable.

**SQLite (run)**: audit price changes, only when the value actually changes.
```sql
CREATE TRIGGER trg_price_audit AFTER UPDATE OF price ON products
WHEN OLD.price <> NEW.price
BEGIN
  INSERT INTO price_audit(product_id, old_price, new_price) VALUES (OLD.id, OLD.price, NEW.price);
END;
UPDATE products SET price = 55 WHERE id=1;
UPDATE products SET price = 55 WHERE id=1;   -- no change, WHEN false, no audit row
SELECT product_id, old_price, new_price FROM price_audit;
```
```
product_id  old_price  new_price
----------  ---------  ---------
         1         50         55
```
Stock guard and decrement (run). Inserting an item that fits works; one that does not aborts the whole statement:
```sql
CREATE TRIGGER trg_stock AFTER INSERT ON order_items
BEGIN UPDATE products SET stock = stock - NEW.qty WHERE id = NEW.product_id; END;
CREATE TRIGGER trg_stock_guard BEFORE INSERT ON order_items
WHEN (SELECT stock FROM products WHERE id = NEW.product_id) < NEW.qty
BEGIN SELECT RAISE(ABORT, 'insufficient stock'); END;
INSERT INTO order_items VALUES (4,3,1,200);   -- Monitor stock 5 -> 4
INSERT INTO order_items VALUES (4,4,500,5);   -- Error: insufficient stock; Cable stays 100
```
Dialect syntax differences: Postgres triggers call a separate function (`CREATE FUNCTION ... RETURNS trigger`, then `CREATE TRIGGER ... EXECUTE FUNCTION f()`, using `NEW`/`OLD`); MySQL puts the body inline (`BEGIN ... END` with `DELIMITER`), error via `SIGNAL SQLSTATE '45000'`; SQL Server uses pseudo-tables `inserted`/`deleted` and fires once per statement (so write set-based bodies). Not run here, verify.

Cautions: triggers are invisible logic (surprising side effects), hurt bulk-load speed, can cascade or recurse, and make debugging hard. Prefer constraints and explicit application/procedure logic; keep triggers for auditing and invariants.

## 5. Stored procedures and functions
Code stored and run inside the database.
- **Function**: returns a value or table; callable inside SQL (`SELECT f(x)`). 
- **Procedure**: invoked with `CALL`; may control transactions (Postgres 11+ allows `COMMIT` inside procedures; functions cannot). SQL Server uses `EXEC`.
- Languages: Postgres PL/pgSQL (also PL/Python, SQL, etc.), MySQL its own SQL/PSM, SQL Server T-SQL, Oracle PL/SQL. SQLite has none (register functions from the host language instead).

Postgres (not run here, verify):
```sql
CREATE FUNCTION order_total(p_order bigint) RETURNS numeric
LANGUAGE sql STABLE AS $$
  SELECT COALESCE(SUM(qty*unit_price),0) FROM order_items WHERE order_id = p_order
$$;

CREATE PROCEDURE ship_order(p_order bigint) LANGUAGE plpgsql AS $$
BEGIN
  UPDATE orders SET status='shipped' WHERE id = p_order AND status='paid';
  IF NOT FOUND THEN RAISE EXCEPTION 'order % not shippable', p_order; END IF;
END $$;
CALL ship_order(3);
```
MySQL (not run here, verify):
```sql
DELIMITER //
CREATE PROCEDURE ship_order(IN p_order BIGINT)
BEGIN
  UPDATE orders SET status='shipped' WHERE id = p_order AND status='paid';
  IF ROW_COUNT() = 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='not shippable'; END IF;
END//
DELIMITER ;
```
Volatility labels in Postgres (`IMMUTABLE`, `STABLE`, `VOLATILE`) tell the planner what it may cache or inline; required `IMMUTABLE` for functions used in index expressions.

Pros: fewer round trips, one place for rules, permission control (callers get EXECUTE, not table access; `SECURITY DEFINER` in Postgres runs with the owner's rights, so set `search_path` carefully). Cons: harder to version/test, ties you to one vendor, business logic splits across layers, scales on the DB server (the hardest tier to scale).

## 6. Temporary tables and other scratch structures
Temp tables live for the session (or transaction) and are invisible to others.

**SQLite (run):**
```sql
CREATE TEMP TABLE big_orders AS SELECT order_id, total FROM order_totals WHERE total >= 100;
```
Postgres/MySQL: `CREATE TEMP[ORARY] TABLE`; SQL Server `#name` (session) and `##name` (global). Postgres can `ON COMMIT DROP`. You can index a temp table and `ANALYZE` it, which is why people use them to break a huge query into steps and give the planner real statistics, something CTEs do not do. In Postgres 12+ a CTE referenced once is inlined; `MATERIALIZED` forces a barrier (check current docs). Compare with CTEs in [week-03](../../week-03-cte-window-case-dates/lesson.md). Beware: temp-table churn creates catalog bloat in Postgres; and with connection pooling in transaction mode, session-level temp tables may vanish or leak across clients.

## 7. User-defined types
Postgres (not run here, verify):
```sql
CREATE TYPE order_status AS ENUM ('new','paid','shipped','cancelled');
CREATE DOMAIN positive_int AS integer CHECK (VALUE > 0);
CREATE TYPE money_pair AS (amount numeric, currency char(3));
```
- ENUM: stored compactly, ordered by declared order; adding values is easy (`ALTER TYPE ... ADD VALUE`), removing is not. A lookup table with FK is more flexible.
- DOMAIN: a base type plus constraints, reusable across tables. 
- Composite types: row-like values, rarely used for stored columns.
MySQL: inline `ENUM('a','b')` and `SET` column types (ordering by index position, altering is a table change). SQL Server: alias types and CLR types. SQLite: no types are enforced beyond affinity (STRICT tables in 3.37+ enforce them); use CHECK.

## 8. Schemas (namespaces)
A schema groups objects inside a database: `schema.table`.
- Postgres/SQL Server/Oracle: database > schema > object. Postgres resolves unqualified names through `search_path` (default `"$user", public`). Tip: revoke CREATE on `public` from PUBLIC (default changed in Postgres 15, check current docs).
- MySQL: "schema" is a synonym for "database"; there is no extra level. 
- SQLite: "databases" via `ATTACH DATABASE 'other.db' AS other;` then `other.table`; `main` and `temp` are built in.

Uses: multi-tenant separation (schema-per-tenant, with migration cost), separating app/reporting/staging, permission boundaries.

SQLite (run-able): 
```sql
ATTACH DATABASE ':memory:' AS archive;
CREATE TABLE archive.old_orders AS SELECT * FROM main.orders WHERE status='shipped';
```

## 9. Roles, GRANT, REVOKE (DCL)
Principle of least privilege: the application should not connect as a superuser or schema owner.

Postgres (not run here, verify):
```sql
CREATE ROLE app_ro NOLOGIN;
GRANT USAGE ON SCHEMA public TO app_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_ro;  -- future tables
CREATE ROLE alice LOGIN PASSWORD '...' ;
GRANT app_ro TO alice;              -- role membership
REVOKE INSERT ON orders FROM alice;
GRANT SELECT (id, name) ON customers TO app_ro;  -- column-level
```
Postgres has only roles (users are roles with LOGIN). MySQL (8.0+ has roles): `CREATE USER 'a'@'host' IDENTIFIED BY '...'; GRANT SELECT ON shop.* TO 'a'@'host';` the host is part of the account identity. SQL Server: logins (server) map to users (database), plus database roles. SQLite: no users or privileges at all; protect the file with the OS.

Pattern: group roles (`app_ro`, `app_rw`, `migrator`), grant to roles, assign people to roles. Views plus GRANT on the view expose only chosen columns/rows. 

## 10. Row-level security (RLS)
Restrict which rows a role sees, enforced by the database, not by app WHERE clauses. Postgres (not run here, verify):
```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::int)
  WITH CHECK (tenant_id = current_setting('app.tenant_id')::int);
-- app does per request:  SET app.tenant_id = '42';   (or SET LOCAL inside a transaction)
```
Table owners and superusers bypass RLS unless `FORCE ROW LEVEL SECURITY` (owners) is set; superusers and `BYPASSRLS` roles always bypass. Policies add a filter to every query, so index the policy column. With transaction-mode pooling use `SET LOCAL` so the setting does not leak. SQL Server has Row-Level Security via security policies and inline table-valued predicate functions. MySQL has no native RLS (use views with `SQL SECURITY` and a session variable, or the app layer). SQLite none.

## 11. Dialect snapshot
| Feature | SQLite | Postgres | MySQL (InnoDB) | SQL Server |
|---|---|---|---|---|
| Views | yes (read-only) | yes, updatable | yes, updatable (simple) | yes, indexed views |
| Materialized views | no | yes (manual refresh) | no | indexed views |
| Sequences | no (rowid) | yes | no (AUTO_INCREMENT); MariaDB yes | yes |
| Triggers | row-level | row + statement | row-level | statement-level |
| Procedures | no | yes (11+) | yes | yes (T-SQL) |
| Roles/GRANT | no | yes | yes (8.0+ roles) | yes |
| RLS | no | yes | no | yes |
| Schemas | ATTACH | yes | = database | yes |

## Common mistakes
- Expecting a view to speed things up (it does not, unless materialized/indexed).
- Using `SELECT *` in a view: columns are frozen at creation in several engines.
- Relying on sequences for gapless invoice numbers.
- Triggers that update the same table recursively.
- Application connecting as the owner/superuser, making RLS and GRANT moot.
- Forgetting `ALTER DEFAULT PRIVILEGES`, so new tables are unreadable to the read-only role.

## Your task
1. `.read setup.sql`, then work through [practice.sql](practice.sql).
2. Answer [interview-qa.md](interview-qa.md) aloud before reading the model answers.
3. If you start Postgres via the Docker one-liner in the folder README, run every "not run here, verify" snippet and fix any syntax I got wrong for your version.
