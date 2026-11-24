# Week 2: Arrays and strings

## 1. Concept (~2 hrs)
Arrays (Python `list`) and strings are the base of most interview questions. Key facts:
- `list`: O(1) index/append/pop-last; O(n) insert/delete in the middle, slicing, `in`.
- `str` is **immutable**: any "modification" builds a new string (O(n)). To edit characters, convert to `list(s)`, modify, then `"".join(...)`.
- Slicing `a[i:j]` copies (O(j-i)). In-place problems forbid extra copies.
- 2D grids: `grid[r][c]`, `len(grid)` rows, `len(grid[0])` cols. Never build with `[[0]*m]*n` (aliases the same row); use `[[0]*m for _ in range(n)]`.

## 2. How to recognize the pattern
- "In place", "O(1) extra space" -> read/write pointers or swaps.
- "Reverse / rotate / partition" -> swap from both ends, or reverse-three-times trick.
- "Everything except self", "running" quantities -> prefix and suffix passes.
- "Palindrome" -> compare ends moving inward, or expand around centers.
- "Matrix traversal" -> track boundaries (top, bottom, left, right) or use transpose + reverse.
- "Merge sorted in place" -> fill from the back so you do not overwrite unread values.

## 3. Templates
Read/write pointer (stable in-place filter):
```python
w = 0
for r in range(len(nums)):
    if keep(nums[r]):
        nums[w] = nums[r]
        w += 1
# nums[:w] is the filtered result
```
Reverse a range in place:
```python
def reverse(a, i, j):
    while i < j:
        a[i], a[j] = a[j], a[i]
        i += 1; j -= 1
```
Rotate right by k: reverse all, reverse first k, reverse the rest (O(n) time, O(1) space).

Prefix/suffix product:
```python
out = [1] * n
for i in range(1, n): out[i] = out[i-1] * nums[i-1]
suf = 1
for i in range(n-1, -1, -1):
    out[i] *= suf
    suf *= nums[i]
```
Expand around center (palindromes): for each center (i,i) and (i,i+1) expand while `s[l]==s[r]`; O(n^2) time, O(1) space.

Matrix rotate 90 degrees clockwise: transpose, then reverse each row.

## 4. Complexity
Most array/string passes are O(n) time. Two-pass is still O(n). In-place problems are O(1) extra space (the output list is not counted when it is required). Palindromic substring by expansion is O(n^2).

## 5. Common mistakes
- Modifying a list while iterating it by value (use indices).
- Off-by-one on slice bounds and loop ranges; empty and single-element inputs.
- Reassigning the parameter (`nums = nums[k:] + ...`) instead of mutating (`nums[:] = ...`) when asked to modify in place.
- Building strings with `+=` in a loop; use list + `join`.
- Forgetting `k %= n` for rotations, and negative numbers/zero in products.
- Using division for product-except-self (breaks on zeros, and is usually disallowed).

## 6. Interview tips
- Ask: can I mutate the input? Is it ASCII? Case-sensitive? Empty allowed?
- Walk through a tiny example by hand before coding; test with `[]`, `[x]`, duplicates.
- Mention the slicing shortcut (`nums[:] = nums[-k:] + nums[:-k]`) but be ready to do the O(1)-space version.
- Writing from the back (merge sorted array) and the read/write pointer are the two tricks Google-style questions lean on.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-02-arrays-strings -q`.
