import itertools
import math
import random

from exercises import *


# ---------- climb_stairs ----------
def test_climb_examples():
    assert climb_stairs(2) == 2
    assert climb_stairs(3) == 3
    assert climb_stairs(5) == 8


def test_climb_base_cases():
    assert climb_stairs(0) == 1
    assert climb_stairs(1) == 1


def test_climb_large_no_recursion_blowup():
    assert climb_stairs(45) == 1836311903
    assert climb_stairs(90) == 4660046610375530309  # fib(91)


# ---------- house_robber ----------
def test_rob_examples():
    assert house_robber([2, 7, 9, 3, 1]) == 12
    assert house_robber([1, 2, 3, 1]) == 4


def test_rob_edges():
    assert house_robber([]) == 0
    assert house_robber([5]) == 5
    assert house_robber([2, 1]) == 2
    assert house_robber([0, 0, 0]) == 0


def test_rob_skip_two_houses_is_best():
    assert house_robber([2, 1, 1, 2]) == 4
    assert house_robber([100, 1, 1, 100]) == 200


def test_rob_matches_bruteforce():
    rng = random.Random(3)
    for _ in range(60):
        a = [rng.randint(0, 20) for _ in range(rng.randint(0, 10))]
        best = 0
        for mask in range(1 << len(a)):
            if mask & (mask >> 1):
                continue
            best = max(best, sum(a[i] for i in range(len(a)) if mask >> i & 1))
        assert house_robber(a) == best


# ---------- house_robber_circular ----------
def test_rob_circular_examples():
    assert house_robber_circular([2, 3, 2]) == 3
    assert house_robber_circular([1, 2, 3, 1]) == 4
    assert house_robber_circular([1, 2, 3]) == 3


def test_rob_circular_edges():
    assert house_robber_circular([5]) == 5
    assert house_robber_circular([2, 9]) == 9
    assert house_robber_circular([0]) == 0


def test_rob_circular_matches_bruteforce():
    rng = random.Random(4)
    for _ in range(60):
        a = [rng.randint(0, 20) for _ in range(rng.randint(1, 10))]
        n = len(a)
        best = 0
        for mask in range(1 << n):
            ok = all(not (mask >> i & 1 and mask >> ((i + 1) % n) & 1) for i in range(n) if n > 1)
            if ok:
                best = max(best, sum(a[i] for i in range(n) if mask >> i & 1))
        assert house_robber_circular(a) == best


# ---------- max_subarray ----------
def test_max_subarray_examples():
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_subarray([1]) == 1
    assert max_subarray([5, 4, -1, 7, 8]) == 23


def test_max_subarray_all_negative():
    assert max_subarray([-3, -1, -2]) == -1
    assert max_subarray([-5]) == -5


def test_max_subarray_matches_bruteforce():
    rng = random.Random(5)
    for _ in range(80):
        a = [rng.randint(-9, 9) for _ in range(rng.randint(1, 12))]
        best = max(sum(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1))
        assert max_subarray(a) == best


# ---------- max_product_subarray ----------
def test_max_product_examples():
    assert max_product_subarray([2, 3, -2, 4]) == 6
    assert max_product_subarray([-2, 0, -1]) == 0
    assert max_product_subarray([-2, 3, -4]) == 24


def test_max_product_edges():
    assert max_product_subarray([-3]) == -3
    assert max_product_subarray([0]) == 0
    assert max_product_subarray([-2, -3, -4]) == 12
    assert max_product_subarray([0, 2]) == 2


def test_max_product_matches_bruteforce():
    rng = random.Random(6)
    for _ in range(100):
        a = [rng.randint(-4, 4) for _ in range(rng.randint(1, 9))]
        best = max(
            math.prod(a[i:j]) for i in range(len(a)) for j in range(i + 1, len(a) + 1)
        )
        assert max_product_subarray(a) == best


# ---------- coin_change ----------
def test_coin_change_examples():
    assert coin_change([1, 2, 5], 11) == 3
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0


