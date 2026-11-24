# Week 23: Greedy algorithms + bit manipulation

## Part A: Greedy

### 1. Concept
A greedy algorithm makes the locally best choice at each step and never
reconsiders. It works only when the problem has:
- **Greedy-choice property**: some optimal solution contains the locally best choice.
- **Optimal substructure**: what remains after the choice is a smaller instance of the same problem.

### 2. Recognising greedy
- "Minimum number of X to cover/remove/schedule", intervals, jumps, tasks.
- Sorting by one key makes the answer fall out (end time, deadline, ratio).
- A DP exists but the table only ever looks at the best neighbour -> collapse to greedy.
- Counter-example search fails after 5 minutes of trying small cases.

### 3. Proving it (what Google interviewers probe)
Use an **exchange argument**: take any optimal solution; swap its first choice
for the greedy choice; show it is no worse. Or a **stays-ahead** argument:
after k steps greedy is at least as far as any other strategy.
Even a 2-sentence justification earns credit. Always test on a tricky small case.

### 4. Templates
Interval scheduling (max non-overlapping = sort by END):
```python
intervals.sort(key=lambda x: x[1])
end = float("-inf"); kept = 0
for s, e in intervals:
    if s >= end:
        kept += 1; end = e
```
Farthest reach (jump game):
```python
far = 0
for i, x in enumerate(nums):
    if i > far: return False
    far = max(far, i + x)
```
BFS-levels jump (min jumps): track `end` of current level and `far`; when `i == end`, jumps += 1, end = far.
Running total reset (gas station): if the prefix balance goes negative, no start up to here works; restart after it.
Last-occurrence extension (partition labels): precompute last index, extend the current part's end.

### 5. Complexity
Usually O(n) after an O(n log n) sort; O(1) extra space.

### 6. Common mistakes
- Sorting by the wrong key (start vs end for scheduling).
- Greedy where it fails: coin change with arbitrary coins, 0/1 knapsack, longest path. Know a counter-example: coins {1,3,4}, amount 6 -> greedy 4+1+1, optimum 3+3.
- Touching intervals: decide `<` vs `<=` explicitly.
- Skipping the empty-input / single-element cases.

## Part B: Bit manipulation

### 1. Core facts
```python
x & 1            # lowest bit (odd/even)
x >> k & 1       # k-th bit
x | (1 << k)     # set bit k
x & ~(1 << k)    # clear bit k
x ^ (1 << k)     # toggle bit k
x & (x - 1)      # clear lowest set bit (Kernighan)
x & -x           # isolate lowest set bit
a ^ a == 0; a ^ 0 == a; XOR is commutative/associative
```
Powers of two have exactly one set bit: `x > 0 and x & (x-1) == 0`.

### 2. Python specifics
- Ints are arbitrary precision; negatives behave as infinite two's complement. For 32-bit emulation mask with `& 0xFFFFFFFF`.
- `bin(x).count("1")` and `int.bit_count()` exist; interviewers still want you to know Kernighan.
- `~x == -x - 1`. Operator precedence: `&`, `^`, `|` bind LOWER than `==`. Always parenthesise: `(x & 1) == 0`.

### 3. Patterns
- XOR cancellation: single number, missing number, find the duplicate pairs.
- Bitmask as a set: subsets of n <= ~20 items via `for mask in range(1 << n)`; DP over masks (TSP-like) at n <= 20.
- Counting bits, parity, swapping without temp, fast power of two checks.

### 4. Complexity
Most are O(1) or O(bits) or O(n) with O(1) extra space, which is the usual follow-up ("do it without a hash set").

### 5. Common mistakes
- Missing parentheses around bit ops in comparisons.
- Assuming 32-bit overflow in Python.
- Right-shifting negatives (arithmetic shift in Python: sign preserved, loops forever with `while n:`).
- Off-by-one on bit indices (0-based from LSB).

## Interview tips
- Greedy: state the greedy rule, give a one-line justification, then try to break it with a small example before coding.
- If unsure greedy is valid, say "I'd verify with DP / brute force on small inputs" and offer the DP.
- Bits: say the O(1) space angle; mention hash-set / sum alternatives first, then the XOR trick.

## Your task
Fill in `exercises.py` (10 problems), then run
`/Users/uttam.sharma/Desktop/python/.venv/bin/pytest -q` from this folder.
Tests include brute-force cross-checks, so a wrong greedy rule will be caught.
