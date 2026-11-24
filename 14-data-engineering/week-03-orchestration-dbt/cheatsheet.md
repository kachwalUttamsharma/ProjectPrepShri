# Orchestration and dbt cheatsheet

**Airflow**: DAG -> tasks (operator instances) -> task instances per run. Scheduler creates runs and queues tasks; executor (Local/Celery/K8s) runs them; metadata DB holds state.
**Data interval**: run `ds=2024-05-01` covers [05-01, 05-02) and fires after it ends. Use `data_interval_start/end`, not `now()`.
**catchup=True** creates runs for every missed interval. **Backfill** = rerun history; needs idempotent tasks.
**XCom** = small metadata only. **Sensors**: reschedule mode/deferrable. **Retries** + backoff; **trigger rules** for cleanup tasks (`all_done`).
**Pitfalls**: heavy top-level DAG code, non-idempotent appends, giant XComs, huge/tiny tasks, poke sensors, dynamic start_date.
**Alternatives**: Dagster (assets), Prefect (Python-first), Step Functions (state machines), managed Airflow (MWAA/Composer).

**dbt**: model = SELECT; materializations view/table/incremental/ephemeral. `ref()` = DAG edges, `source()` = raw inputs. Tests: unique, not_null, accepted_values, relationships. Snapshots = SCD2. `dbt build` = run + test in order. Incremental: `is_incremental()`, `unique_key`, strategy merge/delete+insert/insert_overwrite (adapter-specific).

**Load patterns**: full refresh | watermark (misses deletes, late updates) | CDC (log, handles deletes) | MERGE/upsert | partition overwrite (idempotent by design).
**Idempotency recipe**: deterministic key or partition + overwrite/merge + transaction. Advance watermark in the same transaction as the data.
**Exactly-once effect** = at-least-once delivery + idempotent write/dedupe (`row_number() ... = 1`).
**Late data**: lookback window, reprocess last N days, event_time vs ingested_at.
**Failure handling**: retry transient, DLQ poison records, alert on failure and on missing success, row-count/freshness tests.
