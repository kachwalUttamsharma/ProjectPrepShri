# Week 18: Topological sort and Union-Find

## 1. Concepts

### Topological sort
A **topological order** of a directed graph lists every node so that for each edge
`u -> v`, `u` comes before `v`. It exists **iff the graph is a DAG** (no directed cycle).
Typical story: tasks with prerequisites, build order, course schedules, symbol
dependencies, "order of letters" from sorted data.

Two algorithms:
- **Kahn's (BFS)**: repeatedly remove nodes with in-degree 0. If fewer than V nodes
  are removed, there is a cycle. Easy to extend to "levels" (parallel semesters) and
  longest-chain questions.
- **DFS post-order**: with 3 colors (unvisited / visiting / done). Reverse post-order is a
  topological order; reaching a "visiting" node = cycle.

### Union-Find (Disjoint Set Union, DSU)
Maintains a partition of elements into sets under two operations:
- `find(x)`: which set is x in (its representative root)?
- `union(a, b)`: merge the two sets.
With **path compression** + **union by size/rank** both run in amortized
O(alpha(n)) (practically constant). Ideal for **dynamic connectivity** on
**undirected** graphs where edges only get added: components, cycle detection while
adding edges, Kruskal's MST, merging accounts.

## 2. How to recognize the pattern
Topological sort:
- "Prerequisites", "dependencies", "order of tasks/courses/characters", "build order".
- "Is there a cycle in a directed graph?"
- "Minimum number of rounds/semesters" = longest path in a DAG = Kahn's levels.
- Order inferred from sorted data (alien dictionary): derive edges from adjacent items.
- Tree centers / "peel the leaves" (MHT) is the same in-degree-peeling idea on an undirected tree.

Union-Find:
- "Connected components", "provinces", "same group", "merge groups sharing something".
- Edges arrive one by one and you must detect the first that creates a cycle (redundant connection).
- Grouping by shared key (emails, accounts, equivalences like `a == b`).
- You only need connectivity, not paths. (Need the path itself? Use BFS/DFS.)
- Does NOT handle edge deletion or directed reachability.

## 3. Template code
Kahn's algorithm:
```python
from collections import defaultdict, deque

def topo_order(n, edges):              # edge (a, b): a must come before b
    adj = defaultdict(list)
    indeg = [0] * n
    for a, b in edges:
        adj[a].append(b)
        indeg[b] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == n else []     # [] means a cycle
```
Level-by-level (count semesters): wrap the pop in `for _ in range(len(q))` and count levels.

DFS with 3 states:
```python
def has_cycle(n, adj):
    state = [0] * n                     # 0 new, 1 visiting, 2 done
    def dfs(u):
        state[u] = 1
        for v in adj[u]:
            if state[v] == 1 or (state[v] == 0 and dfs(v)):
                return True
        state[u] = 2
        return False
    return any(state[i] == 0 and dfs(i) for i in range(n))
```
Union-Find:
```python
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True
```
For non-integer keys (emails, strings), either map them to ids or use dicts for `parent`.

## 4. Complexity
- Topological sort (either): O(V + E) time, O(V + E) space.
- Union-Find: O(alpha(n)) amortized per op; building from E edges is O(E * alpha(n)).
- Accounts merge: O(E log E) from sorting the emails.
- Leaf peeling for MHT: O(V).

## 5. Common mistakes
- **Edge direction** flipped: `[a, b]` = "take b before a" means edge `b -> a`. Write it on the board before coding.
- Forgetting nodes with no edges (they still belong in the order / in letters of alien dictionary).
- Not detecting the cycle: always compare `len(order)` against the number of nodes.
- Alien dictionary: forgetting the invalid-prefix case (`["abc", "ab"]`), adding duplicate edges
  (inflates in-degree), or comparing non-adjacent words.
- Union-Find without compression / union by size: O(n) finds, TLE on chains. Recursive `find` hits the recursion limit.
- Calling `parent[x]` instead of `find(x)` when counting groups (stale roots).
- Counting components as `len(set(parent))`: only correct after finding every root.
- Using Union-Find on a **directed** cycle question: DSU only sees undirected connectivity.
- Merging accounts by **name**: different people share names; merge by email.

## 6. Interview tips
- Phrase it: "This is a dependency problem, so I'll build a directed graph and run Kahn's algorithm. If I can't process every node there is a cycle."
- Ask: can there be duplicate edges, self loops, isolated nodes? Does any valid order work or must it be unique/lexicographically smallest (then use a heap instead of a deque)?
- Know both Kahn and DFS and which to pick: Kahn for levels, shortest/longest chains; DFS when you already recurse.
- For DSU say "path compression plus union by size gives near-constant time" and implement `find` iteratively.
- Follow-ups: Kruskal's MST with DSU, "number of islands II" (add land online, DSU), DSU with weights (division evaluation),
  detecting a cycle in directed vs undirected graphs, checking whether a topological order is unique (queue size is always 1).

## Your task
Fill in `exercises.py`, then run the tests from this directory with `../../.venv/bin/pytest` (see PROGRESS.md).
