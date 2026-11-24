# Week 3 interview Q&A: orchestration and dbt

**1. ETL vs ELT: which and why?**
ETL transforms before loading; ELT lands raw data first and transforms in the warehouse/lakehouse with SQL. ELT wins when compute is elastic and storage is cheap: raw data is kept for reprocessing, transformations are versioned SQL (dbt), analysts can contribute. ETL still makes sense for PII scrubbing before landing, heavy non-SQL processing, or legacy targets.
*Follow-ups:* Where does PII masking happen in ELT? How do you handle schema drift in raw?

**2. Explain Airflow's architecture.**
Scheduler parses DAG files, creates DAG runs and task instances, and queues them; the executor decides where they run (Local, Celery workers, Kubernetes pods); workers execute; the metadata DB stores state; the webserver shows UI; the triggerer runs deferrable operators.
*Follow-ups:* What breaks if the scheduler parses slowly? (Heavy top-level code.) Celery vs Kubernetes executor trade-offs? (Latency and shared workers vs isolation and per-task images.)

**3. What are logical date and data interval? Why does a daily run for May 1 start on May 2?**
The run represents the interval of data it covers, `[start, end)`, and can only run once the interval is complete. Tasks should derive their input slice from `data_interval_start/end`, not the wall clock, so reruns and backfills reproduce the same result.
*Follow-ups:* What does `{{ ds }}` give? What breaks if you use `datetime.now()`? How does this change for data-aware (dataset/asset) scheduling? (check current docs)

**4. catchup vs backfill?**
`catchup` is the scheduler automatically creating runs for all intervals since `start_date` that have not run. Backfill is an explicit re-run of a historical range, for new logic or fixed data. Both require idempotent, interval-parameterised tasks and a thought for concurrency (`max_active_runs`) and downstream load.
*Follow-up:* You deployed a bug fix; how do you reprocess the last 30 days safely? (Clear tasks or trigger a backfill, limit concurrency, partition overwrite so no duplicates, notify consumers.)

**5. What makes a task idempotent? Give patterns.**
Same inputs -> same final state regardless of how often it runs. Patterns: output path/partition keyed by the logical date and overwritten; MERGE on a business key; delete+insert for a partition in one transaction; write to staging then atomic swap; deterministic transformations (no `now()`, random).
*Follow-ups:* What about sending an email or calling a payment API? (Idempotency keys, outbox/guard table.) Is `INSERT` after `TRUNCATE` idempotent? (Only if atomic; else a failure leaves it empty.)

**6. Can you get exactly-once?**
Delivery is at-least-once in practice; exactly-once *effect* comes from idempotent writes or dedupe on a stable key (upsert/merge, `row_number()` latest, transactional offset + data commit as in Kafka/Flink sinks).
*Follow-ups:* Where do you get a stable key if the source has none? (Hash of business columns, source offsets/LSN.) What if duplicates have different timestamps? (Define tie-breaking: ingested_at, sequence.)

**7. Compare incremental load strategies.**
Full refresh (simple, expensive, catches deletes), watermark (cheap, needs reliable `updated_at`, misses hard deletes and late-arriving old timestamps), CDC (captures deletes and every change, more infrastructure and ordering concerns), partition overwrite (idempotent for time-partitioned facts). Combine: incremental daily plus periodic full reconcile.
*Follow-ups:* The watermark column is not updated on some edits. Now what? How do you handle deletes without CDC? (Soft deletes, snapshot diff, periodic full compare.) Why advance the watermark transactionally with the load?

**8. How do you handle late-arriving data?**
Decide a lateness tolerance. Batch: lookback window on incremental models (reprocess the last N hours/days), partition overwrite of recent partitions, separate event_time vs ingested_at columns, periodic reconciliation. Streaming: watermarks with allowed lateness, side outputs for too-late events.
*Follow-up:* Downstream consumers already read yesterday's numbers; how do you communicate restatements? (Versioned/slowly settling metrics, data contracts, change logs.)

**9. How do you structure retries and failure handling?**
Retries with backoff for transient failures (network, throttling); fail fast for deterministic errors. Timeouts on tasks. Alerts via callbacks on failure, and monitoring for missing runs/freshness. Per-record bad data goes to a dead-letter table/queue with error and payload; the job continues and DLQ size is alarmed and replayable.
*Follow-ups:* What is a poison pill? Retry storms against a downed dependency? (Backoff + jitter, circuit breaker, pools.)

