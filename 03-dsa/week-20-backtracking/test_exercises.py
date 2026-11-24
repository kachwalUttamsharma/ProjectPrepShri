import itertools
from math import comb, factorial

from exercises import *


def norm(lst):
    """Sort inner lists then the outer list so order never matters."""
    return sorted(sorted(x) for x in lst)


# ---------- subsets ----------
def test_subsets_example():
    assert norm(subsets([1, 2, 3])) == norm([[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]])


def test_subsets_edge_cases():
    assert subsets([]) == [[]]
    assert norm(subsets([0])) == [[], [0]]


def test_subsets_count_and_independent_lists():
    res = subsets(list(range(8)))
    assert len(res) == 256
    assert len({tuple(sorted(x)) for x in res}) == 256
    assert all(isinstance(x, list) for x in res)
    ids = {id(x) for x in res}
    assert len(ids) == 256  # no aliasing of one shared list


def test_subsets_negative_numbers():
    assert norm(subsets([-1, 5])) == norm([[], [-1], [5], [-1, 5]])


# ---------- combinations ----------
def test_combinations_example():
    assert norm(combinations(4, 2)) == [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]


def test_combinations_edges():
    assert combinations(1, 1) == [[1]]
    assert combinations(3, 0) == [[]]
    assert norm(combinations(3, 3)) == [[1, 2, 3]]
    assert combinations(2, 3) == []


def test_combinations_counts():
    for n, k in [(6, 3), (7, 2), (8, 4)]:
        res = combinations(n, k)
        assert len(res) == comb(n, k)
        assert all(len(set(c)) == k and 1 <= min(c) and max(c) <= n for c in res)


# ---------- permutations ----------
def test_permutations_example():
    assert sorted(permutations([1, 2, 3])) == sorted(map(list, itertools.permutations([1, 2, 3])))


def test_permutations_edges():
    assert permutations([]) == [[]]
    assert permutations([7]) == [[7]]
    assert sorted(permutations([0, 1])) == [[0, 1], [1, 0]]


def test_permutations_count_unique_lists():
    res = permutations([1, 2, 3, 4, 5, 6])
    assert len(res) == factorial(6)
    assert len({tuple(p) for p in res}) == factorial(6)


# ---------- letter_combinations ----------
def test_letter_combinations_example():
    assert sorted(letter_combinations("23")) == ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]


def test_letter_combinations_edges():
    assert letter_combinations("") == []
    assert sorted(letter_combinations("2")) == ["a", "b", "c"]
    assert sorted(letter_combinations("7")) == ["p", "q", "r", "s"]


def test_letter_combinations_counts():
    assert len(letter_combinations("79")) == 16
    assert len(letter_combinations("2345")) == 81
    assert len(set(letter_combinations("7799"))) == 256


# ---------- generate_parentheses ----------
def test_parentheses_examples():
    assert sorted(generate_parentheses(3)) == ["((()))", "(()())", "(())()", "()(())", "()()()"]
    assert generate_parentheses(1) == ["()"]
    assert sorted(generate_parentheses(2)) == ["(())", "()()"]


def test_parentheses_zero():
    assert generate_parentheses(0) == [""]


def test_parentheses_catalan_counts_and_validity():
    for n, c in [(4, 14), (5, 42), (6, 132)]:
        res = generate_parentheses(n)
        assert len(res) == c == len(set(res))
        for s in res:
            bal = 0
            for ch in s:
                bal += 1 if ch == "(" else -1
                assert bal >= 0
            assert bal == 0 and len(s) == 2 * n


# ---------- combination_sum ----------
def test_combination_sum_examples():
    assert norm(combination_sum([2, 3, 6, 7], 7)) == [[2, 2, 3], [7]]
    assert norm(combination_sum([2, 3, 5], 8)) == [[2, 2, 2, 2], [2, 3, 3], [3, 5]]


def test_combination_sum_none_and_trivial():
    assert combination_sum([2], 1) == []
    assert combination_sum([5, 7], 3) == []
    assert norm(combination_sum([1], 3)) == [[1, 1, 1]]
    assert norm(combination_sum([3], 3)) == [[3]]


