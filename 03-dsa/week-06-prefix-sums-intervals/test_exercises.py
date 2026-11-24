import random

from exercises import *


def test_running_sum():
    assert running_sum([1, 2, 3, 4]) == [1, 3, 6, 10]
    assert running_sum([]) == []
    assert running_sum([5]) == [5]
    assert running_sum([3, 1, 2, 10, 1]) == [3, 4, 6, 16, 17]
    assert running_sum([-1, 1, -1]) == [-1, 0, -1]
    assert running_sum([0, 0]) == [0, 0]
    a = [1] * 200000
    r = running_sum(a)
    assert r[-1] == 200000 and r[0] == 1
    orig = [1, 2, 3]
    running_sum(orig)
    assert orig == [1, 2, 3]


def test_num_array():
    na = NumArray([-2, 0, 3, -5, 2, -1])
    assert na.sum_range(0, 2) == 1
    assert na.sum_range(2, 5) == -1
    assert na.sum_range(0, 5) == -3
    assert na.sum_range(3, 3) == -5
    assert NumArray([7]).sum_range(0, 0) == 7
    n = NumArray([1, 1, 1, 1])
    assert n.sum_range(1, 2) == 2
    rng = random.Random(1)
    a = [rng.randint(-50, 50) for _ in range(200000)]
    na = NumArray(a)
    for _ in range(2000):
        i = rng.randrange(len(a))
        j = rng.randrange(i, len(a))
        assert na.sum_range(i, j) == sum(a[i:j + 1])


def test_pivot_index():
    assert pivot_index([1, 7, 3, 6, 5, 6]) == 3
    assert pivot_index([1, 2, 3]) == -1
    assert pivot_index([2, 1, -1]) == 0
    assert pivot_index([]) == -1
    assert pivot_index([5]) == 0
    assert pivot_index([-1, -1, 0, 1, 1, 0]) == 5
    assert pivot_index([0, 0, 0]) == 0  # leftmost
    assert pivot_index([1, -1, 1]) == 0
    assert pivot_index([-1, 1, 1]) == 2
    assert pivot_index([1] * 100001) == 50000


def test_subarray_sum():
    assert subarray_sum([1, 1, 1], 2) == 2
    assert subarray_sum([1, 2, 3], 3) == 2
    assert subarray_sum([0, 0, 0], 0) == 6
    assert subarray_sum([], 0) == 0
    assert subarray_sum([5], 5) == 1
    assert subarray_sum([5], 4) == 0
    assert subarray_sum([1, -1, 0], 0) == 3
    assert subarray_sum([-1, -1, 1], 0) == 1
    assert subarray_sum([3, 4, 7, 2, -3, 1, 4, 2], 7) == 4
    rng = random.Random(2)
    for _ in range(40):
        a = [rng.randint(-3, 3) for _ in range(rng.randint(0, 25))]
        k = rng.randint(-4, 4)
        brute = sum(
            1 for i in range(len(a)) for j in range(i, len(a)) if sum(a[i:j + 1]) == k
        )
        assert subarray_sum(a, k) == brute
    assert subarray_sum([0] * 2000, 0) == 2000 * 2001 // 2
    assert subarray_sum([1] * 200000, 7) == 200000 - 6


def test_product_except_self():
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    assert product_except_self([0, 0]) == [0, 0]
    assert product_except_self([2, 3]) == [3, 2]
    assert product_except_self([5]) == [1]
    assert product_except_self([]) == []
    assert product_except_self([0, 2, 3]) == [6, 0, 0]
    assert product_except_self([-2, -3]) == [-3, -2]
    assert product_except_self([1, 1, 1, 1]) == [1, 1, 1, 1]
    r = product_except_self([1] * 200000)
    assert len(r) == 200000 and set(r) == {1}


def test_range_addition():
    assert range_addition(5, [[1, 3, 2], [2, 4, 3], [0, 2, -2]]) == [-2, 0, 3, 5, 3]
    assert range_addition(3, []) == [0, 0, 0]
    assert range_addition(0, []) == []
    assert range_addition(1, [[0, 0, 5]]) == [5]
    assert range_addition(4, [[0, 3, 1], [0, 3, 1]]) == [2, 2, 2, 2]
    assert range_addition(4, [[3, 3, 7]]) == [0, 0, 0, 7]
    assert range_addition(4, [[0, 0, 7]]) == [7, 0, 0, 0]
    rng = random.Random(3)
    n = 50
    ups = []
    exp = [0] * n
    for _ in range(100):
        s = rng.randrange(n)
        e = rng.randrange(s, n)
        inc = rng.randint(-5, 5)
        ups.append([s, e, inc])
        for i in range(s, e + 1):
            exp[i] += inc
    assert range_addition(n, ups) == exp
    n = 200000
    r = range_addition(n, [[0, n - 1, 1]] * 100000)
    assert r[0] == 100000 and r[-1] == 100000


