import sqlite3

import pytest

from exercises import *


# 1 topological order
def test_topological_order_linear_and_diamond():
    deps = {"load": {"transform"}, "transform": {"extract"}, "extract": set()}
    assert topological_order(deps) == ["extract", "transform", "load"]
    d = {"a": set(), "b": {"a"}, "c": {"a"}, "d": {"b", "c"}}
    assert topological_order(d) == ["a", "b", "c", "d"]


def test_topological_order_includes_implicit_nodes_and_is_deterministic():
    assert topological_order({"b": {"a"}}) == ["a", "b"]
    assert topological_order({"z": set(), "m": set(), "a": set()}) == ["a", "m", "z"]
    assert topological_order({}) == []


def test_topological_order_cycle():
    with pytest.raises(CycleError):
        topological_order({"a": {"b"}, "b": {"a"}})
    with pytest.raises(CycleError):
        topological_order({"a": {"a"}})


# 2 run dag
def test_run_dag_order_and_success():
    log = []
    tasks = {n: (lambda n=n: log.append(n)) for n in "abc"}
    st = run_dag(tasks, {"b": {"a"}, "c": {"b"}})
    assert log == ["a", "b", "c"]
    assert st == {"a": "success", "b": "success", "c": "success"}


def test_run_dag_retries_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("boom")

    st = run_dag({"x": flaky}, {}, max_retries=2)
    assert st == {"x": "success"} and calls["n"] == 3


def test_run_dag_failure_skips_downstream():
    ran = []

    def bad():
        raise ValueError

    tasks = {"a": bad, "b": lambda: ran.append("b"), "c": lambda: ran.append("c")}
    st = run_dag(tasks, {"b": {"a"}}, max_retries=1)
    assert st == {"a": "failed", "b": "upstream_failed", "c": "success"}
    assert ran == ["c"]


# 3 refs
def test_extract_refs():
    sql = """select * from {{ ref('stg_orders') }} o
    join {{ ref("stg_users") }} u on 1=1
    join {{ref('stg_orders')}} again"""
    assert extract_refs(sql) == ["stg_orders", "stg_users"]
    assert extract_refs("select 1") == []
    assert extract_refs("select * from {{ source('raw', 'x') }}") == []


def test_build_order():
    models = {
        "orders_mart": "select * from {{ ref('stg_orders') }} join {{ ref('stg_users') }}",
        "stg_orders": "select * from raw.orders",
        "stg_users": "select * from raw.users",
        "report": "select * from {{ ref('orders_mart') }}",
    }
    assert build_order(models) == ["stg_orders", "stg_users", "orders_mart", "report"]


def test_build_order_errors():
    with pytest.raises(KeyError):
        build_order({"a": "select * from {{ ref('missing') }}"})
    with pytest.raises(CycleError):
        build_order({"a": "{{ ref('b') }}", "b": "{{ ref('a') }}"})


# 4 upsert
def rows_of(conn, q):
    return conn.execute(q).fetchall()


def test_upsert_idempotent():
    c = sqlite3.connect(":memory:")
    init_users(c)
    batch = [{"id": 1, "name": "a", "updated_at": "t1"}, {"id": 2, "name": "b", "updated_at": "t1"}]
    upsert_users(c, batch)
    first = rows_of(c, "select * from users order by id")
    upsert_users(c, batch)
    upsert_users(c, batch)
    assert rows_of(c, "select * from users order by id") == first
    assert len(first) == 2


def test_upsert_updates_existing():
    c = sqlite3.connect(":memory:")
    init_users(c)
    upsert_users(c, [{"id": 1, "name": "a", "updated_at": "t1"}])
    upsert_users(c, [{"id": 1, "name": "A2", "updated_at": "t2"}, {"id": 3, "name": "c", "updated_at": "t2"}])
    assert rows_of(c, "select id, name, updated_at from users order by id") == [
        (1, "A2", "t2"), (3, "c", "t2")]


def test_upsert_is_atomic():
    c = sqlite3.connect(":memory:")
    init_users(c)
    bad = [{"id": 1, "name": "a", "updated_at": "t"}, {"id": 2, "name": "b"}]  # missing key
    with pytest.raises(Exception):
        upsert_users(c, bad)
    assert rows_of(c, "select count(*) from users") == [(0,)]


# 5 incremental
SRC = [
    {"id": 1, "value": "a", "updated_at": "2024-01-01"},
    {"id": 2, "value": "b", "updated_at": "2024-01-02"},
]


