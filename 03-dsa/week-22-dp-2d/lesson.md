# Week 22: 2-D dynamic programming (grids, strings, knapsack)

## 1. Concept
Week 21 used a 1-D state (`dp[i]`). Many problems need TWO independent
parameters to describe a subproblem:
- grid position `(r, c)`
- prefix lengths `(i, j)` of two strings
- `(item index, remaining capacity)`
- interval `(left, right)` of one string

`dp[a][b]` = answer to the subproblem described by `(a, b)`. You fill a table
where each cell depends on a few neighbours already computed.

## 2. How to recognise it
- Two sequences compared/aligned (LCS, edit distance, interleaving) -> `dp[i][j]` over prefixes.
- Grid with moves restricted to right/down, counting or optimising paths.
- "Pick items, each at most once, under a budget" -> 0/1 knapsack (subset sum, partition).
- "Unlimited items, count ways" -> unbounded knapsack / coin change II.
- Palindromic substring/subsequence questions -> interval DP `dp[i][j]` or reduce to LCS.
- Brute force is exponential but the number of DISTINCT states is polynomial.

## 3. The 5-step recipe (say this out loud in interviews)
1. State: what does `dp[i][j]` mean? (one precise sentence)
2. Transition: how does it depend on smaller states?
3. Base cases: empty prefix, first row/column, capacity 0.
4. Order: which direction guarantees dependencies are ready?
5. Answer: which cell? Then optimise space if asked.

## 4. Templates
Grid:
```python
def grid_dp(grid):
    m, n = len(grid), len(grid[0])
    dp = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            if r == 0 and c == 0:
                dp[r][c] = grid[r][c]
            else:
                up = dp[r-1][c] if r else INF
                left = dp[r][c-1] if c else INF
                dp[r][c] = grid[r][c] + min(up, left)
    return dp[-1][-1]
```
Two strings (LCS):
```python
dp = [[0] * (n + 1) for _ in range(m + 1)]   # +1: empty prefix row/col
for i in range(1, m + 1):
    for j in range(1, n + 1):
        if a[i-1] == b[j-1]:
            dp[i][j] = dp[i-1][j-1] + 1
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```
0/1 knapsack, 1-D space (capacity DOWNWARD):
```python
dp = [0] * (cap + 1)
for w, v in items:
    for c in range(cap, w - 1, -1):
        dp[c] = max(dp[c], dp[c - w] + v)
```
Unbounded / combinations: iterate coins outer, amount ascending inner.
(Swap the loops and you count permutations instead.)

## 5. Complexity
- Grid: O(m*n) time; O(n) space with a rolling row.
- Two strings: O(m*n) time; O(min(m,n)) space if you only need the length (not the reconstruction).
- Knapsack: O(items * capacity), pseudo-polynomial (capacity is a VALUE, not input size).
- Interval DP: O(n^2) states, O(n) transition -> O(n^3) in general.

## 6. Common mistakes
- Off-by-one between `dp[i]` (prefix length i) and `s[i-1]` (the character).
- Forgetting the extra row/column for the empty prefix.
- 0/1 knapsack iterating capacity upward -> item reused (becomes unbounded).
- Coin change II with loops swapped -> counts permutations.
- Rolling-array overwrites a value you still need (e.g. diagonal in maximal square / edit distance: save `prev` diagonal or use two rows).
- Forgetting blocked start/end in obstacle grids.
- Mutating the input grid when not allowed.
- Using a float `inf` and returning it for impossible cases.

## 7. Interview tips
- Start with the recursive brute force + memo (`functools.cache`), then convert to bottom-up. Interviewers like seeing the derivation.
- State the meaning of `dp[i][j]` before coding. Most bugs are a fuzzy state definition.
- Reconstruction (print the LCS / the path) = walk back through the table choosing the branch that produced each cell. Know how.
- Follow-ups: space optimisation, reconstruct answer, what if inputs are huge (Hirschberg is overkill; mention it).
- Edit distance, LCS, knapsack, coin change are asked at Google/Uber in disguise (diff tools, autocomplete, resource allocation).

## Your task
Fill in `exercises.py` (10 problems, easy -> hard), then:
`/Users/uttam.sharma/Desktop/python/.venv/bin/pytest -q` from this folder.
Budget: ~8 hours. Do 1 of the DP derivations on paper before coding each.
