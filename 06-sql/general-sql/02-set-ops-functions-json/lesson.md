# Part 02: Set operations, functions, pagination, lateral, pivot, JSON

Goal: combine result sets, use the dialect function zoo without panic, handle NULLs on purpose, paginate correctly, and read/write JSON from SQL.

Prerequisites: SELECT/WHERE/GROUP BY and NULL logic in [week-01 lesson](../../week-01-select-filter-aggregate/lesson.md); joins/subqueries in week-02; CTEs, window functions, CASE, dates in [week-03 lesson](../../week-03-cte-window-case-dates/lesson.md). This part does not repeat them.

Setup: `sqlite3 :memory: ".read setup.sql"` (or `sqlite3 part02.db < setup.sql`), then `.headers on` and `.mode column`.
All outputs below marked "Output" were produced by SQLite 3.54 in this repo. Snippets marked **(not run here, verify)** are Postgres/MySQL/SQL Server code that could not be executed in this environment (no `psql`/`mysql`). Version-dependent facts: check current docs.

Tables: `customers_2023`, `customers_2024` (id, name, email; Cy has NULL email), `products` (messy names, NULL discounts and notes), `sales`, `events` (JSON text payloads).

---

## 1. Set operations

Set operators stack the results of two SELECTs vertically. Rules: same number of columns, compatible types, column names come from the first query, and `ORDER BY` goes once at the very end.

| Operator | Result | Duplicates |
|---|---|---|
| `UNION` | rows in A or B | removed (needs sort/hash, slower) |
| `UNION ALL` | A followed by B | kept (fast, no dedup) |
| `INTERSECT` | rows in both | removed |
| `EXCEPT` | rows in A not in B | removed |

Dialect notes: Oracle calls EXCEPT `MINUS`. MySQL gained `INTERSECT` and `EXCEPT` only in 8.0.31 (check current docs). `INTERSECT ALL` / `EXCEPT ALL` exist in Postgres but not SQLite or SQL Server. Precedence: standard SQL makes INTERSECT bind tighter than UNION/EXCEPT; use parentheses to be safe (SQLite evaluates compound selects left to right, so parentheses-free mixes differ between engines).

```sql
SELECT name, email FROM customers_2023
UNION
SELECT name, email FROM customers_2024
ORDER BY name;
```
Output:
```
name    email
----  ---------
Ann   ann@x.com
Bob   bob@x.com
Cy
Di    di@x.com
Eve   eve@x.com
Fay   fay@x.com
```
Bob and Cy appear once. Note: set operators treat NULLs as equal to each other (two NULLs are "not distinct"), unlike `=`. That is why Cy collapsed even though `NULL = NULL` is not true.

```sql
SELECT COUNT(*) AS n FROM (SELECT id FROM customers_2023 UNION ALL SELECT id FROM customers_2024);   -- 8
SELECT id, name FROM customers_2023 INTERSECT SELECT id, name FROM customers_2024;                    -- 2 Bob, 3 Cy
SELECT id, name FROM customers_2023 EXCEPT    SELECT id, name FROM customers_2024;                    -- 1 Ann, 4 Di
```
Use `UNION ALL` by default; use `UNION` only when you need dedup. Reaching for UNION "just in case" costs a sort or hash over the whole result.

Alternatives: `INTERSECT` ~ `WHERE EXISTS`/inner join; `EXCEPT` ~ `NOT EXISTS`/anti-join (see week-02). Set operators compare entire rows with NULL-equal semantics, which is the main behavioural difference from `NOT IN` (which breaks on NULLs, see week-01).

---

## 2. Functions by dialect

You will not memorise these; know the categories and look up spelling. Table of the common ones:

