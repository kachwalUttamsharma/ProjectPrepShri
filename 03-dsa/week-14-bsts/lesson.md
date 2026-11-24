# Week 14: Binary search trees (BSTs)

## 1. Concept
A BST keeps this invariant at **every** node: all values in the left subtree are smaller, all values in
the right subtree are larger. Consequences:
- Search / insert / delete follow a single root-to-leaf path: O(h). Balanced h = log n, skewed h = n.
- **Inorder traversal visits values in sorted order.** This one fact solves a huge share of BST problems.
- Python has no built-in balanced BST. In interviews you use a plain (possibly unbalanced) BST, or
  `bisect` on a sorted list, or `sortedcontainers.SortedList` if allowed (ask).

## 2. How to recognize the pattern
- "Given a BST ..." -> use the ordering; do NOT do a full O(n) search when O(h) is possible.
- "k-th smallest", "next/previous", "range", "sorted output" -> inorder traversal.
- "Validate" -> bounds passed down (or inorder strictly increasing).
- "Build balanced from sorted" -> pick the middle as the root.
- "Iterator over tree" -> explicit stack of the leftmost path (controlled recursion).
- "Two nodes swapped" -> find inorder inversions.

## 3. Templates

### Search / closest value (iterative, O(1) space)
```python
cur = root
while cur and cur.val != target:
    cur = cur.left if target < cur.val else cur.right
```

### Insert (iterative)
```python
if not root: return TreeNode(val)
cur = root
while True:
    if val < cur.val:
        if not cur.left: cur.left = TreeNode(val); break
        cur = cur.left
    else:
        if not cur.right: cur.right = TreeNode(val); break
        cur = cur.right
return root
```

### Validate with bounds
```python
def ok(n, lo, hi):
    if not n: return True
    if (lo is not None and n.val <= lo) or (hi is not None and n.val >= hi): return False
    return ok(n.left, lo, n.val) and ok(n.right, n.val, hi)
```

### Delete (three cases)
```python
def delete(n, key):
    if not n: return None
    if key < n.val:   n.left  = delete(n.left, key)
    elif key > n.val: n.right = delete(n.right, key)
    else:
        if not n.left:  return n.right
        if not n.right: return n.left
        s = n.right
        while s.left: s = s.left          # inorder successor
        n.val = s.val
        n.right = delete(n.right, s.val)
    return n
```

### Controlled inorder (iterator / early stop)
```python
stack, cur = [], root
while cur or stack:
    while cur: stack.append(cur); cur = cur.left
    cur = stack.pop()
    # visit cur; may stop here for k-th smallest
    cur = cur.right
```

### Balanced BST from sorted array
```python
def build(lo, hi):
    if lo > hi: return None
    mid = (lo + hi) // 2
    return TreeNode(nums[mid], build(lo, mid - 1), build(mid + 1, hi))
```

## 4. Complexity
| Operation | Balanced | Worst (skewed) |
|---|---|---|
| search / insert / delete | O(log n) | O(n) |
| k-th smallest | O(h + k) | O(n) |
| validate | O(n) | O(n) |
| build from sorted | O(n) | - |
| iterator next() | amortized O(1), O(h) memory | |
Space for recursion is O(h).

## 5. Common mistakes
- **Validating only parent vs child.** `[5, 4, 6, None, None, 3, 7]` passes the local check but 3 is in 5's right subtree.
- Using `<`/`>` instead of strict bounds, or initializing bounds with `-inf/inf` and breaking on values equal to INT_MIN. Prefer `None` bounds.
- Delete with two children: forgetting to delete the successor from the right subtree afterwards.
- Doing full-tree DFS on a BST problem (O(n)) when O(h) is expected.
- Slicing arrays in `sorted_array_to_bst` (`nums[:mid]`) makes it O(n log n) / extra memory.
- Iterator that flattens the whole tree into a list breaks the O(h) memory requirement.
- Recover-tree: assuming the swapped nodes are non-adjacent; adjacent swaps produce only ONE inversion.

## 6. Interview tips
- Ask about duplicates (left? right? disallowed?) and whether the tree is balanced.
- State complexity in terms of h and mention it degrades to O(n) when skewed.
- "Inorder successor/predecessor" and "range sum" are very common warm-ups; both are small variations of the search walk.
- Know the follow-up: convert BST <-> sorted doubly linked list, serialize a BST (preorder only suffices), Morris traversal for O(1) space.
- If asked to support insertions with rank queries at scale, mention self-balancing trees (AVL / red-black) or augmenting nodes with subtree sizes.

## Your task
Fill in `exercises.py` (10 problems), then run `cd 03-dsa/week-14-bsts && ../../.venv/bin/pytest -q`.
