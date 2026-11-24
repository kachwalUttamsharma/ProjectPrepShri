import random

from exercises import *


def test_is_palindrome():
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome("") is True
    assert is_palindrome(" ") is True
    assert is_palindrome(".,") is True
    assert is_palindrome("a") is True
    assert is_palindrome("0P") is False
    assert is_palindrome("ab_a") is True
    assert is_palindrome("a" * 100000) is True
    assert is_palindrome("a" * 50000 + "b" + "a" * 49999) is False


def _check_pair(nums, target, res):
    assert len(res) == 2
    i, j = res
    assert 0 <= i < j < len(nums)
    assert nums[i] + nums[j] == target


def test_two_sum_sorted():
    _check_pair([2, 7, 11, 15], 9, two_sum_sorted([2, 7, 11, 15], 9))
    _check_pair([-3, -1, 0, 4], 1, two_sum_sorted([-3, -1, 0, 4], 1))
    _check_pair([3, 3], 6, two_sum_sorted([3, 3], 6))
    _check_pair([-5, -2, -1], -7, two_sum_sorted([-5, -2, -1], -7))
    assert two_sum_sorted([1, 2], 10) == []
    assert two_sum_sorted([], 0) == []
    assert two_sum_sorted([5], 10) == []
    assert two_sum_sorted([5], 5) == []  # cannot reuse the same element
    big = list(range(200000))
    _check_pair(big, 399997, two_sum_sorted(big, 399997))
    assert two_sum_sorted(big, 10**9) == []


def test_remove_duplicates_sorted():
    a = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    k = remove_duplicates_sorted(a)
    assert k == 5 and a[:k] == [0, 1, 2, 3, 4]
    a = [1]
    assert remove_duplicates_sorted(a) == 1 and a[:1] == [1]
    assert remove_duplicates_sorted([]) == 0
    a = [2, 2, 2, 2]
    k = remove_duplicates_sorted(a)
    assert k == 1 and a[:1] == [2]
    a = [-3, -3, -1, 0, 0]
    k = remove_duplicates_sorted(a)
    assert k == 3 and a[:k] == [-3, -1, 0]
    a = [1, 2, 3]
    k = remove_duplicates_sorted(a)
    assert k == 3 and a == [1, 2, 3]
    a = sorted(random.Random(1).choices(range(1000), k=100000))
    expected = sorted(set(a))
    k = remove_duplicates_sorted(a)
    assert a[:k] == expected


def test_move_zeroes():
    a = [0, 1, 0, 3, 12]
    assert move_zeroes(a) is None
    assert a == [1, 3, 12, 0, 0]
    a = [0]
    move_zeroes(a)
    assert a == [0]
    a = [0, 0, 0]
    move_zeroes(a)
    assert a == [0, 0, 0]
    a = [1, 2, 3]
    move_zeroes(a)
    assert a == [1, 2, 3]
    a = [4, 0, 0, -1, 0, 5]
    move_zeroes(a)
    assert a == [4, -1, 5, 0, 0, 0]
    a = []
    move_zeroes(a)
    assert a == []
    a = [0, 1] * 100000
    move_zeroes(a)
    assert a == [1] * 100000 + [0] * 100000


def test_is_subsequence():
    assert is_subsequence("abc", "ahbgdc") is True
    assert is_subsequence("axc", "ahbgdc") is False
    assert is_subsequence("", "abc") is True
    assert is_subsequence("", "") is True
    assert is_subsequence("a", "") is False
    assert is_subsequence("aaa", "aa") is False
    assert is_subsequence("aa", "aaa") is True
    assert is_subsequence("ba", "ab") is False
    assert is_subsequence("z" * 1000, "z" * 1000 + "y" * 100000) is True