**10. Task granularity: how big should an Airflow task be?**
A unit that can be retried independently, is idempotent, and produces a checkpoint (a table, file, partition). Too coarse: expensive retries, opaque failures. Too fine: scheduler overhead, many XComs, slow DAG. Group related steps (TaskGroup) for readability.
*Follow-up:* How do you fan out per-file or per-table work? (Dynamic task mapping `.expand()`, with limits.)

**11. What are XComs for and not for?**
Small pieces of metadata (ids, paths, counts) between tasks, stored in the metadata DB (custom backends exist). Never pass data frames or large payloads; write to storage and pass a pointer.

**12. Sensors: what are the pitfalls?**
Poke-mode sensors occupy a worker slot while waiting. Use `reschedule` mode or deferrable operators, set timeouts, and prefer event-driven triggers (datasets/assets, S3 event notifications) over time-based guessing.
*Follow-up:* Cross-DAG dependency options? (ExternalTaskSensor, TriggerDagRunOperator, datasets.)

**13. Common Airflow anti-patterns?**
Heavy imports or API/DB calls at DAG parse time; dynamic `start_date`; non-idempotent appends; storing state on a worker's local disk; big XComs; running heavy compute on Airflow workers instead of delegating; no pools or concurrency caps; secrets in code (use connections/secret backends).

**14. Airflow vs Dagster vs Prefect vs Step Functions?**
Airflow: mature, huge operator ecosystem, task-centric, schedule-oriented. Dagster: asset-centric (declare assets and lineage), good testing and local dev. Prefect: Python-native flows, dynamic, lighter setup. Step Functions: managed serverless state machines with built-in retry/catch, best for AWS service orchestration, not data-aware. Pick based on team skills, ops burden, lineage needs, and ecosystem.
*Follow-up:* When would you not use Airflow? (Low-latency event workflows, streaming.)

**15. What is dbt and where does it sit?**
A transformation framework: SQL SELECT models plus Jinja, compiled into DDL/DML run in the warehouse. It handles dependency ordering via `ref()`, materializations, tests, docs and lineage. It does not extract or load data and is not a scheduler (run it from Airflow, dbt Cloud, etc.).

**16. Materializations: when to use each?**
View: cheap, always fresh, slow to query when stacked. Table: fast reads, rebuilt each run. Incremental: large append/event tables, process only new rows. Ephemeral: inline CTE for tiny reusable logic. Materialized view: warehouse-maintained (adapter support varies, check current docs).
*Follow-ups:* How does an incremental model recover from a bug? (`--full-refresh` or targeted backfill.) What does `unique_key` do? (Enables merge/delete+insert so updates replace rows.)

**17. How does dbt build its DAG and why `ref()` instead of table names?**
`ref('x')` is parsed at compile time to add an edge and is resolved to the right schema/database per target environment. This gives correct run order, environment isolation and lineage. `source()` does the same for raw tables and enables freshness checks.
*Follow-up:* What happens on circular refs? (Compile error.)

**18. dbt tests and data quality.**
Generic tests (unique, not_null, accepted_values, relationships), singular SQL tests, packages (dbt_expectations), source freshness, contracts (check current docs). `dbt build` interleaves run and test so bad upstream models block downstream ones. Severity (`warn`/`error`) and `store_failures` for triage.
*Follow-up:* What can't dbt tests catch? (Business-logic correctness without expectations, cross-system reconciliation, volume anomalies, so add anomaly monitoring.)

**19. Snapshots vs incremental models?**
Snapshots track *changes of mutable source rows* over time (SCD2: `dbt_valid_from/to`), using timestamp or check strategy. Incremental models only keep the latest state (or append facts). Use snapshots when you need history the source does not keep.

**20. Design: daily pipeline loading orders from an OLTP DB into the warehouse, with updates and deletes.**
Prefer CDC (Debezium/managed CDC) into a raw change-log table; staging dedupes to the latest change per key (`row_number` by LSN/ts) and flags deletes; mart applies MERGE (or incremental with soft-delete column). Orchestrate with idempotent, interval-keyed tasks; tests (unique, not_null, row-count vs source); late/out-of-order handled by ordering on source sequence; periodic reconciliation; DLQ for unparseable events; backfill by replaying the log. If CDC is unavailable: watermark on `updated_at` with lookback + daily full key-compare to detect deletes.
*Follow-ups:* How do you backfill a year without disrupting production? How do you prove completeness? (Counts/checksums per partition, reconciliation job.)
