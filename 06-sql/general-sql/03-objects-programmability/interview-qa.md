# Part 03 interview Q&A: objects and programmability

Say the short answer first, then add the trade-off.

**1. What is a view and does it store data?**
A named, stored SELECT. An ordinary view stores no rows; the query is expanded at run time. It gives abstraction and access control, not speed.

**2. View vs materialized view?**
A materialized view stores its result and must be refreshed, so reads are fast but possibly stale. Postgres: `REFRESH MATERIALIZED VIEW [CONCURRENTLY]` (concurrent refresh needs a unique index). MySQL and SQLite lack them (use summary tables); SQL Server has indexed views maintained automatically.

**3. Can you INSERT/UPDATE through a view?**
Simple single-table views are auto-updatable in Postgres and MySQL. Views with aggregates, DISTINCT, GROUP BY or multiple tables are not, unless you add `INSTEAD OF` triggers. `WITH CHECK OPTION` prevents writes that fall outside the view's WHERE.

**4. Why use a view for security?**
Grant access on the view, not the table, to expose only certain columns/rows. In Postgres beware leaks via functions in user queries (`security_barrier`); check current docs.

**5. AUTO_INCREMENT vs sequence vs identity vs UUID?**
AUTO_INCREMENT is a per-table MySQL counter. A sequence is a standalone counter object (Postgres, Oracle, SQL Server). Identity columns are the SQL-standard syntax over a sequence. UUIDs are generated anywhere, globally unique, bigger, and random ones hurt index locality (especially a clustered PK in InnoDB); time-ordered UUIDs help.

**6. Why do sequences have gaps?**
They are non-transactional for concurrency: a rolled-back or failed insert consumes the number, as do crashes and caching. Do not use them for legally gapless numbering; use a dedicated counter row under lock.

**7. How do you get the generated id after an insert?**
Postgres/SQLite: `INSERT ... RETURNING id`. MySQL: `LAST_INSERT_ID()` (per connection). SQL Server: `OUTPUT inserted.id` or `SCOPE_IDENTITY()`. Do not use `SELECT MAX(id)`; it races.

**8. What is a trigger? Give uses and dangers.**
Code fired automatically by INSERT/UPDATE/DELETE, BEFORE/AFTER/INSTEAD OF. Uses: audit logs, derived columns, enforcing complex invariants, writable views. Dangers: hidden side effects, performance on bulk loads, recursion/cascades, hard debugging, portability.

**9. Row-level vs statement-level triggers?**
Row-level fires once per affected row with `OLD`/`NEW`; statement-level once per statement. Postgres has both; MySQL and SQLite only row-level; SQL Server only statement-level (use `inserted`/`deleted` tables and write set-based code).

**10. Function vs stored procedure?**
Functions return values and can be used inside queries; procedures are invoked with CALL/EXEC, may return result sets or OUT params and, in Postgres 11+, can commit/rollback inside. Details vary by dialect, check current docs.

**11. Pros and cons of putting logic in stored procedures?**
Pros: fewer round trips, centralized rules, tight permissions, atomic multi-step work. Cons: harder to version/test/review, vendor lock-in, logic split across tiers, and the database is the hardest tier to scale.

**12. Temp table vs CTE vs subquery?**
CTE/subquery exist for one statement and are mainly readability (planner may inline). A temp table is a real session-scoped table: it can be indexed and analyzed, reused across statements, good for multi-step ETL; cost is writes and catalog churn. Pooling in transaction mode can break session temp tables.

**13. What is a schema?**
A namespace inside a database. Postgres/SQL Server: database > schema > object, resolved by `search_path` in Postgres. In MySQL schema equals database. SQLite uses ATTACH. Used for separation and permissions.

**14. Explain GRANT/REVOKE and least privilege.**
GRANT gives privileges (SELECT, INSERT, EXECUTE, USAGE on schema...) to roles; REVOKE removes. Give the app a role with only the needed rights, never superuser/owner. Use group roles, and `ALTER DEFAULT PRIVILEGES` so new tables inherit grants (Postgres).

**15. What is row-level security and how does it work in Postgres?**
`ALTER TABLE ... ENABLE ROW LEVEL SECURITY` plus `CREATE POLICY ... USING (...) [WITH CHECK (...)]`. Policies are appended to queries so each role sees only permitted rows. Owners/superusers/BYPASSRLS bypass (owners unless FORCE). Typical multi-tenant: policy on `current_setting('app.tenant_id')`, set per request with `SET LOCAL`.

**16. Postgres ENUM vs lookup table vs CHECK?**
ENUM: compact, ordered, but hard to remove/reorder values. Lookup table + FK: flexible, extra join, can carry metadata. CHECK on text: simple, altering needs a constraint change. Choose lookup for values that change, ENUM/CHECK for stable small sets.

**17. What is a domain type?**
A base type plus constraints and optional default (`CREATE DOMAIN positive_int AS int CHECK (VALUE > 0)`), reusable across columns so rules live in one place. Postgres feature.

**18. A trigger-based audit log is slow on bulk updates. Options?**
Make it statement-level using transition tables (Postgres `REFERENCING NEW TABLE`), log asynchronously via logical decoding/CDC, or disable the trigger during loads with a controlled process. Measure first.

**19. SECURITY DEFINER pitfalls?**
Function runs with owner's privileges, so a mutable `search_path` lets attackers shadow objects. Set `SET search_path = ...` on the function, schema-qualify names, restrict EXECUTE.

**20. Why can't a view or CTE "cache" results like a materialized view?**
They are definitions, re-evaluated per use; only materialization stores rows. (Postgres 12+ CTEs are inlined when referenced once and side-effect free; `MATERIALIZED` forces evaluation once.) Check current docs for your version.