def test_merge_intervals():
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([]) == []
    assert merge_intervals([[1, 2]]) == [[1, 2]]
    assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]  # unsorted input
    assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]  # containment
    assert merge_intervals([[1, 4], [0, 4]]) == [[0, 4]]
    assert merge_intervals([[2, 3], [4, 5], [6, 7], [8, 9], [1, 10]]) == [[1, 10]]
    assert merge_intervals([[-5, -2], [-3, 0]]) == [[-5, 0]]
    assert merge_intervals([[1, 1], [1, 1]]) == [[1, 1]]
    inp = [[3, 4], [1, 2]]
    merge_intervals(inp)
    assert inp == [[3, 4], [1, 2]]
    big = [[i * 2, i * 2 + 1] for i in range(100000)]
    assert merge_intervals(big) == big
    chain = [[i, i + 1] for i in range(100000)]
    assert merge_intervals(chain) == [[0, 100000]]


def test_insert_interval():
    assert insert_interval([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert insert_interval([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [
        [1, 2], [3, 10], [12, 16]
    ]
    assert insert_interval([], [5, 7]) == [[5, 7]]
    assert insert_interval([[1, 5]], [2, 3]) == [[1, 5]]
    assert insert_interval([[1, 5]], [6, 8]) == [[1, 5], [6, 8]]
    assert insert_interval([[3, 5]], [0, 1]) == [[0, 1], [3, 5]]
    assert insert_interval([[1, 5]], [5, 7]) == [[1, 7]]
    assert insert_interval([[1, 5]], [0, 6]) == [[0, 6]]
    assert insert_interval([[1, 2], [3, 4]], [0, 10]) == [[0, 10]]
    assert insert_interval([[1, 2], [5, 6]], [3, 4]) == [[1, 2], [3, 4], [5, 6]]
    big = [[i * 3, i * 3 + 1] for i in range(100000)]
    r = insert_interval(big, [1000, 2000])
    assert r[0] == [0, 1] and [999, 2000] in r
    assert len(r) == len(big) - 333


def test_erase_overlap_intervals():
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    assert erase_overlap_intervals([]) == 0
    assert erase_overlap_intervals([[1, 5]]) == 0
    assert erase_overlap_intervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2
    assert erase_overlap_intervals([[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]]) == 2
    assert erase_overlap_intervals([[-10, -5], [-6, 0], [0, 3]]) == 1
    assert erase_overlap_intervals([[1, 10]] * 5 + [[11, 12]]) == 4
    assert erase_overlap_intervals([[i, i + 2] for i in range(100000)]) == 50000


def test_min_meeting_rooms():
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert min_meeting_rooms([]) == 0
    assert min_meeting_rooms([[1, 5]]) == 1
    assert min_meeting_rooms([[1, 5], [5, 10]]) == 1  # back-to-back
    assert min_meeting_rooms([[1, 5], [1, 5], [1, 5]]) == 3
    assert min_meeting_rooms([[1, 10], [2, 3], [4, 5], [6, 7]]) == 2
    assert min_meeting_rooms([[9, 10], [4, 9], [4, 17]]) == 2
    assert min_meeting_rooms([[13, 15], [1, 13]]) == 1
    rng = random.Random(4)
    for _ in range(30):
        iv = []
        for _ in range(rng.randint(0, 15)):
            s = rng.randint(0, 20)
            iv.append([s, s + rng.randint(1, 6)])
        brute = max((sum(1 for s, e in iv if s <= t < e) for t in range(0, 30)), default=0)
        assert min_meeting_rooms(iv) == brute
    assert min_meeting_rooms([[i, i + 1] for i in range(100000)]) == 1
    assert min_meeting_rooms([[0, 100000]] * 50000) == 50000


def test_interval_intersection():
    a = [[0, 2], [5, 10], [13, 23], [24, 25]]
    b = [[1, 5], [8, 12], [15, 24], [25, 26]]
    assert interval_intersection(a, b) == [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    assert interval_intersection([], [[1, 2]]) == []
    assert interval_intersection([[1, 2]], []) == []
    assert interval_intersection([], []) == []
    assert interval_intersection([[1, 3]], [[4, 5]]) == []
    assert interval_intersection([[1, 3]], [[3, 5]]) == [[3, 3]]
    assert interval_intersection([[1, 10]], [[2, 3], [5, 6]]) == [[2, 3], [5, 6]]
    assert interval_intersection([[1, 7]], [[3, 10]]) == [[3, 7]]
    assert interval_intersection([[-5, -1]], [[-3, 2]]) == [[-3, -1]]
    x = [[i * 2, i * 2 + 1] for i in range(100000)]
    assert interval_intersection(x, x) == x
    y = [[i * 2 + 1, i * 2 + 1] for i in range(1000)]
    assert interval_intersection(x[:1000], y) == [[i * 2 + 1, i * 2 + 1] for i in range(1000)]
