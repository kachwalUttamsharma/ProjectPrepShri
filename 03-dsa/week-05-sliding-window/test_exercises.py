import random

from exercises import *


def test_max_sum_subarray_k():
    assert max_sum_subarray_k([2, 1, 5, 1, 3, 2], 3) == 9
    assert max_sum_subarray_k([-1, -2, -3], 2) == -3
    assert max_sum_subarray_k([5], 1) == 5
    assert max_sum_subarray_k([1, 2, 3], 3) == 6
    assert max_sum_subarray_k([1, 2], 3) == 0
    assert max_sum_subarray_k([], 1) == 0
    assert max_sum_subarray_k([1, 2], 0) == 0
    assert max_sum_subarray_k([4, -1, 4, -1], 2) == 3
    n = 300000
    assert max_sum_subarray_k([1] * n, n // 2) == n // 2


def test_contains_nearby_duplicate():
    assert contains_nearby_duplicate([1, 2, 3, 1], 3) is True
    assert contains_nearby_duplicate([1, 2, 3, 1, 2, 3], 2) is False
    assert contains_nearby_duplicate([1, 1], 0) is False
    assert contains_nearby_duplicate([1, 1], 1) is True
    assert contains_nearby_duplicate([], 5) is False
    assert contains_nearby_duplicate([7], 5) is False
    assert contains_nearby_duplicate([1, 0, 1, 1], 1) is True
    assert contains_nearby_duplicate([-1, -1], 1) is True
    assert contains_nearby_duplicate([1, 2, 3, 4, 1], 3) is False
    assert contains_nearby_duplicate(list(range(200000)) + [0], 200000) is True
    assert contains_nearby_duplicate(list(range(200000)) + [0], 199999) is False


def test_min_subarray_len():
    assert min_subarray_len(7, [2, 3, 1, 2, 4, 3]) == 2
    assert min_subarray_len(4, [1, 4, 4]) == 1
    assert min_subarray_len(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0
    assert min_subarray_len(100, [1, 2, 3]) == 0
    assert min_subarray_len(6, [1, 2, 3]) == 3
    assert min_subarray_len(5, []) == 0
    assert min_subarray_len(1, [1]) == 1
    assert min_subarray_len(15, [1, 2, 3, 4, 5]) == 5
    rng = random.Random(1)
    for _ in range(40):
        a = [rng.randint(1, 9) for _ in range(rng.randint(0, 20))]
        t = rng.randint(1, 40)
        best = 0
        for i in range(len(a)):
            for j in range(i, len(a)):
                if sum(a[i:j + 1]) >= t and (best == 0 or j - i + 1 < best):
                    best = j - i + 1
        assert min_subarray_len(t, a) == best
    assert min_subarray_len(10**9, [1] * 300000) == 0


def test_length_of_longest_substring():
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring("a") == 1
    assert length_of_longest_substring("abba") == 2
    assert length_of_longest_substring("tmmzuxt") == 5
    assert length_of_longest_substring(" ") == 1
    assert length_of_longest_substring("abcdefghijklmnopqrstuvwxyz" * 10000) == 26
    assert length_of_longest_substring("a" * 200000) == 1


def test_longest_ones():
    assert longest_ones([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) == 6
    assert longest_ones([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3) == 10
    assert longest_ones([0, 0, 0], 0) == 0
    assert longest_ones([], 3) == 0
    assert longest_ones([1, 1, 1], 0) == 3
    assert longest_ones([0, 0, 0], 5) == 3
    assert longest_ones([1, 0, 1], 0) == 1
    assert longest_ones([0], 1) == 1
    assert longest_ones([0, 1] * 100000, 1) == 3


def test_character_replacement():
    assert character_replacement("ABAB", 2) == 4
    assert character_replacement("AABABBA", 1) == 4
    assert character_replacement("", 2) == 0
    assert character_replacement("A", 0) == 1
    assert character_replacement("ABC", 0) == 1
    assert character_replacement("ABC", 2) == 3
    assert character_replacement("AAAA", 0) == 4
    assert character_replacement("ABBB", 2) == 4
    assert character_replacement("AABBBCCDD", 2) == 5
    assert character_replacement("AB" * 100000, 1) == 3


def test_check_inclusion():
    assert check_inclusion("ab", "eidbaooo") is True
    assert check_inclusion("ab", "eidboaoo") is False
    assert check_inclusion("", "abc") is True
    assert check_inclusion("a", "") is False
    assert check_inclusion("abc", "ab") is False
    assert check_inclusion("abc", "cba") is True
    assert check_inclusion("aab", "abab") is True
    assert check_inclusion("aab", "abcb") is False
    assert check_inclusion("adc", "dcda") is True
    assert check_inclusion("hello", "ooolleoooleh") is False
    assert check_inclusion("ab" * 50, "c" * 100000 + "ba" * 50) is True
    assert check_inclusion("ab" * 50, "c" * 100000) is False


def test_find_anagrams():
    assert find_anagrams("cbaebabacd", "abc") == [0, 6]
    assert find_anagrams("abab", "ab") == [0, 1, 2]
    assert find_anagrams("a", "ab") == []
    assert find_anagrams("", "a") == []
    assert find_anagrams("abc", "") == []
    assert find_anagrams("aaaa", "aa") == [0, 1, 2]
    assert find_anagrams("abc", "abc") == [0]
    assert find_anagrams("abc", "abd") == []
    assert find_anagrams("baa", "aa") == [1]
    assert find_anagrams("a" * 200000, "a" * 1000) == list(range(200000 - 1000 + 1))


def test_longest_substring_k_distinct():
    assert longest_substring_k_distinct("eceba", 2) == 3
    assert longest_substring_k_distinct("aa", 1) == 2
    assert longest_substring_k_distinct("abc", 0) == 0
    assert longest_substring_k_distinct("", 2) == 0
    assert longest_substring_k_distinct("abc", 10) == 3
    assert longest_substring_k_distinct("abaccc", 2) == 4
    assert longest_substring_k_distinct("a", 1) == 1
    assert longest_substring_k_distinct("abcabcabc", 3) == 9
    assert longest_substring_k_distinct("abcabcabc", 2) == 2
    assert longest_substring_k_distinct("ab" * 100000 + "c", 2) == 200000


def test_min_window():
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""
    assert min_window("aa", "aa") == "aa"
    assert min_window("abc", "") == ""
    assert min_window("", "a") == ""
    assert min_window("abc", "d") == ""
    assert min_window("ab", "b") == "b"
    assert min_window("bba", "ab") == "ba"
    assert min_window("cabwefgewcwaefgcf", "cae") == "cwae"
    assert min_window("abcdef", "abcdef") == "abcdef"
    assert min_window("xabcx" + "y" * 100000 + "abc", "abc") == "abc"
    assert min_window("a" * 200000 + "b", "ab") == "ab"
    # leftmost among equal-length answers
    assert min_window("abxab", "ab") == "ab"


def test_max_sliding_window():
    assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert max_sliding_window([1], 1) == [1]
    assert max_sliding_window([], 3) == []
    assert max_sliding_window([1, 2], 0) == []
    assert max_sliding_window([1, 2], 3) == []
    assert max_sliding_window([1, -1], 1) == [1, -1]
    assert max_sliding_window([9, 11], 2) == [11]
    assert max_sliding_window([4, 3, 2, 1], 2) == [4, 3, 2]
    assert max_sliding_window([1, 2, 3, 4], 2) == [2, 3, 4]
    assert max_sliding_window([5, 5, 5, 5], 3) == [5, 5]
    assert max_sliding_window([7, 2, 4], 2) == [7, 4]
    rng = random.Random(7)
    a = [rng.randint(-100, 100) for _ in range(300)]
    for k in (1, 2, 5, 17, 300):
        assert max_sliding_window(a, k) == [max(a[i:i + k]) for i in range(len(a) - k + 1)]
    big = list(range(300000, 0, -1))
    assert max_sliding_window(big, 1000)[:3] == [300000, 299999, 299998]
    assert len(max_sliding_window(big, 1000)) == 300000 - 1000 + 1