def test_incremental_load_watermark():
    c = sqlite3.connect(":memory:")
    init_incremental(c)
    assert incremental_load(c, SRC, "j") == 2
    assert incremental_load(c, SRC, "j") == 0  # nothing new
    assert rows_of(c, "select watermark from etl_state where name='j'") == [("2024-01-02",)]
    src2 = SRC + [{"id": 2, "value": "b2", "updated_at": "2024-01-05"},
                  {"id": 3, "value": "c", "updated_at": "2024-01-04"}]
    assert incremental_load(c, src2, "j") == 2
    assert rows_of(c, "select id, value from target order by id") == [(1, "a"), (2, "b2"), (3, "c")]
    assert rows_of(c, "select watermark from etl_state where name='j'") == [("2024-01-05",)]


def test_incremental_watermarks_are_per_job():
    c = sqlite3.connect(":memory:")
    init_incremental(c)
    incremental_load(c, SRC, "one")
    assert incremental_load(c, SRC, "two") == 2


# 6 backfill
def test_backfill_intervals():
    assert backfill_intervals("2024-02-27", "2024-03-01") == [
        ("2024-02-27", "2024-02-28"), ("2024-02-28", "2024-02-29"),
        ("2024-02-29", "2024-03-01"), ("2024-03-01", "2024-03-02")]
    assert backfill_intervals("2024-01-01", "2024-01-01") == [("2024-01-01", "2024-01-02")]
    assert backfill_intervals("2024-01-02", "2024-01-01") == []


# 7 dedupe
def test_dedupe_latest():
    rows = [
        {"id": 1, "v": "old", "ts": 1},
        {"id": 2, "v": "x", "ts": 5},
        {"id": 1, "v": "new", "ts": 3},
        {"id": 1, "v": "mid", "ts": 2},
    ]
    out = dedupe_latest(rows, "id", "ts")
    assert out == [{"id": 1, "v": "new", "ts": 3}, {"id": 2, "v": "x", "ts": 5}]


def test_dedupe_tie_last_wins_and_idempotent():
    rows = [{"id": 1, "v": "first", "ts": 1}, {"id": 1, "v": "second", "ts": 1}]
    out = dedupe_latest(rows, "id", "ts")
    assert out == [{"id": 1, "v": "second", "ts": 1}]
    assert dedupe_latest(out, "id", "ts") == out
    assert dedupe_latest([], "id", "ts") == []


# 8 partition overwrite
def test_overwrite_partition_idempotent_and_isolated():
    c = sqlite3.connect(":memory:")
    init_daily(c)
    overwrite_partition(c, "2024-01-01", [{"sku": "a", "qty": 1}, {"sku": "b", "qty": 2}])
    overwrite_partition(c, "2024-01-02", [{"sku": "a", "qty": 9}])
    overwrite_partition(c, "2024-01-01", [{"sku": "a", "qty": 1}, {"sku": "b", "qty": 2}])
    assert rows_of(c, "select * from daily_sales order by ds, sku") == [
        ("2024-01-01", "a", 1), ("2024-01-01", "b", 2), ("2024-01-02", "a", 9)]


def test_overwrite_partition_replaces_and_rolls_back():
    c = sqlite3.connect(":memory:")
    init_daily(c)
    overwrite_partition(c, "d1", [{"sku": "a", "qty": 1}])
    overwrite_partition(c, "d1", [{"sku": "z", "qty": 7}])
    assert rows_of(c, "select sku from daily_sales") == [("z",)]
    with pytest.raises(Exception):
        overwrite_partition(c, "d1", [{"sku": "q", "qty": 1}, {"sku": "bad"}])
    assert rows_of(c, "select sku from daily_sales") == [("z",)]  # old data intact


# 9 dead letter
def test_dead_letter_routing_and_retries():
    attempts = {}

    def handler(rec):
        attempts[rec] = attempts.get(rec, 0) + 1
        if rec == "bad":
            raise ValueError("cannot parse")
        if rec == "flaky" and attempts[rec] < 2:
            raise RuntimeError("transient")
        return rec.upper()

    ok, dead = process_with_dead_letter(["a", "bad", "flaky", "b"], handler, max_attempts=3)
    assert ok == ["A", "FLAKY", "B"]
    assert dead == [("bad", "cannot parse")]
    assert attempts["bad"] == 3 and attempts["flaky"] == 2 and attempts["a"] == 1


def test_dead_letter_empty_and_single_attempt():
    assert process_with_dead_letter([], str) == ([], [])
    ok, dead = process_with_dead_letter([1], lambda r: 1 / 0, max_attempts=1)
    assert ok == [] and dead[0][0] == 1
