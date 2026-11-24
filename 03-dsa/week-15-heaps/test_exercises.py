import random
import statistics
import pytest
from collections import Counter
from exercises import *


def make_list(vals):
    dummy = tail = ListNode()
    for v in vals:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def list_vals(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


@pytest.mark.parametrize("nums,k,expected", [
    ([3, 2, 1, 5, 6, 4], 2, 5), ([3, 2, 3, 1, 2, 4, 5, 5, 6], 4, 4), ([1], 1, 1),
    ([5, 5, 5], 2, 5), ([-1, -2, -3], 3, -3), ([7, 6, 5, 4], 4, 4), ([1, 2], 1, 2),
])
def test_kth_largest(nums, k, expected):
    assert kth_largest(nums, k) == expected


def test_kth_largest_does_not_mutate_and_random():
    rng = random.Random(1)
    nums = [rng.randint(-50, 50) for _ in range(300)]
    copy = nums[:]
    for k in (1, 7, 150, 300):
        assert kth_largest(nums, k) == sorted(nums, reverse=True)[k - 1]
    assert nums == copy


@pytest.mark.parametrize("stones,expected", [
    ([2, 7, 4, 1, 8, 1], 1), ([1], 1), ([2, 2], 0), ([], 0), ([3, 3, 3], 3),
    ([1, 3], 2), ([10, 4, 2, 10], 2), ([9, 3, 2, 10], 0),
])
def test_last_stone_weight(stones, expected):
    assert last_stone_weight(stones) == expected


def test_kth_largest_stream():
    kl = KthLargest(3, [4, 5, 8, 2])
    assert [kl.add(3), kl.add(5), kl.add(10), kl.add(9), kl.add(4)] == [4, 5, 5, 8, 8]


def test_kth_largest_stream_edge_cases():
    kl = KthLargest(1, [])
    assert kl.add(-3) == -3
    assert kl.add(-2) == -2
    assert kl.add(-4) == -2
    kl = KthLargest(2, [0])
    assert kl.add(-1) == -1
    assert kl.add(1) == 0
    kl = KthLargest(2, [5, 5, 5])
    assert kl.add(5) == 5
    rng = random.Random(3)
    init = [rng.randint(0, 20) for _ in range(10)]
    kl = KthLargest(4, init)
    seen = init[:]
    for _ in range(100):
        v = rng.randint(0, 20)
        seen.append(v)
        assert kl.add(v) == sorted(seen, reverse=True)[3]


@pytest.mark.parametrize("nums,k,expected", [
    ([1, 1, 1, 2, 2, 3], 2, {1, 2}), ([1], 1, {1}), ([4, 4, 5, 5, 5, 6], 1, {5}),
    ([-1, -1, 2, 2, 2, 3], 2, {-1, 2}), ([1, 2, 3], 3, {1, 2, 3}),
    ([0, 0, 0, 1, 1, 2], 2, {0, 1}),
])
def test_top_k_frequent(nums, k, expected):
    res = top_k_frequent(nums, k)
    assert len(res) == k and set(res) == expected


def dist(p):
    return p[0] ** 2 + p[1] ** 2


@pytest.mark.parametrize("points,k", [
    ([[1, 3], [-2, 2]], 1), ([[3, 3], [5, -1], [-2, 4]], 2), ([[0, 1], [1, 0]], 2),
    ([[1, 1]], 1), ([[5, 5], [1, 1], [2, 2], [3, 3], [4, 4]], 3), ([[0, 0], [0, 0], [1, 1]], 2),
])
def test_k_closest(points, k):
    res = k_closest(points, k)
    assert len(res) == k
    assert sorted(map(dist, res)) == sorted(map(dist, points))[:k]


def test_k_closest_random():
    rng = random.Random(5)
    pts = [[rng.randint(-100, 100), rng.randint(-100, 100)] for _ in range(200)]
    for k in (1, 10, 200):
        res = k_closest(pts, k)
        assert sorted(map(dist, res)) == sorted(map(dist, pts))[:k]


@pytest.mark.parametrize("lists,expected", [
    ([], []), ([[]], []), ([[], []], []), ([[1]], [1]),
    ([[1, 4, 5], [1, 3, 4], [2, 6]], [1, 1, 2, 3, 4, 4, 5, 6]),
    ([[], [1], []], [1]), ([[-2, -1], [-3], [0]], [-3, -2, -1, 0]),
    ([[1, 1, 1], [1, 1]], [1] * 5),
])
def test_merge_k_lists(lists, expected):
    head = merge_k_lists([make_list(v) for v in lists])
    assert list_vals(head) == expected


def test_merge_k_lists_many():
    rng = random.Random(9)
    groups = [sorted(rng.randint(0, 50) for _ in range(rng.randint(0, 20))) for _ in range(30)]
    head = merge_k_lists([make_list(g) for g in groups])
    assert list_vals(head) == sorted(x for g in groups for x in g)


@pytest.mark.parametrize("s", ["aab", "a", "abc", "aabb", "aaabbc", "vvvlo", "aabbcc", "ab", "aaabb"])
def test_reorganize_string_possible(s):
    res = reorganize_string(s)
    assert sorted(res) == sorted(s)
    assert all(a != b for a, b in zip(res, res[1:]))


@pytest.mark.parametrize("s", ["aaab", "aa", "aaaabc", "aaaaabbc"])
def test_reorganize_string_impossible(s):
    assert reorganize_string(s) == ""


@pytest.mark.parametrize("tasks,n,expected", [
    (list("AAABBB"), 2, 8), (list("AAABBB"), 0, 6), (list("AAAAAABCDEFG"), 2, 16),
    (list("A"), 5, 1), (list("AAA"), 2, 7), (list("ABCD"), 3, 4),
    (list("AABBCC"), 1, 6), (list("AAABBBCC"), 2, 8), ([], 3, 0),
])
def test_task_scheduler(tasks, n, expected):
    assert task_scheduler(tasks, n) == expected


def test_median_finder():
    m = MedianFinder()
    m.addNum(1)
    assert m.findMedian() == 1
    m.addNum(2)
    assert m.findMedian() == 1.5
    m.addNum(3)
    assert m.findMedian() == 2


def test_median_finder_negatives_duplicates_random():
    m = MedianFinder()
    for v in (-1, -2, -3, -4, -5):
        m.addNum(v)
    assert m.findMedian() == -3
    m = MedianFinder()
    for v in (5, 5, 5, 5):
        m.addNum(v)
    assert m.findMedian() == 5
    rng = random.Random(11)
    m, seen = MedianFinder(), []
    for _ in range(300):
        v = rng.randint(-1000, 1000)
        seen.append(v)
        m.addNum(v)
        assert m.findMedian() == statistics.median(seen)


@pytest.mark.parametrize("a,b,k", [
    ([1, 7, 11], [2, 4, 6], 3), ([1, 1, 2], [1, 2, 3], 2), ([1, 2], [3], 3),
    ([1, 2, 4], [-1, 1, 2], 100), ([], [1], 2), ([1], [], 2), ([0, 0], [0, 0], 3),
    ([1, 1, 2], [1, 2, 3], 10),
])
def test_k_smallest_pairs(a, b, k):
    res = k_smallest_pairs(a, b, k)
    all_pairs = sorted(([x, y] for x in a for y in b), key=sum)
    assert len(res) == min(k, len(all_pairs))
    assert [sum(p) for p in res] == [sum(p) for p in all_pairs[:len(res)]]
    for u, v in res:
        assert u in a and v in b


def test_k_smallest_pairs_large_is_not_quadratic():
    a = list(range(0, 200000, 2))
    b = list(range(1, 200001, 2))
    res = k_smallest_pairs(a, b, 5)
    assert [sum(p) for p in res] == [1, 3, 3, 5, 5]
