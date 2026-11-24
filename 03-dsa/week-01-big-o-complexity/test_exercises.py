import time
from exercises import *


def test_contains_duplicate():
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3]) is False
    assert contains_duplicate([]) is False
    assert contains_duplicate([7]) is False
    assert contains_duplicate([-1, -1]) is True
    assert contains_duplicate(list(range(200000))) is False
    assert contains_duplicate(list(range(200000)) + [5]) is True


def test_dedupe_preserve_order():
    assert dedupe_preserve_order([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert dedupe_preserve_order([]) == []
    assert dedupe_preserve_order([5]) == [5]
    assert dedupe_preserve_order([1, 1, 1]) == [1]
    assert dedupe_preserve_order(["b", "a", "b"]) == ["b", "a"]
    big = list(range(100000)) * 2
    assert dedupe_preserve_order(big) == list(range(100000))


def test_common_elements():
    assert common_elements([4, 1, 2, 2], [2, 2, 4, 9]) == [2, 4]
    assert common_elements([], [1]) == []
    assert common_elements([1], []) == []
    assert common_elements([1, 2], [3, 4]) == []
    assert common_elements([-1, -2, 0], [0, -2]) == [-2, 0]
    assert common_elements(list(range(100000)), list(range(50000, 150000))) == list(range(50000, 100000))


def test_first_unique_char():
    assert first_unique_char("leetcode") == 0
    assert first_unique_char("loveleetcode") == 2
    assert first_unique_char("aabb") == -1
    assert first_unique_char("") == -1
    assert first_unique_char("z") == 0
    assert first_unique_char("aabbc") == 4
    assert first_unique_char("ab" * 50000 + "c") == 100000


def test_is_anagram():
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("", "") is True
    assert is_anagram("a", "ab") is False
    assert is_anagram("aab", "abb") is False
    assert is_anagram("ab" * 50000, "ba" * 50000) is True


def test_build_csv_line():
    assert build_csv_line([1, "a", 2.5]) == "1,a,2.5"
    assert build_csv_line([]) == ""
    assert build_csv_line(["x"]) == "x"
    assert build_csv_line([None, True]) == "None,True"
    out = build_csv_line(range(100000))
    assert out.startswith("0,1,2") and out.endswith("99999") and out.count(",") == 99999


def test_rotate_left():
    assert rotate_left([1, 2, 3, 4, 5], 2) == [3, 4, 5, 1, 2]
    assert rotate_left([1, 2], 5) == [2, 1]
    assert rotate_left([], 3) == []
    assert rotate_left([1, 2, 3], 0) == [1, 2, 3]
    assert rotate_left([1, 2, 3], 3) == [1, 2, 3]
    src = [1, 2, 3]
    out = rotate_left(src, 1)
    assert out == [2, 3, 1] and src == [1, 2, 3]
    big = list(range(100000))
    assert rotate_left(big, 1)[-1] == 0


def test_merge_sorted():
    assert merge_sorted([1, 4, 7], [2, 3, 9]) == [1, 2, 3, 4, 7, 9]
    assert merge_sorted([], []) == []
    assert merge_sorted([], [1, 2]) == [1, 2]
    assert merge_sorted([1, 2], []) == [1, 2]
    assert merge_sorted([1, 1], [1]) == [1, 1, 1]
    assert merge_sorted([-3, -1], [-2, 0]) == [-3, -2, -1, 0]
    a = list(range(0, 200000, 2))
    b = list(range(1, 200000, 2))
    assert merge_sorted(a, b) == list(range(200000))


def test_fast_power():
    assert fast_power(2, 10) == 1024
    assert fast_power(5, 0) == 1
    assert fast_power(3, 1) == 3
    assert fast_power(0, 0) == 1
    assert fast_power(0, 5) == 0
    assert fast_power(-2, 3) == -8
    assert fast_power(-2, 4) == 16
    assert fast_power(2, 100) == 2 ** 100
    assert fast_power(1, 10 ** 9) == 1  # linear loop would take far too long


def test_is_prime():
    assert [n for n in range(30) if is_prime(n)] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert is_prime(97) is True
    assert is_prime(1) is False
    assert is_prime(0) is False
    assert is_prime(2 ** 31 - 1) is True
    assert is_prime(1_000_000_007) is True
    assert is_prime(1_000_000_007 * 3) is False
    assert is_prime(999_983 ** 2) is False


def test_max_subarray_sum():
    assert max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_subarray_sum([-3, -1]) == -1
    assert max_subarray_sum([5]) == 5
    assert max_subarray_sum([-5]) == -5
    assert max_subarray_sum([1, 2, 3]) == 6
    assert max_subarray_sum([0, 0]) == 0
    assert max_subarray_sum([2, -1, 2]) == 3
    assert max_subarray_sum([1] * 200000) == 200000
    assert max_subarray_sum([-1] * 200000 + [3]) == 3


def test_count_pairs_with_sum():
    assert count_pairs_with_sum([1, 5, 3, 3, 3], 6) == 4
    assert count_pairs_with_sum([], 1) == 0
    assert count_pairs_with_sum([3], 6) == 0
    assert count_pairs_with_sum([3, 3], 6) == 1
    assert count_pairs_with_sum([-1, 1, 0], 0) == 1
    assert count_pairs_with_sum([2, 2, 2, 2], 4) == 6
    assert count_pairs_with_sum([1, 2], 10) == 0
    assert count_pairs_with_sum([1] * 100000, 2) == 100000 * 99999 // 2


def test_analyze():
    assert analyze("a") == "O(n)"
    assert analyze("b") == "O(n^2)"
    assert analyze("c") == "O(log n)"
    assert analyze("d") == "O(n log n)"
    assert analyze("e") == "O(2^n)"
    assert analyze("f") == "O(1)"
    assert analyze("g") == "O(n^2)"
    assert analyze("h") == "O(n^2)"
    assert analyze("i") == "O(n log n)"
