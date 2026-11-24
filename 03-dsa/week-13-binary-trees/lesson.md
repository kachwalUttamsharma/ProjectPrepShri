# Week 13: Binary trees and traversals (DFS / BFS)

## 1. Concept
A binary tree is a node with up to two children (`left`, `right`). Almost every tree problem is
"visit every node once" (O(n)) while carrying some information up or down.
```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right
```
Vocabulary: root, leaf, height (edges or nodes - ASK which), depth, subtree, balanced, complete, full.

## 2. How to recognize the pattern
- "For every node ..." / "any path ..." / "depth/height/diameter" -> recursive DFS that **returns** a value.
- "Level by level", "shortest", "right side view", "zigzag" -> BFS with a queue.
- Input is two traversals -> reconstruct using the root position in one of them.
- "Ancestor", "path from root" -> DFS carrying state **down** (parameters).
- "Best path through a node" -> DFS returning one thing up while updating a global answer with another.

## 3. Templates

### Recursive DFS (return value up)
```python
def solve(node):
    if node is None:
        return BASE
    left = solve(node.left)
    right = solve(node.right)
    return combine(node.val, left, right)
```

### Traversal orders
```python
def pre(n):  return [] if not n else [n.val] + pre(n.left) + pre(n.right)   # node, L, R
def ino(n):  return [] if not n else ino(n.left) + [n.val] + ino(n.right)   # L, node, R
def post(n): return [] if not n else post(n.left) + post(n.right) + [n.val] # L, R, node
```

### Iterative inorder (explicit stack)
```python
out, stack, cur = [], [], root
while cur or stack:
    while cur:
        stack.append(cur); cur = cur.left
    cur = stack.pop()
    out.append(cur.val)
    cur = cur.right
```

### BFS by level
```python
from collections import deque
q = deque([root]) if root else deque()
while q:
    for _ in range(len(q)):       # freeze the level size
        node = q.popleft()
        ...
        if node.left:  q.append(node.left)
        if node.right: q.append(node.right)
```

### "Return one thing, record another" (diameter, max path sum)
```python
best = 0
def height(n):
    nonlocal best
    if not n: return 0
    l, r = height(n.left), height(n.right)
    best = max(best, l + r)       # path THROUGH n (what we record)
    return 1 + max(l, r)          # path ENDING at n going down (what parent can use)
```

### Build from preorder + inorder
Preorder's first element is the root; its index in inorder tells how many nodes are in the left subtree.
Use a dict `value -> inorder index` for O(1) lookups and an iterator over preorder.

## 4. Complexity
- Time O(n) for all of the above (each node visited once).
- Space: DFS O(h) stack (h = log n balanced, n skewed); BFS O(w) where w is the max width (up to n/2).
- Building a tree from traversals: O(n) with a hashmap, O(n^2) with `list.index`.

## 5. Common mistakes
- Forgetting the `None` base case, or testing `if not node.left and not node.right` where None is possible.
- Height in nodes vs edges (diameter asks edges; `max_depth` counts nodes). Clarify with the interviewer.
- Python recursion limit is ~1000: a skewed tree of 10^5 nodes crashes recursive DFS. Mention iterative as the fix.
- BFS: using `len(q)` live inside the loop instead of freezing it before the level loop.
- Max path sum: not clamping negative child gains to 0; initializing best to 0 (all-negative trees).
- LCA: comparing `.val` when the problem gives node references (or vice versa); not handling p being an ancestor of q.
- Mutating the tree (invert) when the caller expects a copy - state whether you mutate.

## 6. Interview tips
- Say the recurrence out loud first: "answer(node) depends on answer(left), answer(right)".
- Decide **top-down** (state in parameters) vs **bottom-up** (state in return value) before coding.
- Always test: empty tree, single node, skewed tree, all-negative values.
- Expect the follow-up "now do it iteratively" - know iterative inorder and BFS cold. Morris traversal (O(1) space) is a bonus.
- Serialize/deserialize, zigzag level order, and vertical order are common Google/Uber extensions of BFS.

## Your task
Fill in `exercises.py` (10 problems, easy to hard), then run:
`cd 03-dsa/week-13-binary-trees && ../../.venv/bin/pytest -q`
Target: 7-8 hours. Do the first 6 in the first sitting; leave `build_tree` and `max_path_sum` for a fresh day.
