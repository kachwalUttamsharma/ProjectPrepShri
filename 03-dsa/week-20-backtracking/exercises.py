"""Week 20 exercises: backtracking. Replace each `...` with your code.

The order of the lists you return does not matter (tests sort them), but the order of
elements *inside* each subset/permutation/combination should follow the examples.
"""


def subsets(nums):
    """LeetCode 78. Return all subsets of `nums` (distinct integers), including [] and nums.

    Example: [1,2,3] -> [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]] (any order)

    Hint: for i in range(start, n): choose nums[i], recurse with i+1, un-choose.
    Expected: O(n * 2^n) time.
    """
    ...


def combinations(n, k):
    """LeetCode 77. Return all k-element combinations of the numbers 1..n (each ascending).

    Example: n=4, k=2 -> [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]; k=0 -> [[]]

    Hint: prune when fewer than k - len(path) numbers remain.
    Expected: O(k * C(n,k)).
    """
    ...


def permutations(nums):
    """LeetCode 46. Return all permutations of `nums` (distinct integers).

    Example: [1,2,3] -> 6 permutations;  [] -> [[]]

    Hint: `used` boolean array, or swap elements in place.
    Expected: O(n * n!).
    """
    ...


def letter_combinations(digits):
    """LeetCode 17. Phone keypad (2=abc 3=def 4=ghi 5=jkl 6=mno 7=pqrs 8=tuv 9=wxyz).
    Return all strings the digit string could represent. Empty input -> [].

    Example: "23" -> ["ad","ae","af","bd","be","bf","cd","ce","cf"]

    Hint: one level of recursion per digit.
    Expected: O(4^n * n).
    """
    ...


def generate_parentheses(n):
    """LeetCode 22. Return all well-formed strings of n pairs of parentheses.

    Example: n=3 -> ["((()))","(()())","(())()","()(())","()()()"]

    Hint: track open/close counts; add "(" if open < n, add ")" if close < open.
    Expected: O(4^n / sqrt(n)) outputs.
    """
    ...


def combination_sum(candidates, target):
    """LeetCode 39. `candidates` are distinct positive ints, each usable unlimited times.
    Return all unique combinations (as lists, any order inside) summing to target.

    Example: [2,3,6,7], 7 -> [[2,2,3],[7]];  [2], 1 -> []

    Hint: recurse with the same index i to allow reuse; sort and break when too large.
    Expected: exponential; bounded by target / min(candidates) depth.
    """
    ...


def subsets_with_dup(nums):
    """LeetCode 90. `nums` may contain duplicates. Return all unique subsets.

    Example: [1,2,2] -> [[],[1],[1,2],[1,2,2],[2],[2,2]]

    Hint: sort; at the same recursion level skip nums[i] if it equals nums[i-1] (i > start).
    Expected: O(n * 2^n).
    """
    ...


def palindrome_partitioning(s):
    """LeetCode 131. Partition s so every piece is a palindrome. Return all partitions.

    Example: "aab" -> [["a","a","b"],["aa","b"]]

    Hint: choose the end of the next piece; only recurse if s[start:end] is a palindrome.
    Expected: O(n * 2^n).
    """
    ...


def word_search(board, word):
    """LeetCode 79. Return True if `word` can be built from sequentially adjacent
    (up/down/left/right) cells of the board, using each cell at most once.

    Example: board=[["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCCED" -> True

    Hint: DFS from every cell; mark the cell visited (e.g. replace with "#") and restore.
    Expected: O(R*C * 3^L).
    """
    ...


def solve_n_queens(n):
    """LeetCode 51. Return all distinct solutions to the n-queens puzzle. Each solution is a
    list of n strings of length n using "Q" and "." (one row per string).

    Example: n=4 -> [[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]

    Hint: place row by row; sets for used columns, r-c diagonals and r+c anti-diagonals.
    Expected: roughly O(n!).
    """
    ...