def test_combination_sum_no_duplicate_combos():
    res = norm(combination_sum([2, 3, 4, 7], 14))
    assert len(res) == len({tuple(r) for r in res})
    assert all(sum(r) == 14 for r in res)
    assert [2, 2, 2, 2, 2, 2, 2] in res and [7, 7] in res


# ---------- subsets_with_dup ----------
def test_subsets_dup_example():
    assert norm(subsets_with_dup([1, 2, 2])) == norm([[], [1], [1, 2], [1, 2, 2], [2], [2, 2]])


def test_subsets_dup_edges():
    assert subsets_with_dup([]) == [[]]
    assert norm(subsets_with_dup([0])) == [[], [0]]
    assert norm(subsets_with_dup([5, 5, 5])) == [[], [5], [5, 5], [5, 5, 5]]


def test_subsets_dup_unsorted_input_and_count():
    res = subsets_with_dup([2, 1, 2, 1])
    assert len(res) == 9  # (2+1) * (2+1)
    assert len({tuple(sorted(x)) for x in res}) == 9


# ---------- palindrome_partitioning ----------
def test_palindrome_partition_example():
    assert sorted(palindrome_partitioning("aab")) == [["a", "a", "b"], ["aa", "b"]]


def test_palindrome_partition_edges():
    assert palindrome_partitioning("a") == [["a"]]
    assert sorted(palindrome_partitioning("ab")) == [["a", "b"]]
    assert palindrome_partitioning("") == [[]]


def test_palindrome_partition_all_same_letter():
    # every composition of n is valid: 2^(n-1)
    res = palindrome_partitioning("aaaaa")
    assert len(res) == 16
    assert all("".join(p) == "aaaaa" for p in res)


def test_palindrome_partition_mixed():
    res = sorted(palindrome_partitioning("abbab"))
    assert res == sorted([["a", "b", "b", "a", "b"], ["a", "bb", "a", "b"], ["a", "b", "bab"], ["abba", "b"]])


# ---------- word_search ----------
BOARD = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]


def test_word_search_examples():
    assert word_search(BOARD, "ABCCED") is True
    assert word_search(BOARD, "SEE") is True
    assert word_search(BOARD, "ABCB") is False


def test_word_search_edge_cases():
    assert word_search([["a"]], "a") is True
    assert word_search([["a"]], "b") is False
    assert word_search([["a"]], "aa") is False
    assert word_search([["a", "b"]], "ba") is True


def test_word_search_cell_reuse_forbidden_and_board_unchanged():
    board = [["a", "a"]]
    assert word_search(board, "aaa") is False
    assert board == [["a", "a"]]
    b2 = [list(r) for r in BOARD]
    word_search(b2, "ABCCED")
    assert b2 == BOARD


def test_word_search_needs_backtracking():
    board = [["a", "a", "a"], ["a", "a", "b"]]
    assert word_search(board, "aaaaab") is True
    assert word_search(board, "aaaaaab") is False


def test_word_search_long_path_through_whole_board():
    board = [["a"] * 4 for _ in range(3)]
    assert word_search(board, "a" * 12) is True
    assert word_search(board, "a" * 13) is False  # length check: more letters than cells


# ---------- solve_n_queens ----------
def test_n_queens_small():
    assert solve_n_queens(1) == [["Q"]]
    assert solve_n_queens(2) == []
    assert solve_n_queens(3) == []


def test_n_queens_four():
    assert sorted(solve_n_queens(4)) == sorted([[".Q..", "...Q", "Q...", "..Q."],
                                                [ "..Q.", "Q...", "...Q", ".Q.."]])


def test_n_queens_counts():
    for n, c in [(5, 10), (6, 4), (7, 40), (8, 92)]:
        assert len(solve_n_queens(n)) == c


def test_n_queens_solutions_valid():
    for board in solve_n_queens(6):
        assert len(board) == 6 and all(len(r) == 6 for r in board)
        cols = [r.index("Q") for r in board]
        assert all(r.count("Q") == 1 for r in board)
        assert len(set(cols)) == 6
        assert len({r - c for r, c in enumerate(cols)}) == 6
        assert len({r + c for r, c in enumerate(cols)}) == 6