| Task | SQLite | PostgreSQL | MySQL | SQL Server |
|---|---|---|---|---|
| Concatenate | `a \|\| b` | `a \|\| b`, `concat()` | `CONCAT(a,b)` (`\|\|` is OR unless `PIPES_AS_CONCAT`) | `a + b`, `CONCAT()` |
| Substring | `substr(s,i,n)` | `substr`, `substring(s from i for n)` | `SUBSTRING(s,i,n)` | `SUBSTRING(s,i,n)` |
| Position | `instr(s,x)` | `strpos(s,x)`, `position(x in s)` | `LOCATE(x,s)`, `INSTR(s,x)` | `CHARINDEX(x,s)` |
| Length | `length` | `length`, `char_length` | `CHAR_LENGTH` (`LENGTH` = bytes) | `LEN` (ignores trailing spaces) |
| Trim | `trim`, `ltrim`, `rtrim` | same | same | `TRIM` (2017+), `LTRIM`, `RTRIM` |
| Current time | `datetime('now')` | `now()`, `CURRENT_TIMESTAMP` | `NOW()` | `GETDATE()`, `SYSDATETIME()` |
| Truncate to month | `date(d,'start of month')` | `date_trunc('month', d)` | `DATE_FORMAT(d,'%Y-%m-01')` | `DATETRUNC` (new; check docs) or `DATEFROMPARTS` |
| Format | `strftime('%Y-%m', d)` | `to_char(d,'YYYY-MM')` | `DATE_FORMAT(d,'%Y-%m')` | `FORMAT(d,'yyyy-MM')` |
| Add interval | `date(d,'+1 month')` | `d + INTERVAL '1 month'` | `d + INTERVAL 1 MONTH` | `DATEADD(month,1,d)` |
| Difference | `julianday(a)-julianday(b)` | `a - b` (dates give integer days) | `DATEDIFF(a,b)` (days) | `DATEDIFF(day,b,a)` (note arg order) |
| Extract part | `strftime('%m',d)` | `EXTRACT(month FROM d)` | `EXTRACT`, `MONTH(d)` | `DATEPART`, `MONTH(d)` |
| Cast | `CAST(x AS INTEGER)` | `CAST` or `x::int` | `CAST`, `CONVERT` | `CAST`, `CONVERT`, `TRY_CAST` |
| Limit rows | `LIMIT n` | `LIMIT n` / `FETCH FIRST n ROWS ONLY` | `LIMIT n` | `TOP n` / `OFFSET..FETCH` |
| Conditional | `CASE`, `iif` | `CASE` | `CASE`, `IF()` | `CASE`, `IIF` |

Only the SQLite column was run here; the others are **(not run here, verify)** against the docs for your version.

### Strings (SQLite, run)
```sql
SELECT '['||TRIM(name)||']' AS t, UPPER(name) u, LENGTH(name) len,
       SUBSTR(TRIM(name),1,3) s3, INSTR(name,'g') pos, REPLACE(name,'e','E') r
FROM products;
```
Output:
```
      t             u       len  s3   pos       r
-------------  -----------  ---  ---  ---  -----------
[Widget]         WIDGET       9  Wid    6    WidgEt
[Gadget]       GADGET         6  Gad    4  GadgEt
[Doohickey]    DOOHICKEY      9  Doo    0  DoohickEy
[Thingamajig]  THINGAMAJIG   11  Thi    5  Thingamajig
[Whatsit]      WHATSIT        7  Wha    0  Whatsit
```
`INSTR` returns 0 when not found (1-based positions). Traps: SQL strings are 1-indexed; `||` with a NULL yields NULL in standard SQL (Postgres `concat()` and MySQL `CONCAT_WS` treat NULL differently, check docs); `LIKE` case sensitivity differs (SQLite: ASCII case-insensitive by default, Postgres: case-sensitive, use `ILIKE`; MySQL depends on collation).

### Dates (SQLite, run)
```sql
SELECT sold_on, strftime('%Y-%m',sold_on) ym, date(sold_on,'start of month') som,
       date(sold_on,'+1 month') nxt,
       CAST(julianday('2024-04-10')-julianday(sold_on) AS INT) days_ago
FROM sales LIMIT 3;
```
Output:
```
 sold_on      ym        som         nxt      days_ago
----------  -------  ----------  ----------  --------
2024-01-05  2024-01  2024-01-01  2024-02-05        96
2024-01-20  2024-01  2024-01-01  2024-02-20        81
2024-01-25  2024-01  2024-01-01  2024-02-25        76
```
SQLite has no date type: dates are TEXT/REAL/INTEGER, and ISO-8601 text sorts correctly. Postgres/MySQL/SQL Server have real `DATE`/`TIMESTAMP` types. Also remember time zones: Postgres `timestamptz` stores UTC and renders in session zone; MySQL `TIMESTAMP` converts, `DATETIME` does not. Month end idiom: `date(d,'start of month','+1 month','-1 day')`; Postgres: `(date_trunc('month', d) + INTERVAL '1 month - 1 day')::date` **(not run here, verify)**; SQL Server: `EOMONTH(d)`; MySQL: `LAST_DAY(d)`.

