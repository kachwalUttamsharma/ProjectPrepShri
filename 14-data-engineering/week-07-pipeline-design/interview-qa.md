# Week 7 Interview Q&A: Pipeline and Platform Design

Short, speakable answers. Each ends with the senior signal: a tradeoff or a failure mode. See [lesson.md](lesson.md) for the framework.

## A. Framing and requirements

**Q1. A stakeholder says "we need real-time data". What do you do?**
Ask what decision changes with fresher data and what staleness is tolerable. "Real-time" usually means 1-5 minutes; true sub-second is rare. Streaming costs more to build and operate, so pick the slowest mode that meets the SLA. Often micro-batch every few minutes is enough.

**Q2. What do you ask first in a pipeline design interview?**
Consumers and decisions, freshness SLA, volume and growth, correctness bar (can we lose/duplicate?), sources and ownership, history/backfill needs, compliance, and budget/team. Then I state the single hardest requirement.

**Q3. Batch vs streaming: how do you decide?**
Freshness SLA first, then complexity cost. Batch for finance, reporting, large recompute. Streaming for alerting, fraud, operations. Hybrid when you need fast approximate plus slow authoritative. I also consider whether consumers can use incomplete data.

**Q4. Lambda vs Kappa?**
Lambda: batch and speed layers, merged at query time; correct but two codebases. Kappa: only a streaming path, reprocess by replaying the log; simpler but needs long retention/replayable storage and mature stream tooling. Today many teams use a lakehouse as replay source and share logic between modes.

## B. Ingestion

**Q5. How do you replicate an OLTP database into the lakehouse?**
Log-based CDC (Debezium) into Kafka keyed by PK, land raw change events, MERGE latest-by-LSN into a mirror table, keep history optionally. Handle snapshot/stream handoff, deletes, schema changes, and reconcile counts/checksums. Risk to name: unconsumed replication slot filling the source disk.

**Q6. Why not just query `updated_at > last_run`?**
It misses hard deletes, has race conditions with long transactions and clock skew, and loads the source. Use an overlap window and periodic full-key diff if you must; prefer log-based CDC.

**Q7. How do you guarantee no data loss on ingestion?**
Durable log first (Kafka with acks=all, replication factor 3, min ISR 2), commit offsets/cursors only after successful write, immutable raw layer, and reconciliation counts between source and landing. Detect loss, not just prevent it.

**Q8. How do you handle schema changes from upstream?**
Data contracts plus a schema registry with compatibility rules. Additive changes flow automatically (nullable columns); breaking changes block promotion and notify the producer; raw keeps everything so you can replay after fixing.

## C. Semantics and correctness

**Q9. Explain at-least-once, at-most-once, exactly-once.**
At-least-once: retries cause duplicates. At-most-once: no retries, possible loss. Exactly-once effect = at-least-once delivery plus idempotent or transactional writes. True end-to-end exactly-once across systems is achieved by idempotency (dedupe keys, MERGE), not magic.

**Q10. How do you make a batch job idempotent?**
Output is a pure function of the input partition and parameters (`logical_date`, not `now()`); write with overwrite-partition or MERGE on a key; atomic publish. Then retries and backfills are safe.

**Q11. Late-arriving data in streaming?**
Use event time, watermarks, and allowed lateness. Beyond the watermark, route to a side output and let a batch job correct. Dashboards are provisional; the batch layer is authoritative.

**Q12. How do you dedupe events?**
A unique event id from the producer; stream dedupe with keyed state TTL; batch dedupe with `row_number() over (partition by key order by version desc)`. For CDC, order by LSN, not arrival.

**Q13. Dimension arrives after the fact (late-arriving dimension)?**
Insert an "unknown" inferred member, and fix when the real record arrives; or hold facts in a retry queue. Never drop facts.

## D. Storage and modeling

**Q14. Explain bronze/silver/gold and why.**
Bronze is the immutable replayable record; silver is cleaned, typed, deduped; gold is business-ready marts. Layers localize failures, enable reprocessing, and separate quality guarantees. Cost: storage and extra hops, which are cheap compared with the debugging value.

**Q15. Why use Iceberg/Delta/Hudi over plain Parquet?**
ACID commits, snapshot isolation, schema evolution, time travel, row-level MERGE/DELETE, and compaction. Plain Parquet folders give no atomic multi-file commits or safe concurrent writers. Feature details vary by version (check current docs).

**Q16. How do you choose partitioning?**
Partition by a low-cardinality column used in most filters (usually date); aim for files of 128 MB-1 GB; avoid over-partitioning that creates small files. Use clustering/Z-order or sort for second-level pruning. Changing partitioning later is costly, so prefer formats with hidden/evolvable partitioning.

