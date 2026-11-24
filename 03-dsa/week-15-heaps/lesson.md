# Week 15: Heaps / priority queues (heapq, top-K)

## 1. Concept
A heap is a complete binary tree stored in an array where each parent is <= its children (min-heap).
The smallest element is always at index 0. You get:
- peek min: O(1)
- push / pop min: O(log n)
- heapify an existing list: O(n)
It is *not* sorted - only the root is guaranteed. Use it when you repeatedly need "the current best".

Python's `heapq` is a **min-heap** on a plain list:
```python
import heapq
h = []
heapq.heappush(h, 5); heapq.heappush(h, 1)
heapq.heappop(h)            # 1
heapq.heapify(lst)          # in place, O(n)
heapq.heapreplace(h, x)     # pop then push, one step (fast)
heapq.heappushpop(h, x)     # push then pop
heapq.nlargest(k, it, key=f); heapq.nsmallest(k, it)
```
Max-heap: push `-x`. Tuples compare lexicographically: `(priority, tiebreak, payload)`.

## 2. How to recognize the pattern
- "k largest / smallest / most frequent / closest" -> size-k heap.
- "Merge k sorted ..." -> heap of the k current heads.
- "Running median / stream" -> two heaps.
- "Always process the most/least X next" (scheduling, smashing stones, Dijkstra next week) -> priority queue.
- "Rearrange so no two equal adjacent" -> greedy with a max-heap.

## 3. Templates

### Top-K largest with a min-heap of size k (O(n log k))
```python
h = []
for x in nums:
    if len(h) < k: heapq.heappush(h, x)
    elif x > h[0]: heapq.heapreplace(h, x)
# h[0] is the k-th largest; h holds the k largest
```
Rule of thumb: for the k LARGEST keep a MIN-heap; for the k SMALLEST keep a MAX-heap (negated).

### Merge k sorted lists
```python
h = [(node.val, i, node) for i, node in enumerate(lists) if node]
heapq.heapify(h)
while h:
    _, i, node = heapq.heappop(h)
    tail.next = node; tail = node
    if node.next: heapq.heappush(h, (node.next.val, i, node.next))
```
The index `i` prevents Python from comparing `ListNode`s on ties (TypeError).

### Two heaps for the median
```python
lo = []   # max-heap (negated): lower half
hi = []   # min-heap: upper half
def add(x):
    heapq.heappush(lo, -x)
    heapq.heappush(hi, -heapq.heappop(lo))
    if len(hi) > len(lo): heapq.heappush(lo, -heapq.heappop(hi))
def median():
    return -lo[0] if len(lo) > len(hi) else (-lo[0] + hi[0]) / 2
```

### "Frontier expansion" (k smallest pairs, k-th in a sorted matrix)
Seed the heap with the first column/row, pop the min, push its successor. Total work O(k log k).

### Lazy deletion
Heaps cannot remove arbitrary items. Mark items as removed (a set / counter) and skip them when they surface at the top.

## 4. Complexity
- build heap O(n); push/pop O(log n); top-K over n items O(n log k) time, O(k) space.
- Beats sorting (O(n log n)) when k << n, and works on streams.
- Quickselect gives expected O(n) for a one-off k-th element, but a heap handles streams.
- Two-heap median: O(log n) add, O(1) query.

## 5. Common mistakes
- Using `heapq` as a max-heap without negating (or negating once and forgetting to negate back).
- Wrong heap type for top-K: min-heap for largest, max-heap for smallest.
- Pushing tuples whose second element is not comparable (nodes, dicts) with tied priorities -> TypeError. Add an index.
- Calling `sorted(h)` or indexing `h[1]` as "second smallest": only `h[0]` is meaningful.
- Pushing all n items then popping k (O(n log n) and O(n) memory) when O(n log k) was expected.
- Median heaps: forgetting to rebalance, or an off-by-one when sizes differ.
- Reorganize string / task scheduler: not holding the just-used item out for the cooldown.

## 6. Interview tips
- Name the trade-off aloud: "sort is O(n log n), heap of size k is O(n log k), quickselect is O(n) average".
- Ask whether the data is a stream or fits in memory; this picks heap vs quickselect.
- For "merge k", mention divide-and-conquer pairwise merge as an equal-complexity, O(1)-space alternative.
- Know the task-scheduler formula AND the heap simulation; interviewers like both.
- Expect follow-ups: sliding window median (two heaps + lazy deletion), IPO, meeting rooms II, find K pairs, smallest range covering k lists.

## Your task
Fill in `exercises.py` (10 problems), then run `cd 03-dsa/week-15-heaps && ../../.venv/bin/pytest -q`.
