# Part 06: Engines, warehouses, and data modeling

Goal: know how the major systems differ, why analytics databases are built differently from transactional ones, and how to model data for reporting.
Builds on: [week-04 lesson](../../week-04-schema-indexes-transactions/lesson.md) (section 7 touches OLTP vs OLAP; section "SQLite vs Postgres vs MySQL cheat table"). This part goes wider and deeper; it does not repeat those.
Practice: `sqlite3 :memory: ".read setup.sql" ".read practice.sql"` (see [README](../README.md)).

Version-dependent facts below are marked "check current docs". Snippets for non-SQLite systems are "not run here, verify".

## 1. The systems at a glance

| | PostgreSQL | MySQL (InnoDB) | SQLite | SQL Server | BigQuery | Snowflake | Redshift |
|---|---|---|---|---|---|---|---|
| Kind | OLTP, general purpose, extensible | OLTP, web workloads | Embedded, in-process library | OLTP + some analytics (columnstore) | Serverless warehouse | Cloud warehouse | Cloud warehouse (Postgres-derived) |
| Deployment | Server you run or managed (RDS, Cloud SQL...) | Same | A file; no server | Server / Azure SQL | Fully managed (Google) | Fully managed, compute (warehouses) separate from storage | Managed clusters or serverless |
| Storage layout | Row (heap) | Row (clustered B-tree on PK) | Row (B-tree) | Row; optional columnstore indexes | Columnar (Capacitor) | Columnar micro-partitions | Columnar |
| Concurrency | MVCC, readers do not block writers | MVCC (undo log) | One writer at a time (WAL mode allows readers during a write) | Locking by default; snapshot/RCSI optional | Not row-level OLTP; DML is batch-oriented | Same: not for high-rate single-row writes | Same |
| Enforced constraints | All (PK, FK, UNIQUE, CHECK) | All (CHECK since 8.0.16, check current docs) | Yes, FKs need `PRAGMA foreign_keys=ON` | All | PK/FK are informational only (not enforced) | PK/FK/UNIQUE declared but not enforced (NOT NULL is) | Same: informational |
| Indexes | B-tree, hash, GIN, GiST, BRIN... | B-tree (+ full-text, spatial) | B-tree | B-tree, columnstore | None in the classic sense (partition + cluster instead) | None (micro-partition pruning, clustering keys) | Sort keys / dist keys, no B-tree |
| Typical scale sweet spot | GB to low TB per node | Same | MB to GB, single app | Same as Postgres | TB to PB | TB to PB | TB to PB |
| Procedural language | PL/pgSQL (+ others) | Stored procs (own dialect) | None (triggers only) | T-SQL | Scripting, UDFs | Snowflake Scripting, JS UDFs | PL/pgSQL-like stored procs |
| Notable quirks | Strict typing, rich types (JSONB, arrays, ranges) | Silent coercions unless strict `sql_mode` | Dynamic typing ("type affinity") | `TOP`, `[brackets]`, `GO` batch separator | Billed by bytes scanned (on-demand); nested/repeated fields | Time Travel, zero-copy clone | Distribution style matters a lot |

Treat the table as orientation. Features change; check current docs before you rely on a specific one.

When to pick what (rule of thumb):
- App backend, transactions, many small reads/writes: Postgres or MySQL (or SQL Server in a Microsoft shop).
- Local tool, mobile, tests, config store, single-user data: SQLite.
- Reporting over hundreds of millions of rows, scans and aggregates: a warehouse (or a columnar engine).
- Both: keep the OLTP database as the system of record and copy data into a warehouse (ELT).

## 2. OLTP vs OLAP

| | OLTP | OLAP |
|---|---|---|
| Typical query | "Get order 4711", "insert a payment" | "Revenue by region by month for 3 years" |
| Rows touched per query | A handful | Millions to billions |
| Columns touched | Most of the row | A few columns of many |
| Concurrency | Thousands of short transactions | Few, long queries |
| Schema | Normalized (3NF) | Denormalized (star/snowflake) |
| Data freshness | Real time | Seconds to hours behind |
| Optimizes | Latency, correctness under concurrency | Throughput of scans |

Mixed workloads on one OLTP box hurt: a big scan evicts cache and holds old row versions. Common fixes: read replica for reports, or a separate warehouse. HTAP engines try to do both in one system; check current docs for any specific product's maturity.

## 3. Columnar storage

Row store: all columns of a row sit together on a page. Good for "fetch whole row".
Column store: each column is stored separately.

```
Row store page:     [id1,name1,amt1] [id2,name2,amt2] [id3,name3,amt3]
Column store:       ids:[id1,id2,id3]  names:[...]  amts:[amt1,amt2,amt3]
```