def test_merge_sorted_in_place():
    a = [1, 2, 3, 0, 0, 0]
    assert merge_sorted_in_place(a, 3, [2, 5, 6], 3) is None
    assert a == [1, 2, 2, 3, 5, 6]
    a = [1]
    merge_sorted_in_place(a, 1, [], 0)
    assert a == [1]
    a = [0]
    merge_sorted_in_place(a, 0, [1], 1)
    assert a == [1]
    a = [0, 0, 0]
    merge_sorted_in_place(a, 0, [-1, 0, 4], 3)
    assert a == [-1, 0, 4]
    a = [4, 5, 6, 0, 0, 0]
    merge_sorted_in_place(a, 3, [1, 2, 3], 3)
    assert a == [1, 2, 3, 4, 5, 6]
    a = [1, 1, 0, 0]
    merge_sorted_in_place(a, 2, [1, 1], 2)
    assert a == [1, 1, 1, 1]
    x = sorted(random.Random(2).sample(range(10**6), 50000))
    y = sorted(random.Random(3).sample(range(10**6), 50000))
    a = x + [0] * 50000
    merge_sorted_in_place(a, 50000, y, 50000)
    assert a == sorted(x + y)


def test_max_area():
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    assert max_area([]) == 0
    assert max_area([5]) == 0
    assert max_area([0, 0, 0]) == 0
    assert max_area([2, 3, 4, 5, 18, 17, 6]) == 17
    assert max_area([10, 1, 1, 1, 10]) == 40
    assert max_area([1] * 100000) == 99999
    rng = random.Random(4)
    for _ in range(50):
        h = [rng.randint(0, 20) for _ in range(rng.randint(0, 15))]
        brute = max(
            (j - i) * min(h[i], h[j]) for i in range(len(h)) for j in range(i + 1, len(h))
        ) if len(h) > 1 else 0
        assert max_area(h) == brute


def test_sort_colors():
    a = [2, 0, 2, 1, 1, 0]
    assert sort_colors(a) is None
    assert a == [0, 0, 1, 1, 2, 2]
    for arr in ([0], [1], [2], [2, 1, 0], [1, 1, 1], [2, 2, 0, 0], [0, 1, 2], [1, 0]):
        b = list(arr)
        sort_colors(b)
        assert b == sorted(arr)
    a = []
    sort_colors(a)
    assert a == []
    rng = random.Random(5)
    a = [rng.randint(0, 2) for _ in range(100000)]
    e = sorted(a)
    sort_colors(a)
    assert a == e


def _norm(trips):
    return sorted(tuple(sorted(t)) for t in trips)


def test_three_sum():
    assert _norm(three_sum([-1, 0, 1, 2, -1, -4])) == [(-1, -1, 2), (-1, 0, 1)]
    assert three_sum([]) == []
    assert three_sum([0]) == []
    assert three_sum([1, 2, 3]) == []
    assert _norm(three_sum([0, 0, 0, 0])) == [(0, 0, 0)]
    assert _norm(three_sum([-2, 0, 0, 2, 2])) == [(-2, 0, 2)]
    assert len(three_sum([-2, 0, 0, 2, 2])) == 1  # no duplicate triplets
    assert _norm(three_sum([-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6])) == [
        (-4, -2, 6), (-4, 0, 4), (-4, 1, 3), (-4, 2, 2), (-2, -2, 4), (-2, 0, 2)
    ]
    rng = random.Random(6)
    for _ in range(30):
        a = [rng.randint(-6, 6) for _ in range(rng.randint(0, 14))]
        brute = set()
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                for k in range(j + 1, len(a)):
                    if a[i] + a[j] + a[k] == 0:
                        brute.add(tuple(sorted((a[i], a[j], a[k]))))
        res = three_sum(a)
        assert len(res) == len(brute)
        assert set(_norm(res)) == brute
    a = [rng.randint(-1000, 1000) for _ in range(1500)]
    res = three_sum(a)
    assert all(sum(t) == 0 for t in res)


def test_trap():
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap([4, 2, 0, 3, 2, 5]) == 9
    assert trap([]) == 0
    assert trap([3]) == 0
    assert trap([1, 2, 3]) == 0
    assert trap([3, 2, 1]) == 0
    assert trap([2, 0, 2]) == 2
    assert trap([5, 5, 5]) == 0
    assert trap([5, 0, 0, 0, 5]) == 15
    assert trap([5] + [0] * 100000 + [5]) == 500000
