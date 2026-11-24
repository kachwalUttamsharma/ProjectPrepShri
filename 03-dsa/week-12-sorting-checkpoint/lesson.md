# Week 12: Sorting + Checkpoint Review

## 1. Concept
Sorting is both a tool (it often turns an O(n^2) problem into O(n log n): intervals,
two pointers, greedy, grouping) and a topic (implement merge sort / quick sort).

| Algorithm | Time (avg / worst) | Space | Stable | Notes |
|---|---|---|---|---|
| Merge sort | n log n / n log n | O(n) | yes | divide, sort halves, merge; counts inversions |
| Quick sort | n log n / n^2 | O(log n) | no | random pivot + 3-way partition handles duplicates |
| Heap sort | n log n / n log n | O(1) | no | via heapq or in-place heap |
| Insertion sort | n^2 / n^2 | O(1) | yes | fast on tiny / nearly sorted input |
| Counting sort | n + k | O(k) | yes | small integer range (sort colors) |
| Python `sorted` | n log n | O(n) | yes | Timsort; O(n) on already sorted data |

## 2. How to recognize the pattern
- "Merge overlapping intervals", "minimum rooms/arrows", "schedule" -> sort by start (or end).
- "Largest number / arrange to maximize" -> custom comparator.
- "Top k", "k-th largest" -> sort, heap (O(n log k)), or quickselect (O(n) avg).
- "Count pairs out of order" -> merge sort with a counter.
- Only a few distinct values (0/1/2) -> counting / Dutch flag, O(n) one pass.

## 3. Template code
**Merge sort**
```python
def merge_sort(a):
    if len(a) <= 1: return a
    m = len(a) // 2
    l, r = merge_sort(a[:m]), merge_sort(a[m:])
    out, i, j = [], 0, 0
    while i < len(l) and j < len(r):
        if r[j] < l[i]: out.append(r[j]); j += 1   # strict < keeps stability
        else:           out.append(l[i]); i += 1
    return out + l[i:] + r[j:]
```
**Quick sort (3-way, random pivot)**
```python
def quick_sort(a):
    if len(a) <= 1: return a
    p = random.choice(a)
    return (quick_sort([x for x in a if x < p]) + [x for x in a if x == p]
            + quick_sort([x for x in a if x > p]))
```
**Custom keys**
```python
sorted(items, key=lambda s: (-s.grade, s.age, s.name))   # mixed asc/desc via negation
sorted(strs, key=cmp_to_key(lambda a, b: -1 if a+b > b+a else 1 if a+b < b+a else 0))
items.sort(key=..., reverse=True)                        # in place, returns None
```
Because Timsort is stable you can also sort in several passes: least significant key first.

**Dutch national flag** (three-way in place): `lo`, `mid`, `hi`; swap 0s to the front,
2s to the back, advance `mid` only when you did not swap with `hi`.

## 4. Complexity
Comparison sorts cannot beat O(n log n). `sorted` returns a new list (O(n) space),
`list.sort` is in place (O(1)-O(n) aux). Sorting dominates many solutions, so say
"O(n log n) for the sort + O(n) scan".

## 5. Common mistakes
- `list.sort()` returns None (`x = a.sort()` is a bug).
- Quick sort with first/last pivot on sorted data: O(n^2) and RecursionError. Randomise.
- Quick sort with `<=` / `>=` only (2-way): all-equal input degenerates to O(n^2).
- Merge sort merge step that uses `<=` on the wrong side loses stability.
- Mutating the input when the problem wants a new list (or vice versa).
- Intervals: forgetting `max(end, ...)` when merging, or `<` vs `<=` for touching ends.
- Comparator mistakes: key functions cannot mix asc/desc on strings (use cmp_to_key
  or sort twice).
- Dutch flag: incrementing `mid` after swapping with `hi`.

## 6. Interview tips
- Ask: stable? in place? input size / range? duplicates? That picks the algorithm.
- Be able to write merge sort and quickselect from memory in under 10 minutes.
- Mention the built-in first ("I'd call sorted; here's how it works if you want it by hand").
- Say Timsort when asked about Python: stable, O(n log n) worst, O(n) on sorted runs.

## 7. Checkpoint review and mock set (Part B of exercises.py)
Problems 11-15 re-test earlier weeks: sliding window (5), monotonic stack (7),
prefix sums + hash map (3/6), linked list (9), intervals + sort (6/12).

Suggested checkpoint routine for the week:
1. Day 1-2 (~3 hrs): concept + Part A problems 1-5.
2. Day 3-4 (~2 hrs): Part A problems 6-10.
3. Day 5-6 (~2 hrs): mock Part B. Run 2 problems per 45-minute timer, no hints. Talk
   through brute force -> optimized -> complexity -> edge cases like a real interview.
4. Day 7: review. For every problem you needed a hint on, re-solve it from scratch
   tomorrow and again in a week. List weak topics (arrays? pointers? recursion?) and
   re-read that week's lesson.md.

Self-assessment questions before moving to trees (week 13):
- Can I state the invariant of binary search and write both templates?
- Can I draw the decision tree for a backtracking problem and spot the prune?
- Can I pick between hash map, sorting, two pointers, and sliding window for a new array
  problem within two minutes?
- Do I know the costs of list / dict / set / deque operations?

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-12-sorting-checkpoint -q`.
