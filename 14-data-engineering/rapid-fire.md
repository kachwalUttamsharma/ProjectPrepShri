# Rapid-Fire: Data Engineering (one-liners)

Answer aloud in under 15 seconds each. Version-specific details: check current docs.

## Modeling and warehousing
1. **Grain?** What exactly one fact row represents; declare it first.
2. **Star vs snowflake?** Star = denormalized dims, one hop; snowflake = normalized dims, more joins.
3. **Surrogate key why?** Stable, meaningless key that supports SCD2 and insulates from source key changes.
4. **SCD2?** New row per change with valid_from/valid_to/is_current; facts point to the version valid at event time.
5. **SCD1 vs SCD2?** Overwrite loses history; versioning keeps it.
6. **Degenerate dimension?** An identifier kept in the fact (order number) with no dimension table.
7. **Conformed dimension?** Same dimension shared across facts so you can drill across.
8. **Semi-additive measure?** Can sum across some dimensions but not time (balance).
9. **Accumulating snapshot?** One row per process instance, updated as milestones occur.
10. **Bridge table?** Resolves many-to-many between fact and dimension, often with weights.
11. **Inferred member?** Placeholder dimension row created when a fact arrives before its dimension.
12. **Kimball vs Inmon?** Dimensional marts bottom-up vs normalized enterprise warehouse top-down.
13. **Data Vault parts?** Hubs (keys), links (relationships), satellites (attributes and history).
14. **ELT vs ETL?** Load raw then transform in the warehouse vs transform before loading.
15. **Why columnar for analytics?** Read only needed columns, compress better, skip blocks via stats.

## SQL and warehouse practice
16. **Partition vs cluster?** Partition splits storage by a column for pruning; clustering orders data within it for tight stats.
17. **Biggest warehouse cost lever?** Bytes scanned or compute time: prune columns/partitions, incremental models, right-size compute.
18. **Window function for dedupe?** `ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC) = 1`.
19. **Why not SELECT * in a warehouse?** Columnar cost and IO scale with columns read.
20. **Idempotent load?** Re-running yields the same result: MERGE on keys or overwrite a partition.

## Spark
21. **Narrow vs wide transformation?** Narrow needs no shuffle (map, filter); wide shuffles (groupBy, join).
22. **What defines a stage boundary?** A shuffle.
23. **Transformation vs action?** Transformations are lazy; actions (count, write) trigger execution.
24. **Data skew fix?** Salting, broadcast the small side, AQE skew join, pre-aggregate.
25. **Broadcast join when?** One side small enough to ship to every executor; avoids shuffle.
26. **repartition vs coalesce?** repartition does a full shuffle (any count); coalesce merges partitions without shuffle (decrease only).
27. **cache vs persist?** cache = persist with default storage level; both only help when data is reused.
28. **What does AQE do?** Re-optimizes at runtime: coalesces shuffle partitions, switches join strategy, splits skewed partitions.
29. **Why avoid Python UDFs?** Serialization overhead between JVM and Python; prefer built-ins or pandas UDFs.
30. **Executor OOM causes?** Skewed partitions, large collects, too few partitions, big broadcast, memory overhead for Python.

## Airflow and dbt
31. **Idempotent task?** Safe to re-run with same inputs; writes by key or partition overwrite.
32. **Catchup/backfill?** Running past schedule intervals; keep tasks parameterized by logical date.
33. **Sensor downside?** Occupies a worker slot while polling unless deferrable/reschedule mode.
34. **XCom use?** Small metadata between tasks, not datasets.
35. **Executors?** Local, Celery, Kubernetes; choose by scale and isolation needs.
36. **Airflow is a ...?** Orchestrator, not a data processing engine: trigger work elsewhere.
37. **dbt incremental model?** Only processes new/changed rows using `is_incremental()` and a unique key.
38. **dbt snapshot?** Implements SCD2 on a source table.
39. **dbt tests basics?** unique, not_null, accepted_values, relationships, plus custom SQL tests.
40. **Data interval vs execution date?** Run covers the interval that just ended; logical date is the interval start (Airflow 2 semantics; check current docs).