def test_coin_change_greedy_fails():
    assert coin_change([1, 3, 4], 6) == 2
    assert coin_change([186, 419, 83, 408], 6249) == 20


def test_coin_change_edges():
    assert coin_change([], 0) == 0
    assert coin_change([5], 5) == 1
    assert coin_change([2], 1) == -1
    assert coin_change([1, 2, 5], 100) == 20


def test_coin_change_matches_bruteforce_small():
    rng = random.Random(7)
    for _ in range(40):
        coins = rng.sample(range(1, 9), rng.randint(1, 3))
        amt = rng.randint(0, 20)
        best = None
        for cnt in range(amt + 1):
            if any(sum(c) == amt for c in itertools.combinations_with_replacement(coins, cnt)):
                best = cnt
                break
        assert coin_change(coins, amt) == (-1 if best is None else best)


# ---------- coin_change_ways ----------
def test_coin_ways_examples():
    assert coin_change_ways(5, [1, 2, 5]) == 4
    assert coin_change_ways(3, [2]) == 0
    assert coin_change_ways(10, [10]) == 1


def test_coin_ways_zero_amount():
    assert coin_change_ways(0, [1, 2]) == 1
    assert coin_change_ways(0, []) == 1


def test_coin_ways_combinations_not_permutations():
    assert coin_change_ways(4, [1, 2, 3]) == 4  # 1111,112,22,13
    assert coin_change_ways(100, [1, 5, 10, 25]) == 242


def test_coin_ways_no_coins():
    assert coin_change_ways(5, []) == 0


# ---------- length_of_lis ----------
def test_lis_examples():
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4
    assert length_of_lis([7, 7, 7, 7]) == 1


def test_lis_edges():
    assert length_of_lis([]) == 0
    assert length_of_lis([4]) == 1
    assert length_of_lis([5, 4, 3, 2, 1]) == 1
    assert length_of_lis(list(range(100))) == 100


def test_lis_tails_trick_pitfall():
    assert length_of_lis([4, 10, 4, 3, 8, 9]) == 3
    assert length_of_lis([1, 3, 6, 7, 9, 4, 10, 5, 6]) == 6


def test_lis_matches_n2():
    rng = random.Random(8)
    for _ in range(60):
        a = [rng.randint(-10, 10) for _ in range(rng.randint(0, 25))]
        dp = [1] * len(a)
        for i in range(len(a)):
            for j in range(i):
                if a[j] < a[i]:
                    dp[i] = max(dp[i], dp[j] + 1)
        assert length_of_lis(a) == max(dp, default=0)


def test_lis_large_input_is_fast():
    assert length_of_lis(list(range(20000, 0, -1)) + list(range(20000))) == 20000


# ---------- word_break ----------
def test_word_break_examples():
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("applepenapple", ["apple", "pen"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False


def test_word_break_edges():
    assert word_break("a", ["a"]) is True
    assert word_break("a", ["b"]) is False
    assert word_break("a", []) is False
    assert word_break("", ["a"]) is True


def test_word_break_overlapping_prefix_words():
    assert word_break("aaaaaaa", ["aaaa", "aaa"]) is True
    assert word_break("aaaaa", ["aaaa", "aaa"]) is False


def test_word_break_exponential_trap():
    s = "a" * 60 + "b"
    assert word_break(s, ["a", "aa", "aaa", "aaaa"]) is False


# ---------- num_decodings ----------
def test_decode_examples():
    assert num_decodings("12") == 2
    assert num_decodings("226") == 3
    assert num_decodings("06") == 0


def test_decode_zeros():
    assert num_decodings("0") == 0
    assert num_decodings("10") == 1
    assert num_decodings("20") == 1
    assert num_decodings("30") == 0
    assert num_decodings("100") == 0
    assert num_decodings("2101") == 1
    assert num_decodings("27") == 1


def test_decode_single_and_runs():
    assert num_decodings("1") == 1
    assert num_decodings("11111") == 8  # fibonacci
    assert num_decodings("9" * 30) == 1


def test_decode_long_input():
    assert num_decodings("1" * 40) == 165580141
