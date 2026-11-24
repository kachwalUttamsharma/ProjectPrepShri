# Week 1 Interview Q&A: Modeling and Warehousing

Cover the answer, say yours out loud, then compare. Answers are deliberately concise. "Probe" lines are the follow-ups interviewers typically ask.

---

**1. OLTP vs OLAP, and why not run analytics on the OLTP database?**
OLTP: many small transactional reads/writes by key, normalized, row-store. OLAP: few large scans/aggregations over history, denormalized, columnar. Analytics on the primary competes for locks, buffer cache and IO with customer traffic, and a row store reads whole rows to aggregate one column. Use CDC or a replica into a warehouse/lakehouse.
Probe: "What if the business needs real-time?" CDC/stream into the warehouse, or a real-time OLAP store (Pinot, Druid, ClickHouse); trade freshness against cost and complexity.

**2. Walk me through the Kimball design process.**
Pick the business process, declare the grain, choose dimensions, choose facts. Grain first because every column and measure must be valid at that grain, and it determines what questions can be answered (you can roll up, never drill below grain).

**3. What is grain, and what goes wrong if it is ambiguous?**
Grain is the precise meaning of one fact row ("one order line"). Ambiguity leads to mixed grains: e.g. shipping fee at order level repeated on each line, so `SUM(shipping)` overcounts. Fix: allocate to lines or keep a header-grain fact.

**4. Star vs snowflake?**
Star: denormalized dimensions, one hop, simple and fast for BI. Snowflake: normalized dimension hierarchies, more joins, minor storage savings (columnar compression already shrinks repetition). Default to star; snowflake only for large shared sub-dimensions or when hierarchy maintenance demands it.

**5. Name the fact table types and when to use each.**
Transaction (event), periodic snapshot (state per period, e.g. daily balance), accumulating snapshot (pipeline lifecycle with updated milestone dates), factless (events/coverage with no measure). Probe: "Which is updated in place?" Accumulating snapshot.

**6. Additive, semi-additive, non-additive?**
Additive sums across all dimensions (revenue). Semi-additive cannot sum across time (balances, inventory; use last value, average or end-of-period). Non-additive: ratios/percentages; store numerator and denominator, compute the ratio after aggregation.

**7. Why surrogate keys instead of natural keys?**
Needed for SCD2 (many versions per natural key); insulates from source key reuse/format changes/merging systems; compact integer joins; supports unknown/inferred members. Cost: needs a lookup during fact load and key management. Hash keys make parallel/idempotent loads easy (deterministic) but are wider.

**8. Explain SCD types 1, 2, 3, 6 and give a use for each.**
1: overwrite (typo fix). 2: new row with valid_from/valid_to/is_current (customer region in sales reports). 3: previous-value column (limited history). 6: SCD2 plus a current-value column on all versions so you can report as-was and as-is. Probe: "Which do you default to?" 2 for analytically significant attributes, 1 for the rest, decided per column, not per table.

**9. How do you implement SCD2 safely and idempotently?**
Stage the changes, compare tracked attributes (column compare or row hash), close current rows, insert new versions, in one transaction (or one MERGE). Half-open intervals, unique index on current row per key, dedupe the staging by key and effective date, and make the batch re-runnable (NOT EXISTS current row). Test: one current row per key, no overlaps/gaps.
Probe: "Two changes for one key in the same batch?" Order by effective timestamp and generate multiple versions in one pass (window function with LEAD to compute valid_to).

**10. How does a fact row find the right SCD2 version?**
Range join on the event time: `event_ts >= valid_from AND event_ts < valid_to` on the natural key. Late events resolve to the version valid at event time, not the current one.

**11. Late-arriving facts vs late-arriving dimensions?**
Late fact: load it, look up the historical version; recompute affected aggregates/partitions. Fact arriving before its dimension row: insert an inferred member (flagged) and fill in the real attributes when they arrive. Late dimension change (backdated): split the version and re-point facts in the affected window, or accept load-time effectiveness and document it.

**12. What is a degenerate dimension? A junk dimension? A role-playing dimension?**
Degenerate: identifier in the fact with no table (order_number). Junk: combine low-cardinality flags into one small dimension. Role-playing: one physical dimension (date) used under several roles (order date, ship date) via aliases/views.

**13. What is a conformed dimension and why does it matter?**
Same keys, attributes and meaning shared across fact tables/marts. It lets you drill across processes (sales vs returns by the same customer segment) and is the basis of the bus matrix. Without it, each mart's "customer" disagrees.

**14. When do you need a bridge table?**
Many-to-many between a fact and a dimension (encounter-diagnosis, account-owners) or hierarchies with variable depth. Add a weighting factor so allocated measures sum correctly; warn consumers about fan-out when no weights are applied.

**15. Kimball vs Inmon vs Data Vault: which and when?**
Kimball: dimensional marts via conformed dims, fastest to value. Inmon: normalized enterprise warehouse first. Data Vault: hubs/links/satellites for auditability and flexible source onboarding, with marts on top. In practice many teams run raw -> staging -> marts (Kimball presentation) and add Vault only for heavy multi-source/audit needs. Trade-off: Vault has more joins and tables and needs a presentation layer.

