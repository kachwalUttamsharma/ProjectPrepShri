from collections import Counter

import pytest

from exercises import *


def canon(rows):
    return sorted(tuple(sorted(r.items())) for r in rows)


# 1 hash_partition
def test_hash_partition_preserves_rows_and_count():
    rows = [{"k": i % 7, "v": i} for i in range(50)]
    parts = hash_partition(rows, "k", 4)
    assert len(parts) == 4
    assert sum(len(p) for p in parts) == 50
    assert canon([r for p in parts for r in p]) == canon(rows)


def test_hash_partition_same_key_same_partition():
    rows = [{"k": i % 5, "v": i} for i in range(100)]
    parts = hash_partition(rows, "k", 3)
    where = {}
    for i, p in enumerate(parts):
        for r in p:
            assert where.setdefault(r["k"], i) == i


def test_hash_partition_stable_order_within_partition():
    rows = [{"k": "a", "v": i} for i in range(5)]
    parts = hash_partition(rows, "k", 2)
    flat = [r["v"] for p in parts for r in p]
    assert flat == [0, 1, 2, 3, 4]


# 2 wordcount
def test_wordcount_shuffle():
    lines = ["the cat sat", "The dog sat", "the end"]
    assert wordcount_shuffle(lines, 3) == {"the": 3, "cat": 1, "sat": 2, "dog": 1, "end": 1}


def test_wordcount_independent_of_partitions():
    lines = ["a b a c b a"] * 5
    assert wordcount_shuffle(lines, 1) == wordcount_shuffle(lines, 7) == {"a": 15, "b": 10, "c": 5}
    assert wordcount_shuffle([], 2) == {}


# 3 skew
def test_skew_ratio():
    assert skew_ratio([10, 10, 10, 10]) == pytest.approx(1.0)
    assert skew_ratio([1, 1, 1, 97]) == pytest.approx(3.88)
    assert skew_ratio([]) == 0.0
    assert skew_ratio([0, 0]) == 0.0


def test_skewed_partitions():
    assert skewed_partitions([1, 1, 1, 97]) == [3]
    assert skewed_partitions([10, 10, 10]) == []
    assert skewed_partitions([5, 20, 5, 5], threshold=1.5) == [1]
    assert skewed_partitions([]) == []


# 4 joins
BIG = [{"id": i % 3, "amt": i} for i in range(12)] + [{"id": 99, "amt": -1}]
SMALL = [{"id": 0, "name": "zero"}, {"id": 1, "name": "one"}, {"id": 2, "name": "two"}, {"id": 2, "name": "deux"}]


def test_broadcast_join_inner():
    out = broadcast_join(BIG, SMALL, "id")
    assert all(r["id"] != 99 for r in out)
    assert len(out) == 4 + 4 + 8  # ids 0,1 -> 4 each; id 2 -> 4 rows * 2 matches
    assert {"id": 1, "amt": 1, "name": "one"} in out


def test_shuffle_join_equals_broadcast_join():
    for n in (1, 2, 5):
        assert canon(shuffle_join(BIG, SMALL, "id", n)) == canon(broadcast_join(BIG, SMALL, "id"))


def test_join_no_matches_and_empty():
    assert broadcast_join([], SMALL, "id") == []
    assert shuffle_join(BIG, [], "id", 3) == []


# 5 salted join
def test_salted_join_same_as_plain():
    skewed = [{"id": 1, "x": i} for i in range(40)] + [{"id": 2, "x": 100}]
    small = [{"id": 1, "name": "hot"}, {"id": 2, "name": "cold"}]
    expected = canon(broadcast_join(skewed, small, "id"))
    for salts in (1, 3, 8):
        got = salted_join(skewed, small, "id", salts)
        assert canon(got) == expected
        assert all("_salt" not in r for r in got)


def test_salted_join_does_not_mutate_inputs():
    big = [{"id": 1, "x": 1}]
    small = [{"id": 1, "n": "a"}]
    salted_join(big, small, "id", 4)
    assert big == [{"id": 1, "x": 1}] and small == [{"id": 1, "n": "a"}]


# 6 lazy dataset
def test_lazy_nothing_runs_until_action():
    calls = []
    ds = LazyDataset([1, 2, 3]).map(lambda x: calls.append(x) or x * 2).filter(lambda x: x > 2)
    assert calls == []
    assert ds.plan() == ["map", "filter"]
    assert ds.collect() == [4, 6]
    assert calls == [1, 2, 3]


def test_lazy_immutable_chaining_and_flat_map():
    base = LazyDataset(["a b", "c"])
    words = base.flat_map(str.split)
    assert base.plan() == []
    assert words.collect() == ["a", "b", "c"]
    assert words.count() == 3
    assert words.map(str.upper).collect() == ["A", "B", "C"]


def test_lazy_recomputes_without_cache_and_reuses_with_cache():
    calls = []
    ds = LazyDataset([1, 2]).map(lambda x: calls.append(x) or x)
    ds.collect(); ds.collect()
    assert len(calls) == 4
    calls.clear()
    c = LazyDataset([1, 2]).map(lambda x: calls.append(x) or x).cache()
    c.collect(); c.collect(); assert c.count() == 2
    assert len(calls) == 2


# 7 narrow/wide
def test_classify_ops():
    assert classify_ops(["map", "filter", "groupBy", "select", "join"]) == [
        "narrow", "narrow", "wide", "narrow", "wide"]
    assert classify_ops([]) == []


def test_classify_unknown_raises():
    with pytest.raises(ValueError):
        classify_ops(["map", "frobnicate"])


def test_count_stages():
    assert count_stages([]) == 1
    assert count_stages(["map", "filter"]) == 1
    assert count_stages(["map", "reduceByKey", "map", "orderBy"]) == 3


# 8 partitions sizing
def test_num_partitions_for():
    mb = 1024 * 1024
    assert num_partitions_for(0) == 1
    assert num_partitions_for(128 * mb) == 1
    assert num_partitions_for(128 * mb + 1) == 2
    assert num_partitions_for(10 * 1024 * mb) == 80
    assert num_partitions_for(1000, target_bytes=100) == 10


# 9 coalesce / repartition
def test_coalesce_merges_without_reordering():
    parts = [[1], [2], [3], [4], [5], [6]]
    out = coalesce(parts, 2)
    assert len(out) == 2
    assert [x for p in out for x in p] == [1, 2, 3, 4, 5, 6]
    assert all(out)


def test_coalesce_cannot_increase():
    parts = [[1], [2]]
    assert coalesce(parts, 5) == [[1], [2]]


def test_repartition_balances():
    parts = [list(range(100)), [], []]
    out = repartition(parts, 4)
    assert [len(p) for p in out] == [25, 25, 25, 25]
    assert sorted(x for p in out for x in p) == list(range(100))
    assert len(repartition(parts, 8)) == 8


# 10 window
def test_row_number_over():
    rows = [
        {"u": "a", "t": 3}, {"u": "a", "t": 1}, {"u": "b", "t": 2}, {"u": "a", "t": 2},
    ]
    out = row_number_over(rows, "u", "t")
    got = {(r["u"], r["t"]): r["rn"] for r in out}
    assert got == {("a", 1): 1, ("a", 2): 2, ("a", 3): 3, ("b", 2): 1}
    assert len(out) == 4
    assert "rn" not in rows[0]


def test_row_number_latest_per_key_descending():
    rows = [{"u": "a", "t": 1, "v": "old"}, {"u": "a", "t": 9, "v": "new"}]
    out = row_number_over(rows, "u", "t", descending=True)
    assert [r["v"] for r in out if r["rn"] == 1] == ["new"]
