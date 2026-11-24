"""Week 22 exercises: 2-D dynamic programming. Replace each `...` with your code."""


def unique_paths(m, n):
    """Robot starts top-left of an m x n grid, moves only right or down.
    Return the number of paths to the bottom-right.

    unique_paths(3, 7) -> 28
    unique_paths(1, 5) -> 1
    Expected: O(m*n) time, O(n) space.
    Hint: dp[r][c] = dp[r-1][c] + dp[r][c-1]. Only the previous row is needed.
    """
    ...


def min_path_sum(grid):
    """Min sum of a path from top-left to bottom-right moving right/down.
    Empty grid -> 0.

    [[1,3,1],[1,5,1],[4,2,1]] -> 7
    Expected: O(m*n) time, O(n) space.
    Hint: first row/column have only one way to be reached.
    """
    ...


def unique_paths_with_obstacles(grid):
    """Like unique_paths but cells with 1 are obstacles (0 = free).
    Return number of paths; 0 if start or end is blocked.

    [[0,0,0],[0,1,0],[0,0,0]] -> 2
    [[1]] -> 0
    Expected: O(m*n) time, O(n) space.
    Hint: an obstacle cell has dp = 0.
    """
    ...


def longest_common_subsequence(a, b):
    """Length of the longest common subsequence of strings a and b.

    ("abcde", "ace") -> 3
    ("abc", "def") -> 0
    Expected: O(len(a)*len(b)) time, O(min) space possible.
    Hint: dp[i][j] for prefixes a[:i], b[:j]. Match -> 1 + dp[i-1][j-1];
    else max(dp[i-1][j], dp[i][j-1]).
    """
    ...


def edit_distance(a, b):
    """Min insert/delete/replace operations to turn a into b.

    ("horse", "ros") -> 3
    ("", "abc") -> 3
    Expected: O(len(a)*len(b)) time.
    Hint: dp[i][0] = i, dp[0][j] = j. On mismatch take 1 + min(replace, delete, insert).
    """
    ...


def knapsack_01(weights, values, capacity):
    """0/1 knapsack: each item used at most once. Return max total value
    with total weight <= capacity.

    weights=[1,3,4,5], values=[1,4,5,7], capacity=7 -> 9
    Expected: O(n*capacity) time, O(capacity) space.
    Hint: 1-D dp, iterate capacity DOWNWARD so an item is not reused.
    """
    ...


def can_partition(nums):
    """Can nums (positive ints) be split into two subsets with equal sum?

    [1,5,11,5] -> True
    [1,2,3,5] -> False
    Expected: O(n*sum) time, O(sum) space.
    Hint: subset-sum to target = total/2; odd total -> False immediately.
    """
    ...


def maximal_square(matrix):
    """Matrix of '0'/'1' strings. Return the AREA of the largest square of all '1's.

    [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]] -> 4
    Expected: O(m*n) time.
    Hint: dp[r][c] = side of largest square ending at (r,c) as bottom-right:
    1 + min(up, left, up-left) when cell is '1'.
    """
    ...


def coin_change_ways(amount, coins):
    """Number of combinations (order does not matter) of coins (unlimited use)
    summing to amount. amount 0 -> 1.

    (5, [1,2,5]) -> 4
    (3, [2]) -> 0
    Expected: O(amount * len(coins)) time, O(amount) space.
    Hint: loop coins OUTER, amounts inner (ascending) to count combinations,
    not permutations.
    """
    ...


def longest_palindromic_subsequence(s):
    """Length of the longest palindromic SUBSEQUENCE of s. Empty -> 0.

    "bbbab" -> 4
    "cbbd" -> 2
    Expected: O(n^2) time.
    Hint: interval DP dp[i][j]; or LCS(s, reversed s).
    """
    ...
