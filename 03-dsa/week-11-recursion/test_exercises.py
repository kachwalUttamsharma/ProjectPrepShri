import itertools
import math
import time

from exercises import *


def norm(lists):
    return sorted(sorted(x) for x in lists)


def test_fib():
    assert [fib(i) for i in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert fib(50) == 12586269025
    assert fib(90) == 2880067194370816120
    t = time.time()
    assert fib(500) % 1000 == 125
    assert time.time() - t < 1


def test_power():
    assert power(2, 10) == 1024
    assert power(2, -2) == 0.25
    assert power(5, 0) == 1
    assert power(0, 5) == 0
    assert power(1, 10 ** 9) == 1
    assert power(-1, 10 ** 9 + 1) == -1
    assert power(-2, 3) == -8
    assert power(-2, 4) == 16
    assert abs(power(2.0, 0.5 * 2) - 2) < 1e-9
    assert abs(power(1.0001, 10000) - 1.0001 ** 10000) < 1e-6
    assert power(2, 2000) == 2 ** 2000


def test_is_palindrome():
    assert is_palindrome("") is True
    assert is_palindrome("a") is True
    assert is_palindrome("aa") is True
    assert is_palindrome("ab") is False
    assert is_palindrome("racecar") is True
    assert is_palindrome("abca") is False
    assert is_palindrome("Aa") is False
    assert is_palindrome("abccba") is True
    assert is_palindrome("a" * 500) is True


def test_subsets():
    assert norm(subsets([])) == [[]]
    assert norm(subsets([1])) == [[], [1]]
    assert norm(subsets([1, 2])) == [[], [1], [1, 2], [2]]
    nums = [3, -1, 4, 0]
    res = subsets(nums)
    assert len(res) == 16
    assert len({tuple(sorted(r)) for r in res}) == 16
    assert norm(res) == norm([list(c) for r in range(5) for c in itertools.combinations(nums, r)])
    assert len(subsets(list(range(14)))) == 2 ** 14


def test_permutations():
    assert permutations([]) in ([[]], [])
    assert permutations([1]) == [[1]]
    assert sorted(permutations([1, 2])) == [[1, 2], [2, 1]]
    res = permutations([1, 2, 3])
    assert len(res) == 6 and len({tuple(r) for r in res}) == 6
    assert sorted(res) == sorted(list(p) for p in itertools.permutations([1, 2, 3]))
    res = permutations([-1, 0, 5, 9, 2])
    assert len(res) == 120 and len({tuple(r) for r in res}) == 120
    assert all(sorted(r) == [-1, 0, 2, 5, 9] for r in res)
    assert len(permutations(list(range(8)))) == 40320


def test_combinations():
    assert sorted(combinations(4, 2)) == [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
    assert combinations(3, 0) == [[]]
    assert combinations(1, 1) == [[1]]
    assert combinations(3, 3) == [[1, 2, 3]]
    assert sorted(combinations(3, 1)) == [[1], [2], [3]]
    res = combinations(15, 7)
    assert len(res) == math.comb(15, 7)
    assert all(r == sorted(r) and len(set(r)) == 7 for r in res)
    assert len({tuple(r) for r in res}) == len(res)


def test_combination_sum():
    assert norm(combination_sum([2, 3, 6, 7], 7)) == [[2, 2, 3], [7]]
    assert norm(combination_sum([2, 3, 5], 8)) == [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    assert combination_sum([2], 1) == []
    assert norm(combination_sum([2], 4)) == [[2, 2]]
    assert combination_sum([], 5) == []
    assert norm(combination_sum([1], 3)) == [[1, 1, 1]]
    assert norm(combination_sum([7, 3, 2], 18)) == norm(_brute_cs([7, 3, 2], 18))
    res = combination_sum([2, 3, 5, 7], 30)
    assert all(sum(r) == 30 for r in res)
    assert len({tuple(sorted(r)) for r in res}) == len(res)


def _brute_cs(c, t):
    out = set()

    def go(i, rem, cur):
        if rem == 0:
            out.add(tuple(sorted(cur)))
            return
        if i == len(c) or rem < 0:
            return
        go(i + 1, rem, cur)
        go(i, rem - c[i], cur + [c[i]])
    go(0, t, [])
    return out


def test_generate_parentheses():
    assert generate_parentheses(0) in ([""], [])
    assert generate_parentheses(1) == ["()"]
    assert sorted(generate_parentheses(2)) == ["(())", "()()"]
    assert sorted(generate_parentheses(3)) == ["((()))", "(()())", "(())()", "()(())", "()()()"]
    res = generate_parentheses(8)
    assert len(res) == len(set(res)) == 1430
    for s in res:
        bal = 0
        for ch in s:
            bal += 1 if ch == "(" else -1
            assert bal >= 0
        assert bal == 0 and len(s) == 16


def test_letter_combinations():
    assert letter_combinations("") == []
    assert sorted(letter_combinations("2")) == ["a", "b", "c"]
    assert sorted(letter_combinations("23")) == ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]
    assert len(letter_combinations("79")) == 16
    assert len(letter_combinations("2345")) == 81
    res = letter_combinations("7777")
    assert len(res) == 256 and len(set(res)) == 256


def test_word_search():
    b = [["A", "B"], ["C", "D"]]
    assert word_search(b, "ABDC") is True
    assert word_search(b, "ABCD") is False
    assert word_search(b, "A") is True
    assert word_search(b, "E") is False
    assert word_search([["A"]], "A") is True
    assert word_search([["A"]], "AA") is False
    b = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    assert word_search(b, "ABCCED") is True
    assert word_search(b, "SEE") is True
    assert word_search(b, "ABCB") is False
    assert word_search([["a", "a"]], "aaa") is False
    big = [["a"] * 5 for _ in range(5)]
    assert word_search(big, "a" * 25) is True
    assert word_search(big, "a" * 26) is False
    small = [["a"] * 4 for _ in range(4)]
    assert word_search(small, "a" * 15 + "b") is False
    assert b == [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]


def test_n_queens_count():
    assert n_queens_count(1) == 1
    assert n_queens_count(2) == 0
    assert n_queens_count(3) == 0
    assert n_queens_count(4) == 2
    assert n_queens_count(5) == 10
    assert n_queens_count(6) == 4
    assert n_queens_count(7) == 40
    assert n_queens_count(8) == 92
    assert n_queens_count(9) == 352