Why analytics likes it:
1. `SELECT SUM(amount) FROM sales` reads only the `amount` column: far less I/O.
2. Values of one column are similar, so they compress very well (run-length, dictionary, delta encoding).
3. Vectorized execution: process thousands of values per CPU instruction batch.
4. Min/max metadata per block lets the engine skip blocks that cannot match (zone maps / pruning).

Why it is bad for OLTP: updating one row touches many column files; single-row lookups reassemble a row from many places. Warehouses therefore favour bulk loads and append-mostly data.

Consequences you will notice as a user:
- `SELECT *` is expensive in a warehouse (BigQuery on-demand bills by columns scanned; check current docs on pricing).
- Single-row `UPDATE`/`DELETE` are slow relative to OLTP.
- No B-tree indexes; instead you choose partitioning and clustering/sort keys.

## 4. Partitioning

Splitting one logical table into pieces so queries can skip the pieces they do not need (partition pruning), and so old data can be dropped cheaply.

| Kind | How rows are assigned | Typical use |
|---|---|---|
| Range | By value range (date) | Time series; drop old months |
| List | By explicit values (region) | Tenant/region isolation |
| Hash | `hash(key) mod N` | Even spread, no natural range |

Postgres (declarative partitioning; not run here, verify):
```sql
CREATE TABLE events (
  id bigint GENERATED ALWAYS AS IDENTITY,
  created_at timestamptz NOT NULL,
  payload jsonb
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_01 PARTITION OF events
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```
MySQL: `PARTITION BY RANGE (YEAR(created_at)) (...)`; the partition key must be part of every unique key (check current docs).
Warehouses: BigQuery `PARTITION BY DATE(created_at)` plus `CLUSTER BY customer_id`; Snowflake auto-partitions into micro-partitions and you may define a clustering key; Redshift uses `DISTKEY`/`SORTKEY` (not run here, verify).

Pitfalls:
- A query must filter on the partition key to benefit. `WHERE created_at >= '2024-01-01'` prunes; `WHERE DATE_FORMAT(created_at,...)` or a cast can defeat pruning.
- Too many tiny partitions cost planning time and metadata.
- Partitioning is not sharding. Partitions live in one database; sharding spreads data across servers and pushes joins/transactions into your application.
- Partitioning rarely speeds up OLTP point lookups that an index already serves; its main wins are pruning scans and cheap data retention (`DROP PARTITION` vs a huge `DELETE`).

## 5. Data modeling for analytics

### 5.1 Star schema
One central fact table (events/measurements, many rows, numeric measures + foreign keys) surrounded by dimension tables (descriptive attributes, fewer rows).

```
            dim_date
               |
dim_product - fact_sales - dim_customer
```
- Fact grain: state it in one sentence ("one row per product per order line"). Everything else follows from the grain.
- Dimensions are denormalized (category lives in `dim_product`, not in a separate table). Snowflake schema is the normalized variant (dimension split into sub-tables): less redundancy, more joins.
- Use surrogate keys (integers) in dimensions, keep the business key as a plain column.
- Additive measures (amount, quantity) can be summed across any dimension; semi-additive (balances) not across time; non-additive (ratios) never: store numerator and denominator instead.

Run against `setup.sql`:
```sql
SELECT p.category, d.quarter, SUM(f.amount) AS revenue
FROM fact_sales f
JOIN dim_product p USING (product_key)
JOIN dim_date    d USING (date_key)
GROUP BY p.category, d.quarter
ORDER BY p.category, d.quarter;
```
Real output:
```
 category    quarter  revenue
-----------  -------  -------
Displays           1    900.0
Displays           2    310.0
Furniture          1    250.0
Furniture          3    500.0
Peripherals        1    160.0
Peripherals        2     50.0
Peripherals        3    100.0
```
"Which products never sold" needs an anti-join from the dimension side (a fact-side join cannot show missing rows). See week-02 for anti-join forms.
```sql
SELECT p.name FROM dim_product p
LEFT JOIN fact_sales f USING (product_key)
WHERE f.sale_id IS NULL;
```
Output: `Chair`.

Other terms: degenerate dimension (order number kept on the fact), junk dimension (bundle low-cardinality flags), conformed dimension (same `dim_date` shared by many facts), factless fact table (records that an event happened, no measure).

### 5.2 Slowly Changing Dimensions (SCD)
A customer moves city. Should old sales still show the old city?

| Type | What it does | History kept? | Use when |
|---|---|---|---|
| 0 | Never changes (original value retained) | n/a | Birth date, original signup channel |
| 1 | Overwrite in place | No | Corrections, typos, history does not matter |
| 2 | Add a new row per version with validity range | Full | Reports must reflect the attribute as it was then |
| 3 | Extra column for previous value (`prev_city`) | Only one prior | Need "before and after" for a single change |
| 4/6 | Separate history table / hybrid of 1+2+3 | Varies | Advanced; check Kimball references |

