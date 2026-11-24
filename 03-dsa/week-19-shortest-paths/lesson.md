# Week 19: Shortest paths (BFS, Dijkstra, 0-1 BFS, Bellman-Ford)

Time budget: ~7-8 hrs. Read lesson (1h), solve problems 1-5 (3h), problems 6-10 (3h), review (1h).

## 1. Concept: pick the algorithm by edge weights
| Graph                           | Algorithm            | Time              |
|---------------------------------|----------------------|-------------------|
| Unweighted (all edges cost 1)   | BFS                  | O(V + E)          |
| Weights only 0 or 1             | 0-1 BFS (deque)      | O(V + E)          |
| Non-negative weights            | Dijkstra (min-heap)  | O((V + E) log V)  |
| At most K edges / negative edges| Bellman-Ford (K rounds) | O(K * E)       |
| All pairs, tiny V (<= ~400)     | Floyd-Warshall       | O(V^3)            |

Dijkstra is greedy: the unvisited node with the smallest tentative distance is final, because
no non-negative edge can make it shorter. **Negative edges break this.**

## 2. How to recognize the pattern
- "minimum time / cost / steps / effort to get from A to B" on a graph or grid.
- Weights are not all equal -> Dijkstra. All equal -> BFS.
- "Minimize the maximum edge on the path" (effort, rising water) -> Dijkstra where the path
  cost is `max(cost_so_far, edge)` instead of a sum. Works because the cost is monotone.
- "At most K stops" -> the state is (node, stops used); plain Dijkstra on node alone is wrong.
- "Maximize a product of probabilities" -> Dijkstra with a max-heap (push negated values).
- Moves that sometimes cost 0 and sometimes 1 (remove an obstacle, change an arrow) -> 0-1 BFS.
- Word transformations / state-space puzzles -> implicit graph + BFS.

## 3. Template code
BFS on a grid (unweighted):
```python
from collections import deque
def bfs(grid, start, goal):
    q = deque([(start[0], start[1], 1)])
    seen = {start}
    while q:
        r, c, d = q.popleft()
        if (r, c) == goal:
            return d
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and (nr, nc) not in seen:
                seen.add((nr, nc)); q.append((nr, nc, d + 1))
    return -1
```
Dijkstra (lazy deletion):
```python
import heapq
def dijkstra(adj, src, n):
    dist = [float("inf")] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:          # stale entry, skip
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist
```
0-1 BFS: same as Dijkstra, but the heap is a deque: `appendleft` for cost-0 edges, `append`
for cost-1 edges, and only relax when `nd < dist[v]`.

Bellman-Ford with at most K edges (copy the array every round!):
```python
dist = [INF] * n; dist[src] = 0
for _ in range(k + 1):
    nxt = dist[:]
    for u, v, w in edges:
        if dist[u] + w < nxt[v]:
            nxt[v] = dist[u] + w
    dist = nxt
```

## 4. Complexity
- BFS O(V + E) time, O(V) space. Grid with R x C cells: O(RC).
- Dijkstra O(E log V) with a binary heap (each edge pushes at most one entry), O(V + E) space.
- 0-1 BFS O(V + E). Bellman-Ford K rounds O(K * E).
- State-space variants: multiply V by the number of extra states (e.g. stops used).

## 5. Common mistakes
- Using BFS on weighted graphs, or Dijkstra with negative weights.
- Forgetting the stale-entry check `if d > dist[u]: continue` (still correct, but slow).
- Marking a node visited when pushed instead of when popped, in Dijkstra (wrong answers).
- Bellman-Ford without a per-round copy: relaxes more than K edges in one round.
- Returning `inf` instead of -1 for unreachable (read the statement).
- Off-by-one on "stops" vs "edges": K stops means K + 1 edges.
- Grid BFS: not checking the start/end cell is blocked; 1x1 grid edge cases.
- Word ladder: building neighbours by comparing all pairs is O(N^2 L); use wildcard buckets
  (`h*t`) instead.

## 6. Interview tips
- State the graph out loud: "nodes are cells, edges cost 1, so BFS" / "weights vary, so Dijkstra".
- Mention why Dijkstra is valid (non-negative weights) before coding. Interviewers at Google
  and Uber love the follow-up "what if there are negative edges?" (Bellman-Ford; detect cycles
  with an extra round).
- Follow-ups to expect: return the actual path (keep a `parent` array), bidirectional BFS for
  word ladder, A* for a grid with a heuristic, Dijkstra on a huge implicit graph (ride/route
  planning at Uber is a classic framing).
- Know `heapq` tuple ordering: ties compare the next tuple element, so keep it comparable.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-19-shortest-paths`.
