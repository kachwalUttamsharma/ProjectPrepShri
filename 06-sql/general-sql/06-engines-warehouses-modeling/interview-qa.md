# Part 06 interview Q&A: engines, warehouses, modeling

Version-specific details: check current docs. Non-SQLite snippets: not run here, verify.

**1. OLTP vs OLAP?**
OLTP: many short transactions touching few rows, normalized schema, row storage, latency and correctness matter. OLAP: few long queries scanning many rows but few columns, denormalized (star) schema, columnar storage, throughput matters. Usually separate systems, linked by ELT/CDC.

**2. Why are column stores faster for analytics?**
They read only the needed columns, compress similar values well, run vectorized, and skip blocks using min/max metadata. The cost: point lookups, single-row updates and wide-row reads are slower.

**3. Why is a warehouse a poor choice for an application backend?**
Single-row writes and lookups are slow or costly, there is little or no enforced row-level integrity, transaction semantics are limited, and concurrency is tuned for a few heavy queries rather than thousands of tiny ones.

**4. Name three differences between Postgres and MySQL (InnoDB).**
Postgres: heap tables with MVCC storing row versions in the table (needs VACUUM), richer types (JSONB, arrays, ranges), many index types (GIN, GiST, BRIN), transactional DDL. InnoDB: clustered index on the primary key, undo-log MVCC, default REPEATABLE READ with gap/next-key locks, historically looser type coercion unless strict `sql_mode`. DDL is mostly not transactional in MySQL. Check current docs for version changes.

**5. When is SQLite the right choice?**
Embedded, single-process or low write concurrency: mobile/desktop apps, tests, caches, small tools, data exchange file. It is a library with one file; there is one writer at a time (WAL mode lets readers proceed during a write). Not for many concurrent writers over a network.

**6. What does "constraints are informational" mean in BigQuery/Snowflake/Redshift?**
You can declare PK/FK/UNIQUE, and the optimizer may use them as hints, but the engine does not reject violating rows (NOT NULL is typically enforced; check current docs per product). So duplicates must be prevented by the pipeline.

**7. What is a star schema? Why use it?**
One fact table (measures plus foreign keys at a declared grain) joined to denormalized dimension tables. Queries are simple (fact join few dimensions, group by attributes), predictable, and perform well on columnar engines. A snowflake schema further normalizes dimensions: less redundancy, more joins.

**8. What is the grain of a fact table and why does it matter?**
The meaning of one row ("one line item per order"). Choosing it first prevents mixing levels (order-level and line-level amounts in one table), which causes double counting on SUM.

**9. Additive, semi-additive, non-additive measures?**
Additive: sum across all dimensions (sales amount). Semi-additive: sum across some but not time (account balance; use latest or average over time). Non-additive: ratios, percentages; store numerator and denominator and divide after aggregation.

**10. Explain SCD types 1, 2, 3.**
Type 1 overwrites (no history). Type 2 inserts a new version row with validity dates and a new surrogate key (full history). Type 3 keeps one previous value in an extra column (limited history). Type 0 never changes.

**11. How do you implement SCD2 in SQL?**
Compare staging to current rows. Step 1: close changed current rows (`valid_to = change_date`, `is_current = 0`). Step 2: insert new current rows for changed and new keys. Do it in one transaction, close before insert. Many systems use MERGE. Point-in-time lookup: `valid_from <= d AND d < valid_to`.

**12. Why a surrogate key in dimensions?**
Business keys can be reused, change, or repeat across SCD2 versions; surrogate keys are stable, small integers, independent of source systems, and let facts point to a specific version.

**13. What goes wrong when joining a fact to an SCD2 dimension on the business key only?**
Each fact matches every version of the customer, multiplying rows and inflating sums. Either store the version's surrogate key on the fact at load time, or join with a date range condition.

**14. What is partitioning and how is it different from sharding and indexing?**
Partitioning splits one table inside one database by range/list/hash so queries prune irrelevant pieces and old data can be dropped quickly. Sharding spreads data across servers (application or middleware must route; cross-shard joins and transactions are hard). An index is an additional structure for fast lookup; partitioning is about physical segmentation.

**15. When does partitioning not help?**
When queries do not filter on the partition key (no pruning), when partitions are tiny and numerous (overhead), or when an index already serves point lookups. In MySQL the partition key must be part of unique keys (check current docs).

**16. ETL vs ELT?**
ETL transforms before loading; ELT loads raw data first and transforms inside the warehouse with SQL (dbt-style). ELT leverages cheap elastic warehouse compute and keeps raw data replayable.

**17. How do BigQuery, Snowflake and Redshift differ architecturally?**
BigQuery: serverless, storage and compute separated, on-demand billing by bytes scanned or reserved slots. Snowflake: virtual warehouses (compute clusters) separate from storage, micro-partitions, Time Travel and zero-copy clones. Redshift: cluster-based (RA3 separates storage; serverless option), you tune distribution and sort keys. Pricing/features change: check current docs.

**18. How would you deduplicate in a warehouse that does not enforce unique keys?**
`ROW_NUMBER() OVER (PARTITION BY business_key ORDER BY loaded_at DESC) = 1` in a view or staging step, or MERGE on load.

**19. A report query on production OLTP is slowing the app. Options?**
Read replica; materialized summary table; move to a warehouse via CDC/ELT; add the right index or rewrite; schedule off-peak; set statement timeouts and resource limits.

**20. Design a model for "orders" analytics.**
Fact: `fact_order_line` (grain: one order line) with keys to `dim_date`, `dim_product`, `dim_customer`, `dim_store`, measures quantity, net_amount, discount; order number as a degenerate dimension. Customer as SCD2 if reports need the attributes at purchase time. Partition by order date; cluster by customer or product. Run the SQLite version in [setup.sql](setup.sql).