## Kafka and streaming
41. **Partition purpose?** Unit of parallelism and ordering; ordering is guaranteed only within a partition.
42. **Consumer group?** Consumers sharing partitions; each partition goes to one consumer in the group.
43. **Offset commit timing and semantics?** Commit after processing = at-least-once; before = at-most-once.
44. **Exactly-once in Kafka?** Idempotent producer plus transactions plus read_committed consumers; end-to-end needs idempotent sinks.
45. **Key choice?** Determines partition; choose to preserve per-entity order and avoid hot keys.
46. **Log compaction?** Keeps the latest record per key; used for changelog/state topics.
47. **Replication factor and ISR?** Copies of a partition; in-sync replicas with min.insync.replicas + acks=all give durability.
48. **Watermark?** Estimate of event-time progress; decides when windows close and late data is dropped.
49. **Event time vs processing time?** When it happened vs when you saw it; use event time for correctness.
50. **CDC?** Capturing row changes from a database log (Debezium) as an event stream.
51. **Schema registry?** Central schema store with compatibility rules for producers/consumers.
52. **Kafka vs queue (SQS)?** Kafka is a replayable partitioned log with multiple independent consumers; SQS is a deletion-on-consume queue.

## Lakehouse and formats
53. **Parquet structure?** Row groups, column chunks, pages, footer with schema and statistics.
54. **Predicate pushdown?** Skip row groups/pages via min/max statistics before reading.
55. **Avro vs Parquet?** Avro row-based for messages and evolution; Parquet columnar for analytics.
56. **Small files problem?** Too many tiny files slow listing and tasks; fix by compaction and write tuning.
57. **Why Delta/Iceberg/Hudi?** ACID, snapshots, row-level changes and schema evolution on object storage.
58. **Copy-on-write vs merge-on-read?** CoW rewrites files on update; MoR writes delta files merged later.
59. **Time travel limit?** Retention: vacuum/expire removes old files.
60. **Medallion?** Bronze raw, silver cleaned, gold business-ready.
61. **Partitioning pitfall?** High-cardinality partition columns create many tiny partitions.
62. **Glue Data Catalog?** AWS managed Hive-compatible metastore used by Athena, EMR, Glue, Spectrum.
63. **Athena billing?** Per data scanned; reduce with Parquet, partitions, column pruning (check current docs).
64. **Lake Formation?** Central fine-grained permissions on catalog resources across AWS analytics engines.

## Quality, governance, pipelines
65. **Data contract?** Agreed schema, semantics, freshness and quality between producer and consumer, enforced in CI.
66. **Five common quality checks?** Freshness, volume, schema, nulls/uniqueness, referential integrity/distribution.
67. **Data lineage?** Tracking where data came from and what depends on it (OpenLineage).
68. **PII handling?** Classify, minimize, mask/tokenize, encrypt, restrict access, support deletion.
69. **Dead-letter queue?** Where unprocessable records go so the pipeline continues and they can be fixed/replayed.
70. **Backfill strategy?** Parameterize by date range, idempotent writes, throttle, validate against totals.
71. **Late-arriving data handling?** Watermark/lookback window and reprocessing of affected partitions.
72. **SLA vs SLO for pipelines?** SLA is the external commitment (data ready by 7am); SLO is the internal target and monitoring.
73. **Batch vs streaming choice?** Streaming only when freshness requirements justify added complexity and cost.
74. **Lambda vs Kappa?** Lambda keeps separate batch and speed paths; Kappa uses one streaming path with replay.
75. **Exactly-once vs effectively-once?** Duplicates possible in transport; idempotent writes make results effectively once.
76. **Pipeline monitoring essentials?** Freshness, row counts, failure/retry rates, runtime, cost, data quality results with alerting.
77. **Reprocessing safely?** Immutable raw data plus deterministic transforms and versioned code.
78. **Handling schema drift?** Contract + compatibility checks + evolution policy; quarantine non-conforming records.
79. **Cost vs latency trade-off?** Lower latency usually means always-on compute and smaller files; pick the slowest acceptable freshness.
80. **What do you do first on a failed pipeline at 3am?** Check scope/impact, stop bad data propagating, fix or roll back, backfill, then write a post-incident action.
