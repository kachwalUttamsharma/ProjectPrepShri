"""Week 2 exercises: Spark ideas simulated in pure Python (stdlib only).

pyspark is not needed. Each exercise models one concept: partitioning,
shuffle, skew, joins, lazy evaluation, stages, coalesce vs repartition,
window functions. Rows are plain dicts; a "dataset" is a list of rows and a
"partitioned dataset" is a list of lists.

Replace each `...` with your code. Run:
    ../../.venv/bin/pytest -q
"""
import math
import zlib
from collections import defaultdict


def stable_hash(value):
    """Provided helper. Python's built-in hash() of str changes per process
    (hash randomisation), so use crc32 for reproducible partitioning."""
    return zlib.crc32(str(value).encode("utf-8"))


# Exercise 1 -------------------------------------------------------------
def hash_partition(rows, key, n):
    """Split `rows` (list of dicts) into `n` partitions (list of n lists) by
    hash of row[key]: partition index = stable_hash(row[key]) % n.
    Rows keep their original relative order inside a partition.
    Same key -> same partition (this is what a shuffle guarantees).
    Example: hash_partition([{"k": 1}, {"k": 1}], "k", 3) puts both rows in
    the same one of the 3 lists.
    """
    ...


# Exercise 2 -------------------------------------------------------------
def wordcount_shuffle(lines, n):
    """Simulate map -> shuffle -> reduce for word count with `n` reducers.
    Map: lowercase, split on whitespace, emit (word, 1).
    Shuffle: route each pair to reducer stable_hash(word) % n.
    Reduce: each reducer sums counts of its own words only.
    Return the merged {word: count} dict (result must not depend on n).
    Example: ["a b", "A"] -> {"a": 2, "b": 1}
    """
    ...


# Exercise 3 -------------------------------------------------------------
def skew_ratio(sizes):
    """Given a list of partition sizes return max(sizes) / mean(sizes).
    Empty list or all-zero sizes -> 0.0. A balanced dataset gives ~1.0.
    """
    ...


def skewed_partitions(sizes, threshold=2.0):
    """Return the indexes of partitions whose size is strictly greater than
    `threshold` * mean(sizes), in ascending order. Empty -> [].
    Example: skewed_partitions([1, 1, 1, 97]) -> [3]
    """
    ...


# Exercise 4 -------------------------------------------------------------
def broadcast_join(big, small, key):
    """Inner join two lists of dicts on `key`, broadcast style: build a dict
    index of `small` (every executor would hold it), then stream `big`
    through it with no shuffle. Merge matching rows as {**big_row, **small_row}.
    Output order: follows `big`. Duplicate keys in `small` produce multiple
    output rows.
    """
    ...


def shuffle_join(left, right, key, n):
    """Inner join by shuffling both sides: hash_partition each side into `n`
    partitions on `key`, join partition i of left with partition i of right
    locally, concatenate. Result must equal broadcast_join as a multiset of
    rows (order may differ).
    Hint: reuse hash_partition and broadcast_join for the local join.
    """
    ...


# Exercise 5 -------------------------------------------------------------
def salted_join(big, small, key, n_salts):
    """Skew fix by salting. Give each row of `big` a "_salt" = index % n_salts;
    replicate every row of `small` n_salts times, once per salt value;
    join on (key, "_salt"); drop "_salt" from the output rows.
    Result must equal an ordinary inner join on `key` (as a multiset).
    Do not mutate the input rows.
    Why it works: one hot key is spread over n_salts partitions.
    """
    ...


# Exercise 6 -------------------------------------------------------------
class LazyDataset:
    """Tiny lazy pipeline, like an RDD/DataFrame.

    Transformations (map, filter, flat_map) only RECORD the step and return a
    NEW LazyDataset (the original must be unchanged). Nothing runs until an
    action (collect, count) is called. collect() runs the recorded steps in
    order over the source data and returns a list.
      - map(fn): one output per input
      - filter(fn): keep items where fn(item) is truthy
      - flat_map(fn): fn returns an iterable; flatten results
    plan() returns the list of recorded step names, e.g. ["map", "filter"].
    cache(): mark this dataset so the first action stores its result and later
    actions reuse it without re-running the functions. Returns self.
    Without cache(), every action recomputes from scratch.
    """

    def __init__(self, data):
        ...

    def map(self, fn):
        ...

    def filter(self, fn):
        ...

    def flat_map(self, fn):
        ...

    def cache(self):
        ...

    def plan(self):
        ...

    def collect(self):
        ...

    def count(self):
        ...


# Exercise 7 -------------------------------------------------------------
def classify_ops(ops):
    """Classify Spark operation names as "narrow" or "wide" dependencies.
    narrow: map, filter, flatMap, select, withColumn, union, coalesce,
            mapPartitions
    wide (needs a shuffle): groupBy, groupByKey, reduceByKey, join, distinct,
            repartition, orderBy, sort
    Return a list of the same length. Unknown name -> raise ValueError.
    """
    ...


def count_stages(ops):
    """A job is cut into stages at shuffle boundaries: stages = 1 + number of
    wide ops. Example: ["map", "reduceByKey", "map", "orderBy"] -> 3.
    Unknown ops raise ValueError (via classify_ops).
    """
    ...


# Exercise 8 -------------------------------------------------------------
def num_partitions_for(total_bytes, target_bytes=128 * 1024 * 1024):
    """How many partitions for `total_bytes` of data at ~`target_bytes` each?
    Round UP, minimum 1. (Spark's default max partition bytes is 128 MB;
    check current docs.)
    """
    ...


# Exercise 9 -------------------------------------------------------------
def coalesce(partitions, n):
    """Reduce partitions WITHOUT a shuffle: merge neighbouring partitions so
    the original row order is preserved. If n >= len(partitions) return a
    copy unchanged (coalesce cannot increase). Return exactly n non-empty
    groups when the inputs are non-empty.
    Hint: output index for input i can be i * n // len(partitions).
    """
    ...


def repartition(partitions, n):
    """Full shuffle into exactly `n` balanced partitions: deal all rows
    round-robin (row j overall goes to partition j % n), in input order.
    Works for increasing or decreasing n.
    """
    ...


# Exercise 10 ------------------------------------------------------------
def row_number_over(rows, partition_key, order_key, descending=False):
    """Emulate row_number() OVER (PARTITION BY partition_key ORDER BY
    order_key [DESC]). Return NEW dicts with an extra "rn" column starting at
    1 within each partition. Do not mutate inputs. Output order is not
    important. Use case: keep rn == 1 to get the latest row per key.
    """
    ...
