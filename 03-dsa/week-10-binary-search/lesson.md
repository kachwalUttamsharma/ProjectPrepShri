# Week 10: Binary Search (including on the answer)

## 1. Concept
Binary search repeatedly halves a search space. It works whenever you can test a
position and know which **side** the answer is on. Sorted array is the classic case,
but the real requirement is a **monotonic predicate**: a yes/no question whose answers
look like `F F F F T T T T`. Find the boundary.

## 2. How to recognize the pattern
- Input is sorted (or rotated sorted) and you need O(log n).
- "Find the minimum X such that ..." / "maximum X such that ..." where checking one
  candidate X is easy (usually an O(n) greedy) and feasibility is monotonic in X.
  This is **binary search on the answer** (Koko bananas, ship packages, split array).
- Peak finding: no sorting, but a local slope tells you which side holds a peak.
- Brute force is O(n) or O(n^2) and n is up to 10^5 - 10^9: think log.

## 3. Templates (memorize these two)
**A. Exact match** (`lo <= hi`, shrink by `mid +/- 1`):
```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        if nums[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
```
**B. Boundary / first True** (`lo < hi`, `hi = mid` keeps the candidate):
```python
def first_true(lo, hi, pred):      # smallest x in [lo, hi] with pred(x) True
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid): hi = mid     # mid might be the answer, keep it
        else:         lo = mid + 1 # mid is definitely too small
    return lo                      # lo == hi: the answer (ensure hi is feasible!)
```
Lower bound = `first_true(0, len(nums), lambda i: nums[i] >= target)` (hi = len means
"not found / insert at end"; adapt so you never index nums[len]).

**Largest True** (e.g. integer sqrt): use `mid = (lo + hi + 1) // 2` and
`lo = mid` / `hi = mid - 1`, otherwise `lo = mid` loops forever.

**Answer-space recipe**
1. Pick range `[lo, hi]` that surely contains the answer (e.g. `max(x)` to `sum(x)`).
2. Write `feasible(x)` (greedy, O(n)).
3. Run template B.

## 4. Complexity
- Plain search: O(log n) time, O(1) space.
- On the answer: O(cost_of_check * log(range)), e.g. O(n log(sum)).
- Python helper: `bisect.bisect_left / bisect_right` are O(log n) lower/upper bound.
  Know them, but be able to write by hand in an interview.

## 5. Common mistakes
- Infinite loop: `lo = mid` with `mid = (lo+hi)//2` (rounds down). Use the +1 variant.
- Mixing templates: `while lo <= hi` with `hi = mid` never terminates.
- Off-by-one on `hi` (`len(nums)` vs `len(nums)-1`); decide whether hi is inclusive.
- Wrong search range for answer problems (lo must be >= max single item for capacity).
- Rotated array: compare against `nums[hi]` (min) or check which half is sorted
  using `nums[lo] <= nums[mid]` (note `<=`).
- Forgetting empty input or single element.
- (Other languages) `(lo+hi)//2` overflow; in Python ints are unbounded so it is safe.

## 6. Interview tips
- State the invariant out loud: "the answer is always in [lo, hi]".
- Test on arrays of size 0, 1, 2 and on target smaller/larger than everything.
- Say "monotonic" explicitly when you binary search on the answer, and justify it.
- For duplicates, ask: first, last, or any occurrence? Use the boundary template.
- Median of two sorted arrays is the classic hard follow-up: practise the partition idea.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-10-binary-search -q`.
Budget: ~2 hrs reading and re-deriving the templates, ~5 hrs on problems.