**16. ELT vs ETL?**
ELT loads raw first and transforms in the warehouse using SQL (dbt); good with elastic compute and raw replay. ETL transforms before load; good when sensitive data must be masked before landing or the target is constrained. Most real pipelines are hybrid. Keep an immutable raw layer either way.

**17. Why are columnar stores fast for analytics and bad at row updates?**
Reading only needed columns, high compression (dictionary/RLE/delta), vectorized execution, block skipping via min/max. Updating one row means rewriting compressed column chunks, so engines use immutable files, delta stores, and batch merges.

**18. Partitioning vs clustering in a warehouse?**
Partitioning physically segments by a column (usually date) for exact pruning and predictable cost; clustering/sorting orders data within storage so min/max statistics are tight for other filter columns. Pitfalls: partitioning on high-cardinality columns (too many small partitions), clustering on columns never filtered, reclustering cost (Snowflake automatic clustering consumes credits; check current docs).

**19. How would you control warehouse cost?**
Prune columns and partitions, incremental models, materialize repeated aggregates, auto-suspend and right-size compute, separate warehouses/slot reservations per workload with budgets and timeouts, query tagging and monitoring of top-cost queries, shorter retention for staging tables, bytes-billed caps (BigQuery) / resource monitors (Snowflake) (check current docs for names).
Probe: "A dashboard suddenly costs 10x." Check query history for changed scan volume, lost partition filter, new join, or cache invalidation from frequent upstream refresh; fix with a pre-aggregated table.

**20. Compare Snowflake, BigQuery, Redshift at a design level.**
Snowflake: virtual warehouses (compute) over micro-partitioned storage, per-second billing, multi-cluster for concurrency, automatic layout. BigQuery: serverless, bytes-scanned or slot capacity pricing, you declare partition/cluster. Redshift: MPP clusters (or Serverless) where sort and distribution keys matter, plus Spectrum for S3. Details and pricing change: check current docs.

**21. What are distribution and sort keys in Redshift?**
Distribution key decides which node holds a row: co-locate join keys to avoid shuffles; ALL for small dimensions; EVEN for no good key; AUTO lets the engine choose. Sort key orders rows on disk so zone maps skip blocks (compound is typical; interleaved is rarely beneficial now, check current docs). Pitfall: skewed distribution key.

**22. How do you model a many-to-one hierarchy that changes over time (e.g. product category reorganized)?**
If history matters, SCD2 on the product dimension (category attribute). If reorganizations are large and frequent, a separate hierarchy dimension or bridge with effective dates so you can report under old or new structure.

**23. How would you test a dimensional model?**
Grain uniqueness on the fact (PK test), not-null and relationship tests on FKs (every FK has a dimension row; unknown member), one current row per natural key, no overlapping SCD intervals, row-count and sum reconciliation to source, freshness checks, accepted values.

**24. What is a fan trap / chasm trap and how do you avoid it?**
Joining across one-to-many paths inflates measures (fan trap), or joining two facts through a shared dimension multiplies rows. Avoid by aggregating each fact to the shared dimension grain before joining (drill-across), and by understanding cardinality of every join.

**25. When would you use One Big Table instead of a star?**
Simple, stable use cases with a single consumer and a columnar engine; avoids joins. Downsides: duplicated attributes, expensive rebuilds on dimension change, weaker governance and SCD handling. Often a derived layer built from the star, not a replacement.

**26. How do you handle currencies/time zones in facts?**
Store UTC timestamp plus a local date key where relevant; store original currency amount, functional-currency amount and the rate used (rate table with effective date). Never convert in the BI layer only.

**27. Explain how you would design the model for a ride-sharing company in 10 minutes.**
Process: trips. Grain: one completed trip (cancelled trips in a sibling fact). Measures: fare, distance, duration, surge, payout. Dims: rider, driver (SCD2), vehicle, pickup/dropoff location role-playing, date, time, product type, payment. Add accumulating snapshot for request-to-dropoff lifecycle and a daily driver-utilization periodic snapshot. Flag late mobile events and event vs server time. (More prompts in the lesson, section 9.)

**28. A source system hard-deletes rows. How does the warehouse know?**
CDC with delete events, or periodic full-key comparison (anti-join of source keys vs warehouse). Implement as soft delete (`is_deleted`, `deleted_at`) so history and facts survive. Mention GDPR deletion as a separate hard-delete path.

**29. What is the difference between a data mart, warehouse, and data lake in this context?**
Warehouse: curated, modeled, governed integrated data. Mart: subject-specific subset (finance, marketing), often a star. Lake: raw/semi-structured files in object storage with schema on read. Lakehouse (week 5) unifies them with table formats.

**30. Where do metrics definitions live?**
Ideally one governed semantic layer (dbt metrics/MetricFlow, LookML, Cube; check current docs) so "revenue" is defined once; otherwise each dashboard reinvents it. Tie to conformed dimensions.

---

## Whiteboard drill (do 3 per session, timed 10 min each)
Pick prompts from lesson section 9. Required output: grain sentence, bus matrix row, fact columns, 5 dimensions with SCD choice, one tricky issue, three business questions answered by your model, and tests you would write.
