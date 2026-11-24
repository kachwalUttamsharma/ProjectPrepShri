# Week 11: Recursion and Backtracking

## 1. Concept
A recursive function solves a problem by solving smaller copies of it. Every
recursion needs:
1. **Base case**: input small enough to answer directly.
2. **Recursive case**: reduce the input and combine the results.
3. **Progress**: each call must move toward the base case.

Backtracking = recursion that builds a candidate step by step, **chooses**, **explores**,
then **un-chooses** (undo) to try the next option. It walks a decision tree and prunes
branches that cannot lead to a solution.

## 2. How to recognize the pattern
- "Return ALL subsets / permutations / combinations / paths / arrangements".
- "Count the ways" where choices interact (N-Queens, word search).
- Input is small (n <= ~15-20) - exponential solutions are expected.
- The problem has self-similar structure (tree, divide in halves, x^n from x^(n/2)).
- Overlapping subproblems (fib) -> add memoization (the bridge to DP in later weeks).

## 3. Template code
**Plain recursion with memo**
```python
from functools import cache
@cache
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
```
**Backtracking skeleton**
```python
def solve(choices):
    res, cur = [], []
    def go(start):
        if is_complete(cur):
            res.append(cur[:])        # COPY - cur keeps changing
            return
        for i in range(start, len(choices)):
            if not valid(choices[i]):  # prune early
                continue
            cur.append(choices[i])     # choose
            go(i + 1)                  # explore (i for reuse, 0/used[] for permutations)
            cur.pop()                  # un-choose
    go(0)
    return res
```
Which "next index" to pass:
- Subsets/combinations (order irrelevant, no reuse): `go(i + 1)`.
- Reuse allowed (combination sum): `go(i)`.
- Permutations (order matters): loop over all, skip `used`.
- Duplicates in input: sort, then `if i > start and nums[i] == nums[i-1]: continue`.

**Include/exclude style** (subsets): `go(i+1)` without nums[i], then with it.

## 4. Complexity
Think "number of nodes in the decision tree x work per node".
- Subsets: O(n * 2^n). Permutations: O(n * n!). Combinations C(n,k): O(k * C(n,k)).
- Parentheses: Catalan number ~ 4^n / n^1.5. N-Queens: ~O(n!) with pruning.
- Space: recursion depth (call stack) plus output. Fast power: O(log n) depth.
- Python's default recursion limit is 1000; depth of ~n for linear recursion on big n
  will crash (`RecursionError`). Fine for backtracking depth <= ~30.

## 5. Common mistakes
- Appending `cur` instead of `cur[:]` / `list(cur)`: all results alias one list.
- Forgetting to undo the choice (`pop`, restoring the grid cell, `set.remove`).
- Missing or wrong base case -> infinite recursion; base case order matters
  (check "found" before "out of bounds" or vice versa deliberately).
- Duplicate results from not using a `start` index.
- Mutating the input (word search) without restoring it.
- Using a mutable default argument for accumulators.
- Exponential recursion without memo (naive fib) when subproblems overlap.

## 6. Interview tips
- Draw the decision tree for a size-2 or size-3 input before coding.
- State what the recursion function means in one sentence ("go(i) = all ways to finish
  from index i").
- Prune early (remaining sum < 0, not enough elements left, column already used) and
  mention it - interviewers look for it.
- Ask whether the input has duplicates and whether output order matters.
- Mention the recursion limit and the iterative alternative when depth could be large.
- If you see overlapping subproblems, say "this can be memoized" - then do it.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-11-recursion -q`.
Budget: ~2 hrs tracing the templates by hand, ~5 hrs on problems.