**Q17. How do you handle SCD2 in a pipeline?**
Keep `valid_from/valid_to/is_current`; on change, close the old row and insert the new one in one MERGE; order events by source version to be robust to out-of-order arrival; facts join on the as-of condition.

## E. Serving

**Q18. Warehouse vs OLAP store (Druid/Pinot/ClickHouse)?**
Warehouse: flexible SQL, joins, moderate concurrency. OLAP: sub-second aggregates on fresh data at high concurrency, usually denormalized with limited joins. Pick OLAP for user-facing dashboards or APIs; a warehouse otherwise.

**Q19. What is point-in-time correctness?**
For training data, each feature value joined to a label must be the value known at the label's time, otherwise future information leaks. Use event-timestamped feature history and as-of joins.

**Q20. How do you serve a metric consistently across BI tools?**
A semantic/metrics layer defining metrics once (dbt metrics/semantic layer, LookML, Cube; check current docs). Avoid per-dashboard SQL copies.

## F. Orchestration and quality

**Q21. Airflow design best practices?**
Idempotent small tasks, no heavy compute in the scheduler (offload to Spark/warehouse), parameterize by logical date, retries with backoff, pools, SLAs, data-aware triggering where possible, dynamic DAGs sparingly, and backfills tested.

**Q22. How do you implement data quality?**
Checks at layer boundaries (schema, freshness, volume, uniqueness, referential, reconciliation, distribution); block-vs-warn policy; quarantine bad rows; ownership and alerts routed to the producer; track quality metrics over time.

**Q23. Data contracts?**
Producer-owned, versioned agreements on schema, semantics, freshness, and SLA, enforced in CI and at ingestion. They shift responsibility upstream, which reduces breakages.

**Q24. How do you do observability for pipelines?**
Freshness, volume, schema, and lineage monitors; job metrics (duration, retries, lag, watermark delay); alerts based on consumer-facing symptoms; runbooks; incident reviews. Cost metrics per pipeline.

## G. Reprocessing and failure

**Q25. How do you backfill safely?**
Parameterized jobs by partition, run in an isolated/throttled queue, write to a shadow table or new snapshot, validate against the old, then swap; notify consumers of restated numbers.

**Q26. A pipeline silently produced wrong numbers for 3 days. Response?**
Stop propagation (pause downstream), assess blast radius via lineage, fix root cause, backfill from immutable raw, validate with reconciliation, communicate restated values, then add a check that would have caught it. Blameless postmortem.

**Q27. Consumer lag keeps growing. Diagnose.**
Compare produce vs consume rate; check skew (one hot partition), slow downstream sink, rebalances, GC, a poison message retry loop, or insufficient consumers/partitions. Fix: scale to partition count, optimize sink (batching), DLQ the poison pill, repartition.

**Q28. Poison message?**
Isolate with a DLQ containing the payload, error, and metadata; continue the main flow; alert; build a replay tool after the fix.

## H. Cost and security

**Q29. How would you cut a platform bill by 30%?**
Measure first (cost per pipeline/team). Then: delete unused tables/pipelines, replace streaming where batch suffices, compaction and partition pruning, columnar compression, lifecycle tiering, spot instances, auto-termination, query guardrails, right-size clusters, cache hot aggregates.

**Q30. How do you protect PII in a lakehouse?**
Classify and tag columns, tokenize/hash at ingest, encryption, column/row-level security, separate restricted zone, audit, short raw retention, and a deletion workflow (design 8). Principle: minimize where PII lives.

**Q31. How do you do GDPR erasure on immutable files?**
Batch deletion by identifier through MERGE/DELETE, compaction and snapshot expiry to physically remove old files, crypto-shredding where designed in, backups by expiry, replay erasure log after restore. Confirm legal specifics with counsel.

## I. Architecture judgment

**Q32. When would you not use Spark?**
Small data that fits warehouse SQL or a single machine (DuckDB/Polars), or pure SQL transformations well served by the warehouse. Spark shines at large-scale, heavy file processing, ML, and custom logic.

**Q33. Centralized platform team vs data mesh?**
Central: consistency and efficiency, but bottleneck at scale. Mesh: domain ownership, requires strong self-serve platform and federated governance. Hybrid is common: platform provides ingestion/compute/catalog, domains own products and quality.

**Q34. How do you evolve a platform without a big-bang rewrite?**
Strangler pattern: new pipelines on the new stack, migrate by consumer value, run old and new in parallel with reconciliation, retire when diffs are zero for N days.

**Q35. Pipeline SLAs: how do you define and meet them?**
Define by consumer: freshness (data ready by 07:00), completeness, accuracy. Build critical path monitoring, buffer time, retries, and degrade gracefully (publish previous snapshot flagged stale). Track SLO attainment and error budget for the data product.
