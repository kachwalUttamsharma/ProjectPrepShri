import pytest

from exercises import *


# 1
def test_partition_deterministic_and_in_range():
    seen = {partition_for_key(f"user-{i}", 6) for i in range(200)}
    assert seen <= set(range(6))
    assert len(seen) > 3  # keys spread out
    assert partition_for_key("abc", 8) == partition_for_key("abc", 8)


def test_partition_str_bytes_same():
    assert partition_for_key("k1", 10) == partition_for_key(b"k1", 10)


def test_partition_known_value():
    import zlib
    assert partition_for_key("order-42", 7) == zlib.crc32(b"order-42") % 7


def test_partition_bad_count():
    with pytest.raises(ValueError):
        partition_for_key("x", 0)


# 2
def test_range_assignment():
    r = assign_partitions(range(7), ["c", "a", "b"], "range")
    assert r == {"a": [0, 1, 2], "b": [3, 4], "c": [5, 6]}


def test_round_robin_assignment():
    r = assign_partitions([4, 3, 2, 1, 0], ["b", "a"], "round_robin")
    assert r == {"a": [0, 2, 4], "b": [1, 3]}


def test_more_consumers_than_partitions_idle():
    r = assign_partitions([0, 1], ["a", "b", "c"])
    assert r == {"a": [0], "b": [1], "c": []}


def test_assign_edge_cases():
    assert assign_partitions([0, 1], []) == {}
    with pytest.raises(ValueError):
        assign_partitions([0], ["a"], "sticky")
    all_p = sorted(sum(assign_partitions(range(10), list("abc")).values(), []))
    assert all_p == list(range(10))


# 3
def test_tumbling():
    assert tumbling_window(125, 60) == (120, 180)
    assert tumbling_window(120, 60) == (120, 180)  # start inclusive
    assert tumbling_window(179, 60) == (120, 180)
    assert tumbling_window(180, 60) == (180, 240)  # end exclusive


def test_sliding():
    assert sliding_windows(25, 30, 10) == [(0, 30), (10, 40), (20, 50)]
    assert sliding_windows(5, 30, 10) == [(0, 30)]  # no negative starts
    assert sliding_windows(30, 30, 10) == [(10, 40), (20, 50), (30, 60)]


def test_sliding_hopping_gap():
    # slide > size: some events fall in no window
    assert sliding_windows(15, 5, 10) == []
    assert sliding_windows(12, 5, 10) == [(10, 15)]


def test_sessions():
    assert session_windows([1, 2, 10, 11, 30], gap=5) == [(1, 2, 2), (10, 11, 2), (30, 30, 1)]
    assert session_windows([30, 1, 11, 2, 10], gap=5) == [(1, 2, 2), (10, 11, 2), (30, 30, 1)]
    assert session_windows([], 5) == []


def test_session_gap_boundary():
    assert session_windows([0, 5], gap=5) == [(0, 5, 2)]   # exactly gap: same session
    assert session_windows([0, 6], gap=5) == [(0, 0, 1), (6, 6, 1)]


# 4
def test_watermark_initial():
    w = WatermarkWindower(10, 5)
    assert w.watermark == float("-inf")


def test_window_closes_when_watermark_passes():
    w = WatermarkWindower(10, 5)
    assert w.process(1, "a") == []
    assert w.process(9, "b") == []       # wm 4
    assert w.process(14, "c") == []      # wm 9 < 10
    closed = w.process(15, "d")          # wm 10 -> closes [0,10)
    assert closed == [(0, 10, ["a", "b"])]
    assert w.watermark == 10


def test_out_of_order_within_delay_is_accepted():
    w = WatermarkWindower(10, 5)
    w.process(12, "x")                   # wm 7
    assert w.process(3, "late-ish") == []  # window [0,10) still open
    assert w.late == []
    closed = w.process(20, "y")          # wm 15 closes only [0,10)
    assert closed == [(0, 10, ["late-ish"])]
    assert w.open  # window [20,30) at least remains


def test_late_event_dropped_to_side_output():
    w = WatermarkWindower(10, 0)
    w.process(5, "a")
    w.process(25, "b")                   # wm 25 closes [0,10), [..]
    assert w.process(7, "too-late") == []
    assert w.late == [(7, "too-late")]


def test_multiple_windows_close_sorted():
    w = WatermarkWindower(10, 0)
    w.process(1, "a")
    w.process(11, "b")                   # wm 11 closes [0,10)
    out = w.process(35, "c")             # wm 35 closes [10,20)
    assert out == [(10, 20, ["b"])]
    assert w.flush() == [(30, 40, ["c"])]
    assert w.flush() == []


def test_closed_window_gets_late_event_exactly_at_boundary():
    w = WatermarkWindower(10, 0)
    w.process(10, "a")                   # wm 10, window [0,10) end == wm -> closed/late
    assert w.process(9, "z") == []
    assert w.late == [(9, "z")]


