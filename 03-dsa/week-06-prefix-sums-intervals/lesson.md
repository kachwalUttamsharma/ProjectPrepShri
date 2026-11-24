# Week 6: Prefix sums and intervals

## Part A: Prefix sums

### 1. The idea
Pay O(n) once to precompute `prefix[i] = nums[0] + ... + nums[i-1]` (with `prefix[0] = 0`).
Then any range sum is O(1):
```
sum(nums[l..r]) = prefix[r + 1] - prefix[l]
```
The leading 0 removes the "if l == 0" special case. Always use length n + 1.

```python
from itertools import accumulate
prefix = [0, *accumulate(nums)]
```

### 2. Recognise it
- Many range-sum queries on a static array.
- "Number of / longest subarray with sum = k" where values can be **negative** (sliding window
  fails, because extending the window does not move the sum in one direction).
- "Everything except me" (product / sum of others) and "balance point" problems.
- Equal counts of two things (map 0 -> -1, then look for sum 0).

### 3. Prefix sum + hash map (the key interview pattern)
`sum(i..j) == k`  <=>  `prefix[j+1] - prefix[i] == k`  <=>  `prefix[i] == prefix[j+1] - k`.
While scanning, keep a dict of how often each prefix value has appeared:
```python
def count_subarrays(nums, k):
    seen = {0: 1}           # empty prefix, forgetting this loses subarrays starting at index 0
    cur = count = 0
    for x in nums:
        cur += x
        count += seen.get(cur - k, 0)   # look up BEFORE inserting cur
        seen[cur] = seen.get(cur, 0) + 1
    return count
```
For the LONGEST such subarray store the FIRST index of each prefix instead of a count.

### 4. Other variants
- **Prefix/suffix products** (`product_except_self`): result[i] = prefix_product[i] * suffix_product[i+1].
  No division, so zeros are fine.
- **Difference array** (`range_addition`): to add `inc` to `[s, e]` do `diff[s] += inc;
  diff[e+1] -= inc`; one prefix sum at the end applies all updates. O(n + q) instead of O(n*q).
  Inverse of prefix sum: prefix sum of the difference array gives the original.
- **2D prefix sums**: `P[i][j]` sum of the rectangle from the origin; query by
  inclusion-exclusion (4 lookups). Same idea.

## Part B: Intervals

### 5. Core move: SORT first
Nearly every interval problem becomes a single sweep after sorting. Decide what to sort by:
- **Sort by start** for merging, inserting, rooms: you look at the previous result's end.
- **Sort by end** for the greedy "keep as many non-overlapping as possible"
  (`erase_overlap_intervals`): finishing earliest leaves the most room. Sorting by start here
  is a classic wrong answer.

Two intervals `[a, b]`, `[c, d]` overlap iff `max(a, c) <= min(b, d)` (closed intervals). For
half-open `[a, b)` use `<`. Ask the interviewer whether touching endpoints count as overlap.

### 6. Templates
```python
def merge(intervals):
    res = []
    for s, e in sorted(intervals):
        if res and s <= res[-1][1]:
            res[-1][1] = max(res[-1][1], e)   # max: the new one may be contained
        else:
            res.append([s, e])
    return res
```
Meeting rooms (count concurrent): sweep with sorted starts and sorted ends, or a min-heap of end
times (`heapq`; pop the earliest end if it is <= the new start).
Intersection of two sorted lists: two pointers, `lo = max(starts)`, `hi = min(ends)`; advance
the pointer whose interval ends first.

### 7. Complexity
| Technique | Time | Space |
|---|---|---|
| Build prefix / query | O(n) / O(1) | O(n) |
| Prefix + hash map count | O(n) | O(n) |
| Difference array | O(n + q) | O(n) |
| Sort + sweep intervals | O(n log n) | O(n) |
| Two sorted interval lists | O(m + n) | O(1) extra |

### 8. Common mistakes
- Off-by-one with the prefix array: it has n + 1 entries, query is `prefix[r+1] - prefix[l]`.
- Forgetting `{0: 1}` in the hash-map version, or inserting the current prefix BEFORE looking
  up (counts the empty subarray when k = 0).
- Using a sliding window for sums with negatives.
- Merge: writing `res[-1][1] = e` instead of `max(...)` when the new interval is contained.
- Mutating the input intervals while merging (copy if the caller reuses them).
- Wrong sort key for the greedy removal problem.
- Treating touching intervals inconsistently across problems; read the statement.

### 9. Interview tips
- Say "I will precompute prefix sums so each query is O(1)" and mention extra O(n) memory.
- For subarray-sum counting, explain the identity prefix[j] - prefix[i] = k out loud.
- Updates + queries interleaved? Prefix sums are static: mention Fenwick tree / segment tree
  as the follow-up (point update O(log n)).
- For intervals, draw them on a number line; list edge cases: empty, one interval, fully
  nested, identical, touching, unsorted input.

## Your task
Fill in `exercises.py`, then run `pytest -q` in this folder. ~2 hrs on the templates (derive the
prefix-sum identities by hand), ~5 hrs on problems.