### Numbers (SQLite, run)
```sql
SELECT 7/2, 7/2.0, 7%3, ROUND(2.5), ROUND(3.14159,2), ABS(-4), CAST('12' AS INTEGER);
```
Output:
```
7/2  7/2.0  7%3  ROUND(2.5)  ROUND(3.14159,2)  ABS(-4)  CAST('12' AS INTEGER)
---  -----  ---  ----------  ----------------  -------  ---------------------
  3    3.5    1         3.0              3.14        4                     12
```
`7/2` is 3 in SQLite, Postgres and SQL Server (integer division); MySQL's `/` returns a decimal 3.5000 and `DIV` is integer division. `ROUND(2.5)`: SQLite rounds half away from zero (3.0); Postgres `round(numeric)` does too but `round(double precision)` uses banker-like round-half-even on many platforms; check docs. Never use floating point for money: use `NUMERIC`/`DECIMAL` or integer cents.

---

## 3. NULL-safe operations, COALESCE, NULLIF

NULL basics are in week-01. What matters here is the comparison toolbox:

| Need | Standard | SQLite | Postgres | MySQL |
|---|---|---|---|---|
| NULL-safe equal | `a IS NOT DISTINCT FROM b` | `a IS b` | `IS NOT DISTINCT FROM` | `a <=> b` |
| NULL-safe not equal | `a IS DISTINCT FROM b` | `a IS NOT b` | `IS DISTINCT FROM` | `NOT (a <=> b)` |

SQLite 3.39+ also supports `IS [NOT] DISTINCT FROM` (check current docs for your build). SQL Server 2022 added `IS [NOT] DISTINCT FROM` as well; older versions need `(a = b OR (a IS NULL AND b IS NULL))`.

```sql
SELECT 1 WHERE NULL = NULL;                       -- no rows
SELECT 'is' AS r WHERE NULL IS NULL;              -- is
SELECT a.id, b.id FROM customers_2023 a JOIN customers_2024 b ON a.email IS b.email;
```
Output of the join: `2|2` and `3|3` (Cy matches Cy only because of the NULL-safe `IS`; with `=` row 3 would vanish).

`COALESCE(a,b,c)` returns the first non-NULL (standard; also `IFNULL`/`NVL`/`ISNULL` in vendor dialects, which take only two args). `NULLIF(a,b)` returns NULL if a = b else a: classic use is converting sentinel values to NULL, and avoiding division by zero with `x / NULLIF(y,0)`.

```sql
SELECT id, price, discount,
       COALESCE(discount,0) AS d,
       ROUND(price*(1-COALESCE(discount,0)),2) AS final,
       NULLIF(note,'') AS note2
FROM products;
```
Output:
```
id  price  discount   d    final  note2
--  -----  --------  ----  -----  -----
 1   9.99               0   9.99  basic
 2   24.5       0.1   0.1  22.05
 3    5.0       0.0   0.0    5.0
 4  12.75      0.25  0.25   9.56  sale
 5    7.2               0    7.2
```
(Blank cells are NULL.) Pitfall: `COALESCE` in an aggregate: `AVG(COALESCE(x,0))` is not `AVG(x)`: it counts the NULL rows as zeros. Decide which you mean.

---

## 4. Pagination: OFFSET vs keyset

