# Week 4: Two pointers

## 1. The idea
Instead of checking every pair (O(n^2)), keep two indices and move them by a rule so each index
only travels once: O(n). The rule is what makes it correct, and it usually relies on **order**
(sorted input) or on a **monotonic property** (moving a pointer only makes some quantity shrink).

## 2. How to recognise it
- Input is a sorted array / string and you look for a pair, triplet, or target sum.
- "In place", "O(1) extra space", "remove / move / partition elements".
- Palindromes, reversing, comparing from both ends.
- Merging two sorted sequences.
- You are tempted to write a nested loop, and a sorted order or greedy argument says one pointer
  can safely be discarded each step.

## 3. The three flavours
**a) Opposite ends (converging)**: `l = 0, r = n-1`, move toward each other.
```python
def pair_sum_sorted(a, target):
    l, r = 0, len(a) - 1
    while l < r:
        s = a[l] + a[r]
        if s == target:
            return l, r
        if s < target:
            l += 1          # need a bigger sum -> only moving l can help
        else:
            r -= 1
    return None
```

**b) Same direction (slow / fast, read / write)**: `w` is where the next kept element goes,
`r` scans.
```python
def compact(a, keep):            # remove elements failing keep(); returns new length
    w = 0
    for r in range(len(a)):
        if keep(a[r]):
            a[w] = a[r]
            w += 1
    return w
```

**c) Two sequences**: one pointer per input (merge, subsequence check, intersection). Often
filling from the **back** avoids overwriting (`merge_sorted_in_place`).

**d) Fix one, two-pointer the rest** (3Sum): sort, loop `i`, run converging pointers on
`i+1..n-1`. O(n^2) instead of O(n^3). Skip duplicates at every level.

## 4. Why moving a pointer is safe (proof sketch, say it out loud)
Container with most water: area = width * min(h[l], h[r]). If you move the TALLER side inward,
width shrinks and min can't grow (still bounded by the shorter), so that move can never improve
things. Hence discard the shorter side. Being able to justify the discard rule is what
interviewers grade.

## 5. Complexity
| Pattern | Time | Space |
|---|---|---|
| Converging on sorted data | O(n) | O(1) |
| Read/write in place | O(n) | O(1) |
| Sort + two pointers | O(n log n) | O(1)-O(n) depending on sort |
| 3Sum | O(n^2) | O(1) extra |

If the array is unsorted and you need a pair sum, a hash map (O(n) time, O(n) space) is the
alternative. State the tradeoff.

## 6. Common mistakes
- `while l <= r` vs `while l < r`: decide whether a pointer may meet itself (pair sums: no;
  Dutch flag: yes for `mid <= hi`).
- Not skipping duplicates in 3Sum (duplicate triplets) or skipping them in the wrong place
  (skipping before use loses valid answers like `[0,0,0]`).
- Dutch national flag: after swapping with `hi`, advancing `mid` skips an unexamined value.
- Overwriting unread data when merging in place (go from the back).
- Forgetting empty / one-element input.
- Using `s = s[1:]` or building copies, which turns O(n) into O(n^2).

## 7. Interview tips
- First say the brute force and its cost, then say what property lets you discard candidates.
- Ask: is it sorted? can I sort it (does the answer need original indices)? may I modify input?
- Write the loop invariant in a comment ("everything left of `w` is already kept").
- Test on: empty, one element, all equal, already sorted, pointers meeting in the middle.
- Follow-ups often asked: 4Sum (k-Sum generalisation), closest 3Sum, count pairs, linked-list
  version (fast/slow cycle detection next weeks).

## Your task
Fill in `exercises.py` (ordered easy to hard), then run `pytest -q` in this folder.
Plan: ~2 hrs reading and re-deriving the proofs above, ~5 hrs on problems.
