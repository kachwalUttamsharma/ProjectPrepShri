# Dialect differences cheatsheet

Rows marked * not run here, verify. Version-dependent: check current docs. Short names: PG = PostgreSQL, MY = MySQL, SL = SQLite, MS = SQL Server, BQ = BigQuery, SF = Snowflake.

| Topic | PG | MY | SL | MS | BQ | SF |
|---|---|---|---|---|---|---|
| Limit rows | `LIMIT n OFFSET m` | same | same | `TOP n`; `OFFSET m ROWS FETCH NEXT n ROWS ONLY` | `LIMIT n OFFSET m` | `LIMIT n OFFSET m` (also `TOP`, `FETCH`) |
| Standard FETCH | `FETCH FIRST n ROWS ONLY` | no (8.x; check) | no | yes (needs ORDER BY) | no | yes |
| String concat | `a \|\| b`, `concat()` | `CONCAT(a,b)` (`\|\|` is OR by default) | `a \|\| b` | `a + b`, `CONCAT()` | `a \|\| b`, `CONCAT()` | `a \|\| b`, `CONCAT()` |
| Quote identifier | `"x"` | `` `x` `` (or `"` with ANSI_QUOTES) | `"x"` (also `[x]`, `` `x` ``) | `[x]` or `"x"` | `` `x` `` | `"x"` |
| String literal | `'x'` | `'x'` (also `"x"`) | `'x'` | `'x'` | `'x'` or `"x"` | `'x'` |
| Unquoted case | folds to lower | table names OS-dependent | case-insensitive | collation-dependent | case-sensitive for tables | folds to UPPER |
| Auto-increment | `GENERATED ... AS IDENTITY`, `SERIAL` | `AUTO_INCREMENT` | `INTEGER PRIMARY KEY` (rowid), `AUTOINCREMENT` | `IDENTITY(1,1)` | none enforced; `GENERATE_UUID()` | `AUTOINCREMENT`/`IDENTITY` |
| Upsert | `ON CONFLICT DO UPDATE` | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT DO UPDATE` | `MERGE` | `MERGE` | `MERGE` |
| RETURNING rows | `RETURNING` | not supported | `RETURNING` (3.35+) | `OUTPUT` | no | no |
| Boolean | real `boolean` | `TINYINT(1)`/`BOOL` | integers 0/1 (`TRUE` alias) | `BIT` | `BOOL` | `BOOLEAN` |
| Case-insens. LIKE | `ILIKE` | default collation is often ci | `LIKE` is ci for ASCII | collation-dependent | `LOWER()` + `LIKE` | `ILIKE` |
| Current time | `now()`, `CURRENT_TIMESTAMP` | `NOW()` | `CURRENT_TIMESTAMP` | `GETDATE()`, `SYSDATETIME()` | `CURRENT_TIMESTAMP()` | `CURRENT_TIMESTAMP()` |
| Add days | `d + INTERVAL '7 days'` | `DATE_ADD(d, INTERVAL 7 DAY)` | `date(d,'+7 days')` | `DATEADD(day,7,d)` | `DATE_ADD(d, INTERVAL 7 DAY)` | `DATEADD(day,7,d)` |
| Date diff (days) | `d2 - d1` (dates) | `DATEDIFF(d2,d1)` | `julianday(d2)-julianday(d1)` | `DATEDIFF(day,d1,d2)` | `DATE_DIFF(d2,d1,DAY)` | `DATEDIFF(day,d1,d2)` |
| Truncate to month | `date_trunc('month',d)` | `DATE_FORMAT(d,'%Y-%m-01')` | `date(d,'start of month')` | `DATETRUNC` (2022+) / `EOMONTH` tricks | `DATE_TRUNC(d, MONTH)` | `DATE_TRUNC('month',d)` |
| Integer division | `7/2 = 3` | `7/2 = 3.5000`; `DIV` for int | `7/2 = 3` | `7/2 = 3` | `7/2 = 3.5`; `DIV()` | `7/2 = 3.5` (check) |
| NULL-safe equal | `IS NOT DISTINCT FROM` | `<=>` | `IS` | `IS NOT DISTINCT FROM` (2022+) | `IS NOT DISTINCT FROM` | `IS NOT DISTINCT FROM`, `EQUAL_NULL` |
| Cast | `x::int`, `CAST` | `CAST`, `CONVERT` | `CAST` | `CAST`, `CONVERT`, `TRY_CAST` | `CAST`, `SAFE_CAST` | `::`, `CAST`, `TRY_CAST` |
| JSON | `jsonb`, `->`, `->>` | `JSON`, `->`, `->>` | `json_extract`, `->`/`->>` (3.38+) | `JSON_VALUE`, `OPENJSON` | `JSON_VALUE`, native `JSON` | `VARIANT`, `col:key` |
| Procedural | PL/pgSQL | stored proc/func | none | T-SQL | scripting | Snowflake Scripting |
| Transactional DDL | yes | no (implicit commit) | yes | yes | limited | limited |
| Group concat | `string_agg(x, ',')` | `GROUP_CONCAT(x)` | `group_concat(x)` | `STRING_AGG` (2017+) | `STRING_AGG` | `LISTAGG` |

Verified in SQLite 3.54 here: `SELECT 7/2, 7/2.0, 'a'||'b', date('2024-01-31','+7 days')` gives `3 | 3.5 | ab | 2024-02-07`. Every other column: not run here, verify against current docs.

Habits that travel: use `CAST` and `COALESCE`, `CASE`, `CURRENT_TIMESTAMP`, `FETCH FIRST` or `LIMIT` consciously, quote nothing unless forced, name columns explicitly, and keep dialect-specific SQL in one layer.