### OFFSET
```sql
SELECT id, sold_on FROM sales ORDER BY id LIMIT 3 OFFSET 3;   -- page 2, size 3
```
Output: rows with id 4, 5, 6.
Dialects: `LIMIT n OFFSET m` (Postgres, MySQL, SQLite); standard `OFFSET m ROWS FETCH NEXT n ROWS ONLY` (Postgres, SQL Server 2012+, Oracle 12c+; SQL Server requires an ORDER BY). Problems:
1. Cost grows with depth: the database still produces and discards the first `m` rows. Page 10,000 is slow.
2. Unstable under writes: an insert/delete on an earlier page shifts rows, so users see duplicates or skip rows.
3. Without a deterministic ORDER BY (add a unique tiebreaker like `id`), pages can overlap.

### Keyset (a.k.a. seek, cursor) pagination
Remember the last row's sort key and ask for "rows after it".
```sql
SELECT id, sold_on FROM sales WHERE id > 6 ORDER BY id LIMIT 3;
```
Output: ids 7, 8, 9. For a non-unique sort column, use a row-value comparison with a unique tiebreaker:
```sql
SELECT id, sold_on FROM sales
WHERE (sold_on, id) > ('2024-02-20', 6)
ORDER BY sold_on, id LIMIT 3;
```
Output: ids 7, 8, 9 (sold_on 2024-03-01, 03-09, 03-15). Row-value comparison works in SQLite 3.15+, Postgres, MySQL (index use may be poor in older MySQL, check docs); SQL Server lacks it, so expand: `sold_on > @s OR (sold_on = @s AND id > @id)`.
With an index on `(sold_on, id)` this is an index range seek: constant cost per page. Trade-offs: no "jump to page 50", needs a stable total order, descending/mixed order needs care, and NULLs in the sort key complicate the comparison. Good for infinite scroll and APIs; OFFSET is acceptable for small admin tables. Index background: [week-04](../../week-04-schema-indexes-transactions/lesson.md) section 4.

---

## 5. LATERAL / CROSS APPLY

A normal subquery in FROM cannot reference columns of earlier FROM items. A **lateral** subquery can, and runs once per outer row: "for each row, run this correlated query and join its rows". The canonical use is top-N-per-group.

| Dialect | Syntax |
|---|---|
| PostgreSQL, MySQL 8.0.14+ (check docs), Oracle 12c+ | `... CROSS JOIN LATERAL (subquery) x` / `LEFT JOIN LATERAL (...) x ON TRUE` |
| SQL Server, Oracle | `CROSS APPLY (subquery) x` / `OUTER APPLY` |
| SQLite | not supported: use window functions |

Latest 2 sales per product with LATERAL **(not run here, verify)**:
```sql
SELECT p.id, s.id AS sale_id, s.sold_on
FROM products p
LEFT JOIN LATERAL (
    SELECT id, sold_on FROM sales
    WHERE product_id = p.id
    ORDER BY sold_on DESC, id DESC
    LIMIT 2
) s ON TRUE;
```
SQL Server version **(not run here, verify)**: `CROSS APPLY (SELECT TOP 2 id, sold_on FROM sales WHERE product_id = p.id ORDER BY sold_on DESC, id DESC) s`.

Portable alternative (week-03 windows), run on SQLite:
```sql
SELECT * FROM (
  SELECT product_id, sold_on, qty,
         ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY sold_on DESC) rn
  FROM sales) WHERE rn <= 1 ORDER BY product_id;
```
Output:
```
product_id   sold_on    qty  rn
----------  ----------  ---  --
         1  2024-04-02    1   1
         2  2024-03-30    2   1
         3  2024-03-09    1   1
         4  2024-03-15    3   1
         5  2024-03-31    6   1
```
LATERAL wins when the per-row subquery can use an index to stop early (top-N with `LIMIT`) and when you call a set-returning function per row (`LATERAL unnest(...)`, `json_each`). The window version scans every row first. `LEFT JOIN LATERAL ... ON TRUE` / `OUTER APPLY` keeps outer rows with no matches.

---

## 6. Pivot and unpivot idioms

