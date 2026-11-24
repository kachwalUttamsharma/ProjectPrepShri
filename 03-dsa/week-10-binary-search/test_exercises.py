import math
import random
import statistics

from exercises import *


def test_binary_search():
    assert binary_search([-1, 0, 3, 5, 9, 12], 9) == 4
    assert binary_search([-1, 0, 3, 5, 9, 12], 2) == -1
    assert binary_search([], 1) == -1
    assert binary_search([5], 5) == 0
    assert binary_search([5], 4) == -1
    assert binary_search([1, 2], 1) == 0
    assert binary_search([1, 2], 2) == 1
    assert binary_search([1, 2, 3], 0) == -1
    assert binary_search([1, 2, 3], 4) == -1
    big = list(range(0, 2_000_000, 2))
    assert binary_search(big, 1_999_998) == 999_999
    assert binary_search(big, 7) == -1


def test_search_insert():
    assert search_insert([1, 3, 5, 6], 5) == 2
    assert search_insert([1, 3, 5, 6], 2) == 1
    assert search_insert([1, 3, 5, 6], 7) == 4
    assert search_insert([1, 3, 5, 6], 0) == 0
    assert search_insert([], 3) == 0
    assert search_insert([4], 4) == 0
    assert search_insert([4], 5) == 1
    assert search_insert([-5, -2, 0], -3) == 1


def test_search_range():
    assert search_range([5, 7, 7, 8, 8, 10], 8) == [3, 4]
    assert search_range([5, 7, 7, 8, 8, 10], 6) == [-1, -1]
    assert search_range([], 0) == [-1, -1]
    assert search_range([1], 1) == [0, 0]
    assert search_range([2, 2, 2, 2], 2) == [0, 3]
    assert search_range([1, 2, 2, 2, 3], 1) == [0, 0]
    assert search_range([1, 2, 2, 2, 3], 3) == [4, 4]
    assert search_range([1, 3], 2) == [-1, -1]
    big = [1] * 100_000 + [2] * 100_000 + [3] * 100_000
    assert search_range(big, 2) == [100_000, 199_999]


def test_my_sqrt():
    assert my_sqrt(0) == 0
    assert my_sqrt(1) == 1
    assert my_sqrt(2) == 1
    assert my_sqrt(3) == 1
    assert my_sqrt(4) == 2
    assert my_sqrt(8) == 2
    assert my_sqrt(16) == 4
    assert my_sqrt(99) == 9
    assert my_sqrt(2 ** 31 - 1) == 46340
    for x in [10 ** 12, 10 ** 12 - 1, 10 ** 18 + 12345]:
        assert my_sqrt(x) == math.isqrt(x)


def test_search_rotated():
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1
    assert search_rotated([1], 1) == 0
    assert search_rotated([1], 0) == -1
    assert search_rotated([], 1) == -1
    assert search_rotated([3, 1], 1) == 1
    assert search_rotated([3, 1], 3) == 0
    assert search_rotated([1, 3], 3) == 1
    base = list(range(-50, 50))
    for r in range(len(base)):
        arr = base[r:] + base[:r]
        for t in (-50, -1, 0, 49, 7, 100, -51):
            exp = arr.index(t) if t in arr else -1
            assert search_rotated(arr, t) == exp


def test_find_min_rotated():
    assert find_min_rotated([3, 4, 5, 1, 2]) == 1
    assert find_min_rotated([4, 5, 6, 7, 0, 1, 2]) == 0
    assert find_min_rotated([11, 13, 15, 17]) == 11
    assert find_min_rotated([2, 1]) == 1
    assert find_min_rotated([1, 2]) == 1
    assert find_min_rotated([7]) == 7
    assert find_min_rotated([-3, -2, -1, -10, -9]) == -10
    base = list(range(1000))
    for r in range(0, 1000, 37):
        assert find_min_rotated(base[r:] + base[:r]) == 0


def _is_peak(nums, i):
    if not isinstance(i, int) or not 0 <= i < len(nums):
        return False
    left = nums[i - 1] if i > 0 else -math.inf
    right = nums[i + 1] if i < len(nums) - 1 else -math.inf
    return nums[i] > left and nums[i] > right


def test_find_peak():
    cases = [[1], [1, 2], [2, 1], [1, 2, 3, 1], [1, 2, 1, 3, 5, 6, 4],
             [1, 2, 3, 4, 5], [5, 4, 3, 2, 1], [-5, -1, -7], [3, 1, 3, 1, 3]]
    for c in cases:
        assert _is_peak(c, find_peak(c)), c
    random.seed(1)
    for _ in range(200):
        n = random.randint(1, 60)
        arr = [random.randint(-50, 50)]
        while len(arr) < n:
            v = random.randint(-50, 50)
            if v != arr[-1]:
                arr.append(v)
        assert _is_peak(arr, find_peak(arr)), arr
    big = list(range(200_000)) + list(range(200_000, 0, -1))
    assert _is_peak(big, find_peak(big))


def test_min_eating_speed():
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    assert min_eating_speed([30, 11, 23, 4, 20], 6) == 23
    assert min_eating_speed([1], 1) == 1
    assert min_eating_speed([10], 5) == 2
    assert min_eating_speed([1, 1, 1, 1], 4) == 1
    assert min_eating_speed([312884470], 312884469) == 2
    big = [10 ** 9] * 10_000
    assert min_eating_speed(big, 20_000) == 5 * 10 ** 8


def test_ship_within_days():
    assert ship_within_days([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15
    assert ship_within_days([3, 2, 2, 4, 1, 4], 3) == 6
    assert ship_within_days([1, 2, 3, 1, 1], 4) == 3
    assert ship_within_days([5], 1) == 5
    assert ship_within_days([1, 2, 3], 1) == 6
    assert ship_within_days([1, 2, 3], 3) == 3
    assert ship_within_days([10, 50, 10], 3) == 50
    assert ship_within_days([1] * 50_000, 10) == 5000


def test_split_array():
    assert split_array([7, 2, 5, 10, 8], 2) == 18
    assert split_array([1, 2, 3, 4, 5], 2) == 9
    assert split_array([1, 4, 4], 3) == 4
    assert split_array([5], 1) == 5
    assert split_array([1, 2, 3], 1) == 6
    assert split_array([0, 0, 0], 2) == 0
    assert split_array([10, 5, 13, 4, 8, 4, 5, 11, 14, 9, 16, 10, 20, 8], 8) == 25
    assert split_array([1] * 20_000, 4) == 5000


def test_find_median_sorted_arrays():
    assert find_median_sorted_arrays([1, 3], [2]) == 2.0
    assert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5
    assert find_median_sorted_arrays([], [1]) == 1.0
    assert find_median_sorted_arrays([2], []) == 2.0
    assert find_median_sorted_arrays([], [1, 2, 3, 4]) == 2.5
    assert find_median_sorted_arrays([0, 0], [0, 0]) == 0.0
    assert find_median_sorted_arrays([1, 2], [10, 11]) == 6.0
    assert find_median_sorted_arrays([-5, -3], [-4]) == -4.0
    random.seed(7)
    for _ in range(300):
        a = sorted(random.randint(-20, 20) for _ in range(random.randint(0, 12)))
        b = sorted(random.randint(-20, 20) for _ in range(random.randint(0, 12)))
        if not a and not b:
            continue
        assert find_median_sorted_arrays(a, b) == statistics.median(a + b), (a, b)
    a = list(range(0, 1_000_000, 2))
    b = list(range(1, 1_000_000, 2))
    assert find_median_sorted_arrays(a, b) == 499_999.5
