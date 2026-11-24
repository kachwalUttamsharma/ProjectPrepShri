"""Week 3 exercises: orchestration, idempotent loads, dbt-style dependencies.

Stdlib only (sqlite3 for the load exercises; needs SQLite 3.24+ for
`INSERT ... ON CONFLICT DO UPDATE`, which every recent Python ships).
Dates are ISO strings ("2024-01-31") and compare correctly as text.

Replace each `...` with your code. Run:
    ../../.venv/bin/pytest -q
"""
import re
import sqlite3
from datetime import date, timedelta


class CycleError(Exception):
    """Raised when a dependency graph contains a cycle."""


# Exercise 1 -------------------------------------------------------------
def topological_order(deps):
    """`deps` maps node -> set of its UPSTREAM nodes (what must run first).
    Nodes that only appear as upstreams are part of the graph too.
    Return a list of all nodes so every node comes after its upstreams.
    Deterministic: among nodes that are ready at the same time, take them in
    sorted (alphabetical) order. Raise CycleError on a cycle (self-loop too).
    Example: {"load": {"transform"}, "transform": {"extract"}}
             -> ["extract", "transform", "load"]
    Hint: Kahn's algorithm: repeatedly emit nodes with no remaining upstreams.
    """
    ...


# Exercise 2 -------------------------------------------------------------
def run_dag(tasks, deps, max_retries=0):
    """Mini scheduler. `tasks`: {name: zero-arg callable}; `deps` as above
    (names in deps may be a subset of tasks; tasks absent from deps have no
    upstreams). Run tasks in topological order.
      - A task raising an exception is retried up to `max_retries` more times
        (so max_retries+1 attempts in total).
      - If it never succeeds its status is "failed".
      - A task with any upstream whose status is not "success" is NOT run and
        gets "upstream_failed".
    Return {name: "success" | "failed" | "upstream_failed"} for every task.
    Unrelated branches keep running after a failure (like Airflow).
    """
    ...


# Exercise 3 -------------------------------------------------------------
def extract_refs(sql):
    """dbt-style dependency parsing: return the model names referenced via
    {{ ref('name') }} in `sql`, de-duplicated, in order of first appearance.
    Accept single or double quotes and optional whitespace inside the braces:
    {{ref("x")}} and {{ ref('x') }} both count. {{ source(...) }} does not.
    Hint: re.findall with a pattern, then de-dupe preserving order.
    """
    ...


def build_order(models):
    """`models` maps model name -> its SQL text. Work out each model's
    dependencies with extract_refs and return the build order (use
    topological_order). A ref to a model that is not in `models` raises
    KeyError(that_name). Cycles raise CycleError.
    """
    ...


# Exercise 4 -------------------------------------------------------------
def init_users(conn):
    """Provided helper: create the table used by upsert_users."""
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, updated_at TEXT)")


def upsert_users(conn, rows):
    """Idempotent load. `rows` is a list of dicts with keys id, name,
    updated_at. Insert new ids; for existing ids overwrite name and
    updated_at. Running it twice with the same rows must leave the table
    identical. The whole batch is ONE transaction: if any row fails (e.g. a
    missing key) nothing from the batch is written.
    Hint: INSERT ... ON CONFLICT(id) DO UPDATE SET name=excluded.name, ...
    with executemany and named placeholders; `with conn:` commits/rolls back.
    """
    ...


# Exercise 5 -------------------------------------------------------------
def init_incremental(conn):
    """Provided helper: target table + a state table holding watermarks."""
    conn.execute("CREATE TABLE IF NOT EXISTS target (id INTEGER PRIMARY KEY, value TEXT, updated_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS etl_state (name TEXT PRIMARY KEY, watermark TEXT)")


def incremental_load(conn, source_rows, name="job"):
    """High-water-mark incremental load.
    1. Read the watermark for `name` from etl_state (none yet -> load all).
    2. Take source rows (dicts: id, value, updated_at) with
       updated_at > watermark.
    3. Upsert them into `target` by id.
    4. Advance the watermark to the max updated_at of the rows loaded.
    Steps 3 and 4 in ONE transaction, so a crash cannot move the watermark
    without the data. Return the number of rows loaded (0 if none; then the
    watermark is unchanged). Watermarks are per `name`.
    """
    ...


# Exercise 6 -------------------------------------------------------------
def backfill_intervals(start, end):
    """Backfill planner. Given inclusive ISO dates `start` and `end`, return
    one (data_interval_start, data_interval_end) tuple per day, where the end
    is the NEXT day (half-open interval, like Airflow's data interval).
    start > end -> []. Handles month ends and leap years.
    Example: ("2024-01-31", "2024-02-01") ->
             [("2024-01-31", "2024-02-01"), ("2024-02-01", "2024-02-02")]
    Hint: datetime.date.fromisoformat, timedelta(days=1), .isoformat().
    """
    ...


# Exercise 7 -------------------------------------------------------------
def dedupe_latest(rows, key, ts):
    """Keep one row per row[key]: the one with the greatest row[ts]. On a tie
    the LATER row in the input wins. Output order: by first appearance of each
    key. Does not mutate input. This is the "exactly-once effect via dedupe"
    pattern (the SQL equivalent is row_number() ... = 1).
    Applying it to its own output changes nothing.
    """
    ...


# Exercise 8 -------------------------------------------------------------
def init_daily(conn):
    """Provided helper."""
    conn.execute("CREATE TABLE IF NOT EXISTS daily_sales (ds TEXT, sku TEXT, qty INTEGER)")


def overwrite_partition(conn, ds, rows):
    """Partition-overwrite load for one day. In ONE transaction delete every
    daily_sales row with this `ds`, then insert `rows` (dicts with sku, qty)
    stamped with `ds`. Re-running for the same day gives the same table;
    other days are untouched. If an insert fails, the delete is rolled back
    (old data stays).
    """
    ...


# Exercise 9 -------------------------------------------------------------
def process_with_dead_letter(records, handler, max_attempts=3):
    """Call handler(record) for each record. If it raises, retry up to
    `max_attempts` total attempts. A record that never succeeds goes to the
    dead-letter list as (record, str(last_exception)); processing continues
    with the next record (one poison pill must not stop the batch).
    Return (results, dead_letters): results are the handler return values of
    successful records in input order.
    """
    ...
