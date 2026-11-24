import sqlite3
from datetime import datetime, timedelta

import pytest

from exercises import *


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, email TEXT, name TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, amount REAL);
        INSERT INTO customers VALUES (1,'a@x.com','Ann'),(2,'b@x.com','Bob'),(3,'c@x.com','Cy');
        INSERT INTO orders VALUES (10,1,5.0),(11,2,6.0),(12,9,7.0),(13,NULL,8.0),(14,9,1.0),(15,7,2.0);
    """)
    yield c
    c.close()


# 1
def test_not_null_counts_blank_and_missing():
    rows = [{"a": 1}, {"a": None}, {"a": "  "}, {}]
    r = check_not_null(rows, "a")
    assert r.name == "not_null:a" and r.passed is False
    assert r.details["null_count"] == 3 and r.details["total"] == 4
    assert r.details["null_ratio"] == 0.75


def test_not_null_threshold_and_empty():
    rows = [{"a": 1}] * 9 + [{"a": None}]
    assert check_not_null(rows, "a", 0.1).passed
    assert not check_not_null(rows, "a", 0.05).passed
    assert check_not_null([], "a").passed
    assert check_not_null([{"a": 0}, {"a": False}], "a").passed  # 0/False are values


def test_range():
    rows = [{"x": 5}, {"x": -1}, {"x": None}, {"x": 11}, {"x": 10}, {"x": 0}]
    r = check_range(rows, "x", 0, 10)
    assert r.name == "range:x" and not r.passed
    assert r.details["violations"] == [1, 3]
    assert check_range(rows, "x", min_value=-1).details["violations"] == []
    assert check_range([{"x": 1}], "x", 0, 2).passed


def test_run_checks_collects_and_survives_exceptions():
    rows = [{"a": None}]

    def boom():
        raise RuntimeError("db down")

    out = run_checks([lambda: check_not_null(rows, "a"), boom,
                      lambda: check_range([{"a": 1}], "a", 0, 5)])
    assert out["passed"] is False
    assert len(out["results"]) == 3
    assert out["failed"] == ["not_null:a", "boom"]
    assert out["results"][1].details == {"error": "db down"}


def test_run_checks_all_pass():
    out = run_checks([lambda: check_range([{"a": 1}], "a", 0, 5)])
    assert out["passed"] and out["failed"] == []
    assert run_checks([])["passed"] is True


# 2
def test_duplicates_single_and_composite():
    rows = [{"id": 1, "d": "x"}, {"id": 2, "d": "x"}, {"id": 1, "d": "y"}, {"id": 1, "d": "x"}]
    assert find_duplicate_keys(rows, ["id"]) == {(1,): [0, 2, 3]}
    assert find_duplicate_keys(rows, ["id", "d"]) == {(1, "x"): [0, 3]}
    assert find_duplicate_keys([{"id": 1}], ["id"]) == {}
    assert find_duplicate_keys([], ["id"]) == {}


# 3
OLD = {"id": {"type": "int"}, "name": {"type": "string", "default": ""}}


def test_backward_add_required_field_breaks():
    new = {**OLD, "email": {"type": "string"}}
    v = check_schema_compat(OLD, new, "backward")
    assert len(v) == 1 and "email" in v[0]
    assert check_schema_compat(OLD, new, "forward") == []


def test_backward_add_with_default_ok_and_remove_ok():
    new = {**OLD, "email": {"type": "string", "default": None}}
    assert check_schema_compat(OLD, new, "backward") == []
    removed = {"id": {"type": "int"}}
    assert check_schema_compat(OLD, removed, "backward") == []


def test_forward_remove_required_breaks():
    new = {"name": {"type": "string", "default": ""}}
    v = check_schema_compat(OLD, new, "forward")
    assert len(v) == 1 and "id" in v[0]
    assert check_schema_compat(OLD, new, "backward") == []


def test_type_change_breaks_all_modes():
    new = {"id": {"type": "string"}, "name": OLD["name"]}
    for m in ("backward", "forward", "full"):
        v = check_schema_compat(OLD, new, m)
        assert len(v) == 1 and "id" in v[0]


def test_full_combines_and_sorted():
    new = {"name": OLD["name"], "zed": {"type": "int"}}
    v = check_schema_compat(OLD, new, "full")
    assert len(v) == 2 and v == sorted(v)
    assert any("zed" in s for s in v) and any("id" in s for s in v)
    assert check_schema_compat(OLD, OLD, "full") == []
    with pytest.raises(ValueError):
        check_schema_compat(OLD, OLD, "sideways")


# 4
def test_freshness():
    now = datetime(2025, 1, 2, 12, 0)
    ok = check_freshness(now - timedelta(hours=1), now, timedelta(hours=2))
    assert ok.passed and ok.name == "freshness"
    assert ok.details["age_seconds"] == 3600 and ok.details["max_age_seconds"] == 7200
    assert check_freshness(now - timedelta(hours=2), now, timedelta(hours=2)).passed  # boundary
    assert not check_freshness(now - timedelta(hours=3), now, timedelta(hours=2)).passed
    assert check_freshness(now + timedelta(minutes=1), now, timedelta(hours=2)).passed
    n = check_freshness(None, now, timedelta(hours=2))
    assert not n.passed and n.details["age_seconds"] is None


# 5
HIST = [100, 102, 98, 101, 99, 103, 97, 100]


def test_volume_normal_vs_anomalous():
    assert detect_volume_anomaly(HIST, 101) is False
    assert detect_volume_anomaly(HIST, 20) is True
    assert detect_volume_anomaly(HIST, 500) is True


def test_volume_robust_to_past_outage():
    hist = HIST + [0, 0]   # outages in history must not hide a new outage
    assert detect_volume_anomaly(hist, 0) is True
    assert detect_volume_anomaly(hist, 100) is False


def test_volume_edge_cases():
    assert detect_volume_anomaly([100, 100, 100, 100], 100) is False
    assert detect_volume_anomaly([100, 100, 100, 100], 101) is True
    assert detect_volume_anomaly([1, 2], 1000) is False


# 6
def test_orphans(conn):
    assert find_orphans(conn, "orders", "customer_id", "customers", "id") == [7, 9]


def test_no_orphans(conn):
    conn.execute("DELETE FROM orders WHERE customer_id IN (7, 9)")
    assert find_orphans(conn, "orders", "customer_id", "customers", "id") == []


# 7
def test_mask_email():
    assert mask_email("alice@example.com") == "a****@example.com"
    assert mask_email("b@x.org") == "b@x.org"
    assert mask_email("nope") == "***"
    assert mask_email("a@b@c") == "***"


def test_mask_phone():
    assert mask_phone("+1 (415) 555-0134") == "+* (***) ***-0134"
    assert mask_phone("4155550134") == "******0134"
    assert mask_phone("123") == "123"
    assert mask_phone("") == ""


# 8
@pytest.fixture
def two(conn):
    conn.executescript("""
        CREATE TABLE src (id INTEGER PRIMARY KEY, a TEXT, b INTEGER);
        CREATE TABLE dst (id INTEGER PRIMARY KEY, a TEXT, b INTEGER);
        INSERT INTO src VALUES (1,'x',1),(2,'y',2),(3,'z',3);
        INSERT INTO dst VALUES (3,'z',3),(1,'x',1),(2,'y',2);
    """)
    return conn


def test_reconcile_identical_regardless_of_order(two):
    r = reconcile_tables(two, "src", "dst", "id", ["a", "b"])
    assert r["count_a"] == r["count_b"] == 3
    assert r["checksum_match"] is True and r["ok"] is True
    assert r["only_in_a"] == [] and r["only_in_b"] == [] and r["mismatched"] == []


def test_reconcile_finds_differences(two):
    two.execute("DELETE FROM dst WHERE id = 1")
    two.execute("INSERT INTO dst VALUES (9,'q',9)")
    two.execute("UPDATE dst SET b = 99 WHERE id = 2")
    r = reconcile_tables(two, "src", "dst", "id", ["a", "b"])
    assert r["only_in_a"] == [1] and r["only_in_b"] == [9] and r["mismatched"] == [2]
    assert r["checksum_match"] is False and r["ok"] is False
    assert r["count_a"] == 3 and r["count_b"] == 3  # counts equal but data differs


def test_reconcile_ignores_unlisted_columns(two):
    two.execute("UPDATE dst SET b = 99 WHERE id = 2")
    r = reconcile_tables(two, "src", "dst", "id", ["a"])
    assert r["ok"] is True and r["checksum_match"] is True


# 9
def test_psi_identical_is_zero():
    xs = list(range(100))
    assert population_stability_index(xs, xs) == pytest.approx(0.0, abs=1e-9)


def test_psi_shift_detected():
    base = list(range(100))
    small = [x + 3 for x in base]
    big = [x + 60 for x in base]
    assert population_stability_index(base, small) < 0.1
    assert population_stability_index(base, big) > 0.25
    assert population_stability_index(base, big) > population_stability_index(base, small)


def test_psi_nonneg_clamp_and_constant():
    base = list(range(10))
    assert population_stability_index(base, [1000] * 10) > 0.25  # clamped to last bin
    assert population_stability_index([5, 5, 5], [1, 2, 3]) == 0.0


# 10
def test_erase_subject(conn):
    n = erase_subject(conn, "customers", "id", 2, ["email", "name"])
    assert n == 1
    assert conn.execute("SELECT email, name FROM customers WHERE id=2").fetchone() == (None, None)
    assert conn.execute("SELECT email FROM customers WHERE id=1").fetchone() == ("a@x.com",)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 3


def test_erase_subject_multiple_rows_none_and_invalid(conn):
    assert erase_subject(conn, "orders", "customer_id", 9, ["amount"]) == 2
    assert erase_subject(conn, "orders", "customer_id", 12345, ["amount"]) == 0
    with pytest.raises(ValueError):
        erase_subject(conn, "orders", "customer_id", 9, [])
