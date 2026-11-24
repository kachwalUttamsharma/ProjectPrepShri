# Week 9: Linked lists

## 1. Concept
A singly linked list is a chain of nodes; each holds a value and a pointer to the next node. No random access: reaching index i costs O(i). Insert/delete is O(1) **once you hold the previous node**.
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```
Python has no pointers, but names are references: `a = b` makes two names for the same node; `a.next = b` rewires the chain.

## 2. How to recognize the pattern
- "Reverse", "merge", "reorder", "rotate", "remove the n-th from end", "palindrome list".
- "Cycle" / "middle" / "k-th from end" / "intersection" -> **fast & slow pointers**.
- Head might be removed or replaced -> **dummy node**.
- O(1) extra space required -> in-place pointer surgery (no list copy).

## 3. Templates

### Dummy head (removes special cases for the head)
```python
dummy = ListNode(0, head)
prev = dummy
while prev.next:
    if should_delete(prev.next):
        prev.next = prev.next.next
    else:
        prev = prev.next
return dummy.next
```

### Reverse (iterative, 3 pointers)
```python
prev, cur = None, head
while cur:
    nxt = cur.next      # save
    cur.next = prev     # flip
    prev, cur = cur, nxt
return prev             # new head
```

### Fast & slow
```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
# slow is the middle (second middle for even length)
```
Cycle: if they ever meet there is a cycle. Cycle start: after meeting, reset one pointer to head and move both one step at a time; they meet at the cycle entry (Floyd).

### Merge two sorted lists
```python
dummy = tail = ListNode()
while a and b:
    if a.val <= b.val: tail.next, a = a, a.next
    else:              tail.next, b = b, b.next
    tail = tail.next
tail.next = a or b
```

### Gap technique (n-th from end)
Advance `fast` n steps first, then move `fast` and `slow` together; when `fast` reaches the end, `slow` is just before the target.

## 4. Complexity
Most are O(n) time, O(1) space (iterative). Recursive reverse is O(n) stack: avoid it for 10^5 nodes (Python recursion limit ~1000).
Merge k lists with a heap: O(N log k).

## 5. Common mistakes
- Losing the rest of the list: save `cur.next` before overwriting it.
- `fast.next.next` without checking `fast` and `fast.next`.
- Forgetting to set the last node's `next = None` (creates an accidental cycle), e.g. in reorder / split.
- Not using a dummy node, then special-casing the head badly.
- Returning the old head after reversing.
- Comparing nodes with `==` on values instead of `is` for identity (intersection, cycles).
- Heap with ListNodes: tie-breaking on equal values compares nodes -> TypeError. Push `(val, index, node)`.

## 6. Interview tips
- Draw boxes and arrows; walk a 3-node example plus empty and single-node lists.
- Ask: singly or doubly linked? Can I modify the list? Is O(1) space required?
- Name the technique ("dummy node", "fast/slow", "reverse second half").
- Re-trace your pointer assignments in the right order; most bugs are order bugs.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-09-linked-lists -q` (from the repo root).
