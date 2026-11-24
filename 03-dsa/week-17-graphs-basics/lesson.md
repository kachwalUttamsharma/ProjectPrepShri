# Week 17: Graph basics (BFS, DFS, grids, adjacency lists)

## 1. Concept
A graph is vertices (nodes) plus edges (connections). Edges can be directed or
undirected, and weighted or unweighted. Almost every "map", "network",
"dependencies", "grid", "state transitions" problem is a graph in disguise.

Representations:
- **Adjacency list**: `adj[u] = [v1, v2, ...]`. O(V + E) space. The default choice.
- **Adjacency matrix**: `m[u][v]`. O(V^2) space. Only for dense graphs / tiny V.
- **Edge list**: `[[u, v], ...]`. What interviews hand you; convert it first.
- **Implicit graph**: grid cells (neighbors = 4 or 8 directions), word ladders
  (neighbors = words one letter apart). You never build it, you compute neighbors on the fly.

Two traversals:
- **DFS** (stack / recursion): go deep first. Connectivity, components, cycle detection, flood fill.
- **BFS** (queue): level by level. **Shortest path in an unweighted graph**, minimum steps, multi-source spreading.

## 2. How to recognize the pattern
- "Connected", "reachable", "number of islands/provinces/components" -> DFS/BFS (or union-find, week 18).
- "Minimum number of steps/moves/transformations" with unit cost -> **BFS**.
- Everything spreads simultaneously (rotting oranges, fire, walls and gates) -> **multi-source BFS**.
- Grid with obstacles -> BFS/DFS with direction array.
- Need a copy of a structure with cycles -> traversal with old->new map.
- "Can water/ball reach X from Y" over many starts -> search **backwards** from the targets.

## 3. Template code
Build adjacency list:
```python
from collections import defaultdict, deque
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)        # drop this line if directed
```
Iterative DFS (safe from Python's recursion limit of ~1000):
```python
def dfs(start):
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen
```
BFS with distance (level-by-level):
```python
def bfs(start):
    seen = {start}
    q = deque([start])
    steps = 0
    while q:
        for _ in range(len(q)):          # one full level
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)          # mark when ENQUEUED
                    q.append(v)
        steps += 1
```
Grid neighbors:
```python
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
for dr, dc in DIRS:
    nr, nc = r + dr, c + dc
    if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 1 and (nr, nc) not in seen:
        ...
```
Connected components: loop over all nodes, start a traversal at each unseen node, count starts.
Multi-source BFS: push **all** sources into the queue before the loop starts.
Cloning: `clones = {node: Node(node.val)}`; create the clone when first discovered, then wire neighbors.

## 4. Complexity
- Traversal: O(V + E) time, O(V) space for seen + stack/queue.
- Grid: O(R * C) time and space (E <= 4 * V, or 8 * V).
- Word ladder: O(N * L^2) with wildcard buckets vs O(N^2 * L) pairwise comparison.

## 5. Common mistakes
- Marking visited when **dequeuing** instead of enqueuing in BFS: nodes enter the queue many times (blow-up/TLE).
- No visited set on cyclic or undirected graphs: infinite loop. In undirected graphs every edge points back.
- Flood fill when new color == old color: infinite loop. Guard it.
- Recursive DFS on a 300x300 grid or 50k-node chain: RecursionError. Use an explicit stack.
- Mutating the input grid when the caller may need it (or document it). Using a `seen` set is safer.
- Mixing up `[row][col]` with `(x, y)`.
- Diagonal adjacency when the problem says 4-directional (and vice versa; 1091 is 8-directional).
- Counting nodes vs edges for "path length" (cells on path = edges + 1).
- Forgetting disconnected components (loop over all start nodes).
- DFS does **not** give shortest paths. Use BFS for unweighted shortest paths.

## 6. Interview tips
- Clarify: directed or undirected? Duplicates / self loops? Can the graph be disconnected? Node labels 0..n-1?
- Say your representation out loud: "I'll build an adjacency list, then BFS because we need the minimum number of steps."
- Name the complexity in V and E, not just N.
- Always sketch a tiny example including a cycle and a disconnected node.
- Offer iterative DFS if recursion depth could be large; mention it proactively.
- Follow-ups at Google/Uber: bidirectional BFS (word ladder), BFS on state space (lock combinations),
  grids with keys/doors (state = position + bitmask), "what if the graph does not fit in memory".
- Tree check shortcut: connected AND exactly n - 1 edges.

## Your task
`Node` in `exercises.py` is already implemented. Fill in the functions, then run the tests from this directory with `../../.venv/bin/pytest` (see PROGRESS.md).
