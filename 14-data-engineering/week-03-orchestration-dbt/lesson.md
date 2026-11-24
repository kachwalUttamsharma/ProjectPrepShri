# Week 3: Orchestration, dbt and reliable loads

Airflow/dbt snippets are illustrative and **not run here**. The exercises use stdlib + sqlite3 to practise the underlying ideas.

## 1. Batch ETL vs ELT
- **ETL**: transform before loading (on a separate engine). **ELT**: load raw data into the warehouse/lake, transform there with SQL (dbt). ELT dominates with cheap storage and scalable warehouses; it keeps raw data for replays.
- Layers (medallion/staging): raw/bronze -> cleaned/staging/silver -> marts/gold.
- An **orchestrator** schedules, orders, retries and observes jobs; it should not do the heavy compute itself (it triggers Spark/dbt/warehouse SQL).

## 2. Airflow essentials
- **DAG**: directed acyclic graph of **tasks** with a schedule. **Operator** = task template (Bash, Python, SQL, provider operators); a task is an operator instance; a **task instance** is a task for one DAG run.
- Components: scheduler (parses DAG files, creates runs, queues tasks), executor (Local, Celery, Kubernetes; decides where tasks run), workers, metadata DB, webserver/UI, triggerer (deferrable operators).
- **Logical date / data interval**: a daily run labelled `2024-05-01` processes data of `[2024-05-01, 2024-05-02)` and starts *after* that interval ends. Use `data_interval_start/end` (templated `{{ data_interval_start }}`, `{{ ds }}`) never `datetime.now()` inside tasks. Airflow 2.2+ naming; "execution_date" is legacy (check current docs).
- **catchup**: if True, scheduler creates a run for every missed interval since `start_date`. **Backfill** = rerun a historical range (`airflow dags backfill`, or clear tasks/trigger runs; behaviour changed in Airflow 3, check current docs).
- **Retries / retry_delay / exponential backoff**, `execution_timeout`, **SLAs** (deprecated/reworked in recent versions, check current docs; many teams alert via callbacks/Deadline alerts instead), trigger rules (`all_success` default, `all_done`, `one_failed`).
- **XCom**: small metadata between tasks (stored in the metadata DB). Never pass dataframes; pass paths/ids. The TaskFlow API (`@task`) wraps this.
- **Sensors**: wait for a condition (file, partition, upstream DAG). Use `mode="reschedule"` or deferrable operators so they do not hog worker slots.
- Pools and concurrency limits protect downstream systems. Datasets/assets (data-aware scheduling) trigger DAGs when upstream data updates (naming changed in Airflow 3, check current docs).

```python
# not run here: Airflow 2.x style
from datetime import datetime, timedelta
from airflow.decorators import dag, task

@dag(schedule="@daily", start_date=datetime(2024, 1, 1), catchup=False,
     default_args={"retries": 3, "retry_delay": timedelta(minutes=5)})
def sales_pipeline():
    @task
    def extract(data_interval_start=None, data_interval_end=None):
        # idempotent: write to a path keyed by the interval, overwrite if it exists
        return f"s3://lake/raw/sales/ds={data_interval_start:%Y-%m-%d}/"

    @task
    def load(path: str):
        ...  # MERGE/partition overwrite, not blind INSERT

    load(extract())

sales_pipeline()
```

### Pitfalls
- Non-idempotent tasks (append on retry -> duplicates).
- Heavy top-level code in DAG files (scheduler re-parses constantly: no API/DB calls at import).
- `datetime.now()`/`Variable.get` at parse time; dynamic `start_date`.
- Big XComs; tasks sharing local disk (workers differ).
- Too fine tasks (scheduler overhead, thousands of tiny tasks) or too coarse (one 4-hour task: retry redoes everything). Aim for tasks that are meaningful, restartable units.
- Sensors in poke mode eating slots; no pools; cross-DAG deps by time guessing instead of datasets/ExternalTaskSensor.
- Dynamic DAGs generated from config (loops, or dynamic task mapping `.expand()`): fine, but keep generation cheap and deterministic.

