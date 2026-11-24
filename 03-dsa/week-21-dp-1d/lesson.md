# Week 21: 1-D Dynamic Programming

Time budget: ~7-8 hrs. Lesson (1h), problems 1-5 (3h), problems 6-10 (3h), review (1h).

## 1. Concept
DP = recursion with **overlapping subproblems** + **optimal substructure**, where you store
each subproblem's answer so it is computed once. Two equivalent styles:
- **Top-down (memoization):** write the recursion, cache with `functools.cache`.
- **Bottom-up (tabulation):** fill `dp[0..n]` in dependency order; often compressible to O(1) space.

A 5-step recipe that works in interviews:
1. **State:** what does `dp[i]` mean? Write it in one English sentence.
2. **Transition:** express `dp[i]` through smaller states.
3. **Base cases:** `dp[0]` (and `dp[1]`).
4. **Order:** which direction fills the table so dependencies are ready.
5. **Answer:** `dp[n]`, or `max(dp)` if the state is "ending at i".

## 2. How to recognize the pattern
- "Number of ways to ...", "minimum cost / coins / steps to reach ...", "longest ...",
  "can you form ...?" over a **sequence or a number line**.
- A brute-force recursion branches 2+ ways at each step and revisits the same arguments.
- Greedy fails on a small counterexample (coins [1,3,4], amount 6).
- Typical 1-D families:
  | Family | Transition | Problems |
  |---|---|---|
  | Fibonacci-like | `dp[i] = dp[i-1] + dp[i-2]` | climb stairs, decode ways |
  | Take-or-skip | `dp[i] = max(dp[i-1], dp[i-2] + x)` | house robber |
  | Best ending at i | `dp[i] = max(x, dp[i-1] + x)` | Kadane, max product |
  | Unbounded knapsack on amount | `dp[a] = min(dp[a-c] + 1)` | coin change |
  | Prefix feasibility | `dp[i] = any(dp[j] and s[j:i] in set)` | word break |
  | Subsequence | `dp[i] = 1 + max(dp[j])` for `j < i`, `a[j] < a[i]` | LIS |

## 3. Template code
```python
from functools import cache

# top-down
def f(n):
    @cache
    def go(i):
        if i <= 1:
            return 1
        return go(i - 1) + go(i - 2)
    return go(n)

# bottom-up with O(1) space
def climb(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b

# unbounded knapsack / coin change (min coins)
def coin_change(coins, amount):
    INF = float("inf")
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return -1 if dp[amount] == INF else dp[amount]
```
O(n log n) LIS: keep `tails`, where `tails[k]` is the smallest tail of an increasing
subsequence of length `k + 1`; use `bisect_left`.

## 4. Complexity
- Time = (#states) x (work per transition). Climb/rob/Kadane: O(n). Coin change: O(amount * #coins).
- Word break: O(n^2) substring checks (O(n^2 * L) with hashing cost). LIS: O(n^2) or O(n log n).
- Space: O(n), compressible to O(1) when `dp[i]` only needs the previous 1-2 states.

## 5. Common mistakes
- Not defining the state precisely (is `dp[i]` "using first i items" or "ending at item i"?).
- Wrong loop order for **coin change counting**: coins in the outer loop counts combinations;
  amount in the outer loop counts permutations.
- Kadane for max product needs both a running **max and min** (negatives flip signs).
- Circular house robber: run the linear solution twice (exclude first / exclude last) and
  handle `n == 1` separately.
- Decode ways: '0' can only be part of "10" or "20"; "06" is invalid.
- `dp = [[0]] * n` style aliasing bugs; use list comprehensions.
- Mixing up the `-1` sentinel and `inf` in min problems.
- LIS: `bisect_left` for strictly increasing, `bisect_right` for non-decreasing.

## 6. Interview tips
- Start with the brute-force recursion, point at the repeated subproblems, add `@cache`,
  then offer bottom-up and the space optimization. This shows the full thought process.
- Always state the DP meaning in words before writing code.
- Check small cases (n = 0, 1, 2) aloud; most bugs live in the base cases.
- Follow-ups: "return the actual solution" (keep parent pointers or reconstruct backwards),
  "reduce space", "what if the numbers are huge" (then DP over the amount is too slow).

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-21-dp-1d`.
