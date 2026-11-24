# Week 20: Backtracking

Time budget: ~7-8 hrs. Lesson (1h), problems 1-5 (3h), problems 6-10 (3h), review (1h).

## 1. Concept
Backtracking = DFS over a **decision tree** of partial solutions. At each step you
**choose** an option, **explore** recursively, then **un-choose** (undo) to try the next option.
You **prune** a branch as soon as it cannot lead to a valid answer.

Think of three questions for every problem:
1. What is a *state*? (the path built so far + where I am in the input)
2. What are the *choices* at this state?
3. When is the state a complete answer (*base case*), and when can I stop early (*pruning*)?

## 2. How to recognize the pattern
- "Return **all** subsets / permutations / combinations / partitions / valid configurations."
- "Does **any** arrangement exist?" with small constraints (n <= ~20, board <= ~9x9).
- Constraints that are tiny (n <= 15) signal exponential time is expected.
- Words: "generate", "enumerate", "all possible", "place N things such that".
If it asks for a *count or an optimum* and subproblems overlap, think DP instead (weeks 21-22).

## 3. Template code
```python
def solve(nums):
    res, path = [], []
    def dfs(start):
        res.append(path[:])              # record (copy!) when each node is a solution
        for i in range(start, len(nums)):
            path.append(nums[i])         # choose
            dfs(i + 1)                   # explore
            path.pop()                   # un-choose
    dfs(0)
    return res
```
Variants (memorize the differences):
| Problem | Loop over | Recurse with | Notes |
|---|---|---|---|
| Subsets | `i in range(start, n)` | `i + 1` | record at every node |
| Combinations (size k) | same | `i + 1` | record when `len(path) == k`; prune if not enough left |
| Combination sum (reuse) | same | `i` | prune when remaining < 0; sort to break early |
| Permutations | all unused indices | -- | `used[]` array, record when `len == n` |
| With duplicates | sort first | -- | `if i > start and nums[i] == nums[i-1]: continue` |
| Grid search (word search) | 4 neighbours | -- | mark visited in place, restore after |
| N-Queens | columns in this row | `row + 1` | sets for cols / diagonals (`r-c`, `r+c`) |

## 4. Complexity
Count the leaves of the decision tree times the work to copy an answer:
- Subsets: O(n * 2^n). Permutations: O(n * n!). Combinations C(n,k): O(k * C(n,k)).
- Parentheses: O(Catalan(n) * n) ~ O(4^n / sqrt(n)). N-Queens: roughly O(n!) with pruning.
- Word search: O(R*C * 3^L). Space: O(depth) recursion plus output.
Always state "output-sensitive": you can't beat the size of the output.

## 5. Common mistakes
- `res.append(path)` instead of `res.append(path[:])` -> all results alias one list.
- Forgetting to undo (`pop`, `visited = False`, board restore).
- Duplicates: skipping with `used[i-1]` logic wrong, or forgetting to sort first.
- Using `start` for permutations (that gives combinations) or no `start` for subsets (repeats).
- Pruning too late: check constraints *before* recursing, not at the leaf.
- Strings: building with `+` is fine for short strings; for deep paths use a list and `join`.
- Python recursion limit (1000) is not a concern for these depths, but know it.

## 6. Interview tips
- Draw the decision tree for a tiny input (n = 3) before coding; interviewers love this.
- Say the complexity as "number of leaves x cost per leaf".
- Mention pruning optimizations (sorting + break, early `False`, sets for O(1) conflict checks).
- Be ready for the follow-up "now with duplicates" and "count only, don't list" (-> DP/math).
- Prefer a nested `dfs` with closures over many parameters; but pass indices explicitly.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-20-backtracking`.
Tests compare results as sorted lists, so order of your output does not matter.
