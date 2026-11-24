# Week 8: Queues, deque, monotonic queue

## 1. Concept
A queue is First-In-First-Out (FIFO). **Never use `list.pop(0)`** (O(n)). Use `collections.deque`:
```python
from collections import deque
q = deque()
q.append(x)        # enqueue right, O(1)
q.popleft()        # dequeue left, O(1)
q[0], q[-1]        # peek front / back, O(1)
q.appendleft(x)    # O(1)
q.pop()            # O(1) from the right
len(q), bool(q)
```
A deque is a double-ended queue: O(1) at both ends, but indexing in the middle is O(n).
`deque(maxlen=k)` automatically drops from the opposite end when full (handy for "last k items").

## 2. How to recognize the pattern
- Process in arrival order, or "the last N events / the last k seconds" -> queue / deque.
- Shortest path or minimum steps in an unweighted graph/grid, level by level -> **BFS** with a queue.
- Simulation (round-robin, ticket lines) -> queue.
- Implement one structure with another (queue via two stacks).
- Sliding window **maximum/minimum** -> **monotonic deque**.
- DP of the form `dp[i] = x[i] + max(dp[i-k..i-1])` -> monotonic deque over the window of dp.
- Shortest subarray with sum >= K when negatives exist -> monotonic deque over prefix sums.

## 3. Templates

### BFS (level order, tracks distance)
```python
q = deque([start]); seen = {start}; steps = 0
while q:
    for _ in range(len(q)):          # one level at a time
        node = q.popleft()
        if node == goal: return steps
        for nxt in neighbors(node):
            if nxt not in seen:
                seen.add(nxt)        # mark when ENQUEUING, not when dequeuing
                q.append(nxt)
    steps += 1
```

### Monotonic deque: window maximum (store INDICES, values decreasing)
```python
dq = deque()
for i, x in enumerate(nums):
    while dq and nums[dq[-1]] <= x:   # smaller items can never be a max again
        dq.pop()
    dq.append(i)
    if dq[0] <= i - k:                # front has left the window
        dq.popleft()
    if i >= k - 1:
        out.append(nums[dq[0]])       # front is the window max
```
For a window minimum flip the comparison (increasing deque).

### Queue from two stacks (amortized O(1))
`inbox` takes pushes; when `outbox` is empty on pop/peek, move everything from `inbox` to `outbox` (this reverses order).

## 4. Complexity
Each index enters and leaves the deque at most once, so monotonic-deque algorithms are O(n) time, O(k) or O(n) space. BFS is O(V + E) (grid: O(rows*cols)).

## 5. Common mistakes
- `list.pop(0)` in a loop -> accidental O(n^2).
- Marking visited when dequeuing instead of enqueuing (duplicates in the queue, blow-up).
- Storing values instead of indices in the monotonic deque (can't tell when the front expires).
- `<` vs `<=` when popping: both work for max, but `<=` keeps the deque smaller with duplicates.
- Forgetting to expire the front before reading it.
- Not handling `k > len(nums)` or empty input.

## 6. Interview tips
- State the invariant: "the deque holds indices of candidates in decreasing value order".
- Explain why popped elements are useless: a newer, larger element outlives them.
- For BFS, say why BFS (shortest path in an unweighted graph) and what the state is.
- For queue-with-two-stacks, justify amortized O(1): each element moves at most twice.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-08-queues-deque-monotonic-queue -q` (from the repo root).