Pivot = rows to columns. Portable idiom: conditional aggregation (works everywhere).
```sql
SELECT p.category,
  SUM(CASE WHEN s.region='N' THEN s.qty ELSE 0 END) AS north,
  SUM(CASE WHEN s.region='S' THEN s.qty ELSE 0 END) AS south
FROM sales s JOIN products p ON p.id = s.product_id
GROUP BY p.category ORDER BY 1;
```
Output:
```
category  north  south
--------  -----  -----
garden        6      0
tools        13      5
toys          1     15
```
Limits: the column list is fixed at write time. Dynamic columns need dynamic SQL (build the string, then execute) in every dialect. Native alternatives: SQL Server and Oracle have `PIVOT`/`UNPIVOT` operators; Postgres has `crosstab()` in the `tablefunc` extension and `FILTER`: `SUM(qty) FILTER (WHERE region='N')` **(not run here, verify)**; MySQL has neither (use CASE); Snowflake/BigQuery have `PIVOT`/`UNPIVOT` (check docs).

Unpivot = columns to rows. Portable idiom: `UNION ALL` one SELECT per column:
```sql
WITH t(category,north,south) AS (VALUES ('garden',6,0),('tools',13,5),('toys',1,15))
SELECT category,'north' AS region, north AS qty FROM t
UNION ALL SELECT category,'south',south FROM t ORDER BY 1,2;
```
Output:
```
category  region  qty
--------  ------  ---
garden    north     6
garden    south     0
tools     north    13
tools     south     5
toys      north     1
toys      south    15
```
Postgres alternative: `CROSS JOIN LATERAL (VALUES ('north', t.north), ('south', t.south)) v(region, qty)`; SQL Server: `CROSS APPLY (VALUES (...)) v(...)` **(not run here, verify)**. If you find yourself unpivoting often, the table is probably modelled wrong (repeating columns, see normalization in week-04).

---

## 7. JSON in SQL

Relational databases now store semi-structured data, but JSON is not a free pass: you lose type checks, foreign keys and easy indexing. Rule of thumb: columns for anything you filter, join or constrain on; JSON for sparse, vendor-defined or rarely queried attributes.

| | SQLite (json1) | PostgreSQL | MySQL |
|---|---|---|---|
| Types | none; TEXT (3.45+ also has JSONB-like binary internally, check docs) | `json` (text, preserves formatting), `jsonb` (binary, indexable; prefer it) | `JSON` (binary, validated) |
| Get as JSON | `->` | `->` | `->` (alias for `JSON_EXTRACT`) |
| Get as text | `->>` | `->>` | `->>` (unquotes) |
| Path | `'$.a.b[0]'` | `payload->'a'->'b'`, or `#>'{a,b}'`, or `jsonb_path_query` | `'$.a.b[0]'` |
| Expand array | `json_each`, `json_tree` | `jsonb_array_elements`, `jsonb_each` | `JSON_TABLE` (8.0+) |
| Build | `json_object`, `json_array`, `json_group_array` | `jsonb_build_object`, `jsonb_agg` | `JSON_OBJECT`, `JSON_ARRAYAGG` |
| Modify | `json_set`, `json_insert`, `json_remove` | `jsonb_set`, `\|\|`, `-` | `JSON_SET`, `JSON_REMOVE` |
| Contains | (use `json_each`) | `@>`, `?` | `JSON_CONTAINS`, `MEMBER OF` |
| Index | expression index on `json_extract(...)` | GIN on the column (`jsonb_path_ops`), btree on expression | functional index or generated column + index |

### SQLite (run)
```sql
SELECT id, json_extract(payload,'$.user') u, payload->>'$.meta.ip' ip, payload->'$.meta.tags' tags
FROM events;
```
Output:
```
id   u     ip         tags
--  ---  -------  -------------
 1  ann  1.1.1.1  ["web","mfa"]
 2  bob  2.2.2.2  ["mobile"]
 3  ann  1.1.1.1  []
 4  cy
```
`->` returns JSON text; `->>` returns a SQL value. Missing paths and JSON `null` both become SQL NULL (row 4), which hides the difference between "key absent" and "key is null": use `json_type(payload,'$.meta')` (returns `'null'` for JSON null, SQL NULL if absent).

Filter on a JSON field:
```sql
SELECT id, json_extract(payload,'$.amount') amt FROM events
WHERE json_extract(payload,'$.action')='buy';
```
Output: `2|19.5` and `3|5`.

