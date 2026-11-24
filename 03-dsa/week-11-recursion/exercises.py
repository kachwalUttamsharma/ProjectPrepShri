"""Week 11: Recursion and backtracking.
Replace each `...` with your code. Run: .venv/bin/pytest 03-dsa/week-11-recursion -q
Where order of results is not specified, tests compare sorted results."""


def fib(n):
    """Return the n-th Fibonacci number (fib(0)=0, fib(1)=1) using memoization.
    Example: 10 -> 55 ; 90 -> 2880067194370816120
    Time O(n), Space O(n). Must not be exponential.
    Hint: functools.cache on an inner function, or a dict memo."""
    ...


def power(x, n):
    """Return x ** n using fast exponentiation (n may be negative; no ** or pow).
    Example: (2, 10) -> 1024 ; (2, -2) -> 0.25 ; (5, 0) -> 1
    Time O(log |n|), Space O(log |n|).
    Hint: x^n = (x^(n//2))^2 * (x if n odd). Handle n < 0 via 1 / power(x, -n)."""
    ...


def is_palindrome(s):
    """Return True if s reads the same backwards, using recursion on s[lo:hi].
    Ignore nothing: case and characters matter. '' and 1 char are palindromes.
    Example: 'racecar' -> True ; 'ab' -> False
    Time O(n), Space O(n) call stack. Hint: compare ends, recurse on the inside."""
    ...


def subsets(nums):
    """Return all subsets (the power set) of a list of DISTINCT ints, as lists.
    Any order of subsets / elements within a subset is accepted.
    Example: [1,2] -> [[], [1], [2], [1,2]]
    Time O(n * 2^n), Space O(n) extra (excluding output).
    Hint: for each element, choose to include it or not."""
    ...


def permutations(nums):
    """Return all permutations of a list of DISTINCT ints.
    Example: [1,2,3] -> 6 lists such as [1,2,3], [1,3,2], ...
    Time O(n * n!), Space O(n) extra.
    Hint: backtrack with a `used` set/array, or swap elements in place."""
    ...


def combinations(n, k):
    """Return all k-element combinations of 1..n, each as an ascending list.
    Example: (4, 2) -> [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]] ; (3, 0) -> [[]]
    Time O(k * C(n,k)), Space O(k) extra.
    Hint: pass a `start` index; prune when too few numbers remain."""
    ...


def combination_sum(candidates, target):
    """candidates: DISTINCT positive ints, each reusable unlimited times.
    Return all UNIQUE combinations (as lists; order within a list/overall is free,
    but [2,3] and [3,2] count as the same combination) summing to target.
    Example: ([2,3,6,7], 7) -> [[2,2,3],[7]] ; ([2], 1) -> []
    Time O(N^(T/M)) worst case, Space O(T/M) depth.
    Hint: pass a start index and recurse with the same index to allow reuse."""
    ...


def generate_parentheses(n):
    """Return all well-formed strings with n pairs of parentheses.
    Example: 3 -> ['((()))','(()())','(())()','()(())','()()()']
    Time O(4^n / sqrt(n)) (Catalan), Space O(n) depth.
    Hint: add '(' if open < n; add ')' if close < open. Only valid prefixes are built."""
    ...


def letter_combinations(digits):
    """Phone keypad (2=abc 3=def 4=ghi 5=jkl 6=mno 7=pqrs 8=tuv 9=wxyz).
    Return all letter strings the digit string could represent; [] if digits is ''.
    Example: '23' -> ['ad','ae','af','bd','be','bf','cd','ce','cf']
    Time O(4^n * n), Space O(n) depth."""
    ...


def word_search(board, word):
    """board: list of lists of single chars. Return True if word can be formed by
    sequentially adjacent (up/down/left/right) cells, each cell used at most once.
    Example: board [['A','B'],['C','D']], 'ABDC' -> True ; 'ABCD' -> False
    Time O(R*C*3^L), Space O(L).
    Hint: DFS from every cell; mark visited in place (restore on backtrack)."""
    ...


def n_queens_count(n):
    """Return the number of ways to place n queens on an n x n board with none
    attacking another. Example: 1 -> 1 ; 4 -> 2 ; 6 -> 4 ; 8 -> 92  (HARD)
    Time O(n!), Space O(n).
    Hint: place one queen per row; track used columns and both diagonals
    (row - col and row + col) in sets."""
    ...
