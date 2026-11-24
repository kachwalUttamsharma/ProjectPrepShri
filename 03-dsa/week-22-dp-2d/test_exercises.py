import itertools
import random

from exercises import *


def test_unique_paths():
    assert unique_paths(3, 7) == 28
    assert unique_paths(1, 1) == 1
    assert unique_paths(1, 5) == 1
    assert unique_paths(5, 1) == 1
    assert unique_paths(3, 2) == 3
    assert unique_paths(10, 10) == 48620
    assert unique_paths(23, 12) == 193536720


def test_min_path_sum():
    assert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    assert min_path_sum([[1, 2, 3], [4, 5, 6]]) == 12
    assert min_path_sum([[5]]) == 5
    assert min_path_sum([[1, 2, 3]]) == 6
    assert min_path_sum([[1], [2], [3]]) == 6
    assert min_path_sum([]) == 0
    assert min_path_sum([[0, 0], [0, 0]]) == 0


def test_min_path_sum_does_not_mutate():
    g = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    assert min_path_sum(g) == 7
    assert g == [[1, 3, 1], [1, 5, 1], [4, 2, 1]]


def test_unique_paths_with_obstacles():
    assert unique_paths_with_obstacles([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) == 2
    assert unique_paths_with_obstacles([[0, 1], [0, 0]]) == 1
    assert unique_paths_with_obstacles([[1]]) == 0
    assert unique_paths_with_obstacles([[0]]) == 1
    assert unique_paths_with_obstacles([[1, 0]]) == 0
    assert unique_paths_with_obstacles([[0, 1]]) == 0
    assert unique_paths_with_obstacles([[0, 0], [1, 1]]) == 0
    assert unique_paths_with_obstacles([[0, 0, 0], [0, 0, 0]]) == 3


def test_lcs():
    assert longest_common_subsequence("abcde", "ace") == 3
    assert longest_common_subsequence("abc", "abc") == 3
    assert longest_common_subsequence("abc", "def") == 0
    assert longest_common_subsequence("", "abc") == 0
    assert longest_common_subsequence("abc", "") == 0
    assert longest_common_subsequence("", "") == 0
    assert longest_common_subsequence("AGGTAB", "GXTXAYB") == 4
    assert longest_common_subsequence("bl", "yby") == 1
    assert longest_common_subsequence("a" * 50, "a" * 30) == 30


def test_edit_distance():
    assert edit_distance("horse", "ros") == 3
    assert edit_distance("intention", "execution") == 5
    assert edit_distance("", "") == 0
    assert edit_distance("", "abc") == 3
    assert edit_distance("abc", "") == 3
    assert edit_distance("abc", "abc") == 0
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance("a", "b") == 1
    assert edit_distance("sea", "eat") == 2


def test_knapsack_basic():
    assert knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7) == 9
    assert knapsack_01([], [], 10) == 0
    assert knapsack_01([5], [10], 4) == 0
    assert knapsack_01([5], [10], 5) == 10
    assert knapsack_01([1, 2, 3], [6, 10, 12], 5) == 22
    assert knapsack_01([2, 2], [3, 3], 0) == 0


def test_knapsack_item_used_once():
    # reuse would give 20; 0/1 gives 10
    assert knapsack_01([1], [10], 2) == 10


def test_knapsack_vs_bruteforce():
    rng = random.Random(7)
    for _ in range(60):
        n = rng.randint(0, 8)
        w = [rng.randint(1, 6) for _ in range(n)]
        v = [rng.randint(1, 20) for _ in range(n)]
        cap = rng.randint(0, 15)
        best = 0
        for mask in range(1 << n):
            tw = sum(w[i] for i in range(n) if mask >> i & 1)
            if tw <= cap:
                best = max(best, sum(v[i] for i in range(n) if mask >> i & 1))
        assert knapsack_01(w, v, cap) == best


def test_can_partition():
    assert can_partition([1, 5, 11, 5]) is True
    assert can_partition([1, 2, 3, 5]) is False
    assert can_partition([1, 1]) is True
    assert can_partition([2]) is False
    assert can_partition([]) is True
    assert can_partition([100, 100, 100, 100, 99, 101]) is True
    assert can_partition([3, 3, 3, 4, 5]) is True
    assert can_partition([1, 2, 5]) is False


def test_maximal_square():
    m = [list("10100"), list("10111"), list("11111"), list("10010")]
    assert maximal_square(m) == 4
    assert maximal_square([["0", "1"], ["1", "0"]]) == 1
    assert maximal_square([["0"]]) == 0
    assert maximal_square([["1"]]) == 1
    assert maximal_square([]) == 0
    assert maximal_square([list("111"), list("111"), list("111")]) == 9
    assert maximal_square([list("1111")]) == 1
    assert maximal_square([list("11"), list("11"), list("11")]) == 4


def test_coin_change_ways():
    assert coin_change_ways(5, [1, 2, 5]) == 4
    assert coin_change_ways(3, [2]) == 0
    assert coin_change_ways(10, [10]) == 1
    assert coin_change_ways(0, [1, 2]) == 1
    assert coin_change_ways(0, []) == 1
    assert coin_change_ways(4, []) == 0
    assert coin_change_ways(4, [1, 2, 3]) == 4  # combos, not permutations
    assert coin_change_ways(100, [1, 5, 10, 25, 50]) == 292


def test_longest_palindromic_subsequence():
    assert longest_palindromic_subsequence("bbbab") == 4
    assert longest_palindromic_subsequence("cbbd") == 2
    assert longest_palindromic_subsequence("a") == 1
    assert longest_palindromic_subsequence("") == 0
    assert longest_palindromic_subsequence("abcd") == 1
    assert longest_palindromic_subsequence("racecar") == 7
    assert longest_palindromic_subsequence("agbdba") == 5
    assert longest_palindromic_subsequence("aaaa") == 4


def test_lps_vs_bruteforce():
    rng = random.Random(3)
    for _ in range(40):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 9)))
        best = 0
        for mask in range(1 << len(s)):
            t = [s[i] for i in range(len(s)) if mask >> i & 1]
            if t == t[::-1]:
                best = max(best, len(t))
        assert longest_palindromic_subsequence(s) == best