Expand an array into rows:
```sql
SELECT e.id, j.value AS tag FROM events e, json_each(e.payload,'$.meta.tags') j;
```
Output: `1|web`, `1|mfa`, `2|mobile` (row 3 has an empty array and row 4 has null meta, so they produce no rows; use `LEFT JOIN` form to keep them).

Build JSON:
```sql
SELECT json_object('a',1,'b',json_array(1,2,3)) AS o;               -- {"a":1,"b":[1,2,3]}
SELECT json_group_array(DISTINCT json_extract(payload,'$.user')) FROM events;  -- ["ann","bob","cy"]
SELECT json_set('{"a":1}','$.b',2);                                  -- {"a":1,"b":2}
```

### PostgreSQL **(not run here, verify)**
```sql
CREATE TABLE events (id bigserial PRIMARY KEY, payload jsonb NOT NULL);
SELECT payload->>'user' AS usr, (payload->>'amount')::numeric AS amt
FROM events WHERE payload @> '{"action":"buy"}';          -- containment, can use a GIN index
SELECT e.id, t.tag FROM events e, jsonb_array_elements_text(e.payload->'meta'->'tags') AS t(tag);
CREATE INDEX events_payload_gin ON events USING gin (payload jsonb_path_ops);
CREATE INDEX events_user_idx    ON events ((payload->>'user'));   -- btree on one key
UPDATE events SET payload = jsonb_set(payload, '{meta,ip}', '"9.9.9.9"') WHERE id = 1;
```
Careful: `payload->'user'` gives jsonb (quoted), `->>` gives text. `json` keeps duplicates and key order; `jsonb` dedupes and reorders. SQL/JSON path (`jsonb_path_query`, `@?`) arrives in 12+, `JSON_TABLE` and more SQL/JSON in newer versions (check current docs).

### MySQL **(not run here, verify)**
```sql
CREATE TABLE events (id BIGINT AUTO_INCREMENT PRIMARY KEY, payload JSON NOT NULL);
SELECT payload->>'$.user' AS usr FROM events WHERE JSON_EXTRACT(payload,'$.action') = 'buy';
-- JSON cannot be indexed directly; index a generated column:
ALTER TABLE events ADD COLUMN usr VARCHAR(50) AS (payload->>'$.user') STORED, ADD INDEX (usr);
SELECT jt.tag FROM events, JSON_TABLE(payload,'$.meta.tags[*]' COLUMNS (tag VARCHAR(20) PATH '$')) jt;
```
Note `->` in MySQL returns a quoted JSON value, so comparing `payload->'$.user' = 'ann'` fails; use `->>`. Newer versions allow functional indexes and multi-valued indexes (check docs).

### SQL Server
No native JSON type in older versions (JSON stored in `NVARCHAR`, queried with `JSON_VALUE`, `JSON_QUERY`, `OPENJSON`); a native `json` type is newer (check current docs). Warehouses: Snowflake `VARIANT` with `col:path::type` and `FLATTEN`; BigQuery `JSON` with `JSON_VALUE`; check docs.

When not to use JSON: when you need referential integrity, when the same keys appear on every row (make them columns), or when you aggregate on a key constantly (add a generated/typed column).

---

## Common mistakes
- Using `UNION` where `UNION ALL` was meant (silent row loss and slowness).
- `ORDER BY` inside the first branch of a UNION, or trusting sort order of a subquery.
- Mismatched column order between UNION branches: matching is by position, not name.
- `NOT IN (subquery)` with a NULL in the list returns nothing: use `NOT EXISTS` or `EXCEPT`.
- Paginating without a unique tiebreaker in ORDER BY.
- Comparing `JSON ->` output to a plain string (works in SQLite `->>`, not MySQL `->`).
- Assuming `/`, `ROUND`, `LIKE` and string concat behave identically across engines.

## Your task
1. Create the DB and work through [practice.sql](practice.sql) (21 tasks); reference solutions are deliberately not in the repo.
2. Rewrite two practice answers for Postgres or MySQL in comments, using the table above and docs.
3. Do [interview-qa.md](interview-qa.md) aloud.