SCD2 design: surrogate key per version, business key repeated, `valid_from`, `valid_to` (use `9999-12-31` rather than NULL so range predicates stay simple), optional `is_current`. Facts store the surrogate key of the version that was current when the fact happened, so history joins "just work".

Runnable SQLite example (tables in `setup.sql`: `dim_customer_scd2` and a change feed `stg_customer`).

Before: Asha has two versions, Ben one. Feed says: Asha moved to Bengaluru, Ben unchanged, Esha is new.
```sql
-- step 1: close the current row of customers whose attributes changed
UPDATE dim_customer_scd2
SET valid_to = '2024-09-01', is_current = 0
WHERE is_current = 1
  AND customer_id IN (
    SELECT s.customer_id FROM stg_customer s
    JOIN dim_customer_scd2 d ON d.customer_id = s.customer_id AND d.is_current = 1
    WHERE s.name <> d.name OR s.city <> d.city);

-- step 2: insert a new current row for every customer without a current row
INSERT INTO dim_customer_scd2 (customer_id, name, city, valid_from)
SELECT s.customer_id, s.name, s.city, '2024-09-01'
FROM stg_customer s
WHERE NOT EXISTS (SELECT 1 FROM dim_customer_scd2 d
                  WHERE d.customer_id = s.customer_id AND d.is_current = 1);
```
Real output of `SELECT * FROM dim_customer_scd2 ORDER BY customer_id, valid_from`:
```
customer_sk  customer_id  name    city     valid_from   valid_to   is_current
-----------  -----------  ----  ---------  ----------  ----------  ----------
          1  C001         Asha  Pune       2023-01-01  2024-03-01           0
          2  C001         Asha  Mumbai     2024-03-01  2024-09-01           0
          4  C001         Asha  Bengaluru  2024-09-01  9999-12-31           1
          3  C002         Ben   Delhi      2023-06-01  9999-12-31           1
          5  C005         Esha  Chennai    2024-09-01  9999-12-31           1
```
Point-in-time lookup (as of 2024-02-01) uses a half-open range `valid_from <= d AND d < valid_to` so adjacent versions never both match:
```sql
SELECT customer_id, city FROM dim_customer_scd2
WHERE '2024-02-01' >= valid_from AND '2024-02-01' < valid_to ORDER BY 1;
-- C001 Pune, C002 Delhi
```
Order matters: close first, then insert; otherwise the NOT EXISTS check sees the old current row and inserts nothing. Run the pair inside one transaction. In Postgres/SQL Server/Snowflake the same logic is often written with `MERGE` (see [part 01](../01-language-map-ddl-dml/lesson.md)), not run here, verify.

Late-arriving or backdated changes make SCD2 harder (you must split an existing validity range). Mention that in interviews.

### 5.3 ETL vs ELT, and other modeling styles
- ETL: transform before loading (older, on-prem). ELT: load raw data into the warehouse, transform with SQL there (dbt-style). Cheap warehouse compute made ELT dominant.
- Wide denormalized "one big table" is common in columnar warehouses because joins are costlier than scanning extra columns, at the price of redundancy.
- Data Vault (hubs, links, satellites) targets auditability and many sources; heavier to query.
- Kimball (star schemas, bottom-up) vs Inmon (normalized enterprise warehouse first): know the names.

## 6. Dialect traps when moving between engines
- Warehouse "constraints" you declare may not be enforced: duplicates can enter silently. Deduplicate in the pipeline (e.g. `ROW_NUMBER() OVER (PARTITION BY key ORDER BY loaded_at DESC) = 1`).
- Case/quoting: Postgres folds unquoted identifiers to lower case, Snowflake to upper case, SQL Server depends on collation.
- Integer division, string concatenation, date arithmetic all differ: see [cheatsheet](../cheatsheet.md).

## Common mistakes
- Modeling a warehouse like a 3NF OLTP schema (too many joins) or an OLTP app like one wide table (update anomalies).
- No stated grain, so a fact table mixes order-level and line-level amounts and sums double count.
- Joining facts to an SCD2 dimension on the business key without a date condition: row fan-out and double counting.
- Partitioning on a column nobody filters on.
- Using `SELECT *` on columnar engines.

## Your task
1. Run `sqlite3 :memory: ".read setup.sql" ".read practice.sql"` after filling in practice.sql.
2. Draw the star schema for an e-commerce domain you know; state its grain.
3. Answer [interview-qa.md](interview-qa.md) out loud, then try [rapid-fire.md](../rapid-fire.md).