# 5
def test_log_append_and_read():
    log = InMemoryLog()
    assert [log.append("k", i) for i in range(3)] == [0, 1, 2]
    assert log.end_offset() == 3
    assert [r.value for r in log.read(1)] == [1, 2]
    assert [r.offset for r in log.read(0, 2)] == [0, 1]
    assert log.read(3) == []
    assert log.read(0)[0] == Record(0, "k", 0)


def test_poll_advances_position_not_committed():
    log = InMemoryLog()
    for i in range(5):
        log.append(None, i)
    assert [r.value for r in log.poll("g", 2)] == [0, 1]
    assert [r.value for r in log.poll("g", 2)] == [2, 3]
    assert log.committed("g") == 0


def test_crash_replays_uncommitted():
    log = InMemoryLog()
    for i in range(5):
        log.append(None, i)
    log.poll("g", 2)
    log.commit("g")
    log.poll("g", 2)             # processed 2,3 but crash before commit
    log.restart("g")
    assert [r.value for r in log.poll("g")] == [2, 3, 4]
    assert log.committed("g") == 2


def test_groups_independent_and_seek_replay():
    log = InMemoryLog()
    for i in range(3):
        log.append(None, i)
    assert len(log.poll("a")) == 3
    assert len(log.poll("b", 1)) == 1
    assert log.poll("a") == []
    log.seek("a", 0)
    assert len(log.poll("a")) == 3
    assert log.committed("zzz") == 0


def test_new_data_visible_to_existing_consumer():
    log = InMemoryLog()
    log.append(None, "x")
    log.poll("g")
    log.append(None, "y")
    assert [r.value for r in log.poll("g")] == ["y"]


# 6
def test_dedupe_basic():
    d = Deduper()
    assert d.is_duplicate("a") is False
    assert d.is_duplicate("a") is True
    assert d.is_duplicate("b") is False


def test_dedupe_capacity_evicts_lru():
    d = Deduper(capacity=2)
    d.is_duplicate("a")
    d.is_duplicate("b")
    d.is_duplicate("a")          # refresh a; b is now least recent
    d.is_duplicate("c")          # evicts b
    assert d.is_duplicate("a") is True
    assert d.is_duplicate("b") is False   # forgotten -> looks new


# 7
def test_lag_basic():
    r = consumer_lag({0: 10, 1: 5}, {0: 7, 1: 5})
    assert r["per_partition"] == {0: 3, 1: 0}
    assert r["total"] == 3 and r["max"] == 3 and r["max_partition"] == 0


def test_lag_missing_and_negative():
    r = consumer_lag({0: 10, 1: 5, 2: 5}, {0: 7, 2: 9})
    assert r["per_partition"] == {0: 3, 1: 5, 2: 0}
    assert r["total"] == 8
    assert r["max_partition"] == 1


def test_lag_ties_and_empty():
    assert consumer_lag({3: 4, 1: 4}, {})["max_partition"] == 1
    e = consumer_lag({}, {})
    assert e == {"per_partition": {}, "total": 0, "max": 0, "max_partition": None}


# 8
def test_compact_keeps_latest():
    out = compact_log([("a", 1), ("b", 2), ("a", 3)])
    assert out == [Record(1, "b", 2), Record(2, "a", 3)]


def test_compact_tombstone_deletes():
    out = compact_log([("a", 1), ("b", 2), ("a", None), ("c", 3)])
    assert out == [Record(1, "b", 2), Record(3, "c", 3)]


def test_compact_resurrect_after_tombstone():
    out = compact_log([("a", 1), ("a", None), ("a", 5)])
    assert out == [Record(2, "a", 5)]
    assert compact_log([]) == []


# 9
def test_dlq_all_ok():
    res, dead = process_with_dlq([1, 2], lambda m: m * 2)
    assert res == [(1, 2), (2, 4)] and dead == []


def test_dlq_retries_then_succeeds():
    calls = {"n": 0}

    def flaky(m):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    res, dead = process_with_dlq(["x"], flaky, max_attempts=3)
    assert res == [("x", "ok")] and dead == [] and calls["n"] == 3


def test_dlq_poison_message_parked_batch_continues():
    def h(m):
        if m == "bad":
            raise ValueError("boom")
        return m.upper()

    res, dead = process_with_dlq(["a", "bad", "b"], h, max_attempts=2)
    assert res == [("a", "A"), ("b", "B")]
    assert dead == [{"message": "bad", "error": "boom", "attempts": 2}]


# 10
def test_partitions_needed():
    assert partitions_needed(100, 10, 20) == 10
    assert partitions_needed(100, 50, 10) == 10   # consumer-bound
    assert partitions_needed(105, 10, 100) == 11  # round up


def test_partitions_headroom_and_float_noise():
    assert partitions_needed(100, 10, 20, headroom=2) == 20
    assert partitions_needed(0.3, 0.1, 0.1) == 3
    assert partitions_needed(1, 1000, 1000) == 1


def test_partitions_bad_args():
    with pytest.raises(ValueError):
        partitions_needed(0, 1, 1)
    with pytest.raises(ValueError):
        partitions_needed(1, 1, -1)