## 3. Alternatives
- **Dagster**: asset-centric (declare data assets and their lineage), strong local dev/testing, IO managers.
- **Prefect**: Python-first flows/tasks, dynamic by default, hybrid execution.
- **AWS Step Functions**: managed state machines (JSON/ASL) for serverless workflows, retries/catch built in; not data-aware.
- Others: Mage, Kestra, cloud-native (Cloud Composer/MWAA are managed Airflow), Databricks Workflows.
Trade-off axes: task-centric vs asset-centric, scheduling model, ops burden, ecosystem of operators, testing story.

## 4. dbt
- A **model** is a `SELECT` in a `.sql` file; dbt wraps it in DDL per its **materialization**: `view`, `table`, `incremental`, `ephemeral` (CTE inlined), plus materialized views.
- `{{ ref('model') }}` builds the dependency graph (DAG) and resolves schema names per environment; `{{ source('raw', 'orders') }}` declares external raw tables (with freshness checks).
- **Tests**: generic (`unique`, `not_null`, `accepted_values`, `relationships`) in YAML, and singular SQL tests. **Docs**: `dbt docs generate` produces lineage and column docs from YAML.
- **Snapshots**: SCD Type 2 history of mutable source rows (`check` or `timestamp` strategy).
- **Incremental models** (not run here):
```sql
-- models/fct_events.sql
{{ config(materialized='incremental', unique_key='event_id', incremental_strategy='merge') }}
select event_id, user_id, event_ts, payload
from {{ ref('stg_events') }}
{% if is_incremental() %}
where event_ts > (select max(event_ts) from {{ this }}) - interval '3 hours'  -- lookback for late data
{% endif %}
```
Strategies (`merge`, `delete+insert`, `insert_overwrite`, `append`; availability is adapter-specific, check current docs). `--full-refresh` rebuilds. Commands: `dbt run`, `test`, `build` (run+test in DAG order), `--select model+`, state-based `--select state:modified+`.
- Jinja macros, packages (dbt_utils), seeds (small CSVs), exposures; contracts and model versions in newer versions (check current docs).

## 5. Incremental loading patterns
| Pattern | How | Catches deletes? | Notes |
|---|---|---|---|
| Full refresh | truncate + reload | yes | simple, costly at scale |
| Watermark / high-water mark | `updated_at > last` | no (unless soft deletes) | needs reliable monotonic column; misses late updates with older timestamps; use lookback window |
| CDC (log-based, e.g. Debezium) | stream of insert/update/delete events | yes | ordering and schema changes matter; apply with merge |
| Upsert / MERGE | match on key, update or insert | only if delete flag | the load primitive for watermark/CDC |
| Partition overwrite | replace whole partition (day) | per partition | naturally idempotent, ideal for immutable-day facts |
Store the watermark in the same transaction as the data, or derive it from the target (`max(updated_at)`), never advance it first.

## 6. Idempotency and exactly-once effect
- **Idempotent**: running a task N times has the same effect as once. Needed because retries, backfills and manual reruns *will* happen.
- Recipes: deterministic output location keyed by the logical date (overwrite); MERGE on a business key; delete-then-insert for a partition inside a transaction; write to staging then atomic swap/rename; dedupe by `row_number() over (partition by key order by updated_at desc, ingested_at desc) = 1`.
- True exactly-once delivery is not possible in general; you build **at-least-once delivery + idempotent processing = exactly-once effect**.
- Avoid in tasks: `now()`, random values, appends without keys, side effects (emails) without guards.

## 7. Backfills, late data, retries, DLQ
- Backfill: re-run historical intervals using the logical date; code must not depend on "today". Parallelism limits; downstream consumers should be told.
- **Late data**: events arrive after their interval was processed. Options: lookback window, reprocess the last N partitions every run, watermarks with allowed lateness (streaming), bi-temporal columns (event_time vs ingested_at), accept and reconcile periodically.
- **Retries**: for transient errors, with backoff and jitter; do not retry deterministic failures forever. **Dead-letter queue/table**: bad records are diverted with the error and context so the batch continues; monitor its size, support replays.
- Observability: row-count and freshness checks, data-quality tests (dbt tests, Great Expectations/Soda), alerts on failure and on *absence* of success, lineage.

## 8. Exercises map
1 topological_order, 2 run_dag with retries, 3 ref() parsing + build order, 4 idempotent upsert, 5 watermark incremental load, 6 backfill intervals, 7 dedupe latest, 8 partition overwrite, 9 dead-letter handling.
