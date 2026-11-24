# Week 5: Sliding window

## 1. The idea
A window is a contiguous slice `nums[l..r]`. Instead of recomputing a property (sum, distinct
count, frequencies) for every slice, you **update it incrementally** as `r` moves right
(add one element) and `l` moves right (remove one element). Each index enters and leaves the
window at most once, so total work is O(n) even though there is a loop inside a loop.

## 2. How to recognise it
- "Longest / shortest / maximum / minimum **contiguous** subarray or substring such that ..."
- "Every window of size k", "substring containing all of ...", "at most k distinct / zeros".
- The constraint is monotonic: growing the window can only make it "more full", shrinking can
  only make it "less full" (this is why positive numbers matter for sum problems).
- Negative numbers with a "sum equals k" condition: window does NOT work, use prefix sums (week 6).

## 3. Template A: fixed size k
```python
def fixed(nums, k):
    cur = sum(nums[:k])
    best = cur
    for i in range(k, len(nums)):
        cur += nums[i] - nums[i - k]     # add entering, remove leaving
        best = max(best, cur)
    return best
```

## 4. Template B: variable size, find the LONGEST valid window
```python
def longest(s):
    l = 0
    state = {}                      # whatever you need: counts, sum, zeros...
    best = 0
    for r, x in enumerate(s):
        add(state, x)               # expand
        while invalid(state):       # shrink until valid again
            remove(state, s[l])
            l += 1
        best = max(best, r - l + 1) # window is valid here
    return best
```

## 5. Template C: variable size, find the SHORTEST valid window
```python
def shortest(nums, target):
    l = 0
    cur = 0
    best = INF
    for r, x in enumerate(nums):
        cur += x
        while valid(cur):           # shrink WHILE still valid, record each time
            best = min(best, r - l + 1)
            cur -= nums[l]
            l += 1
    return best
```
Longest: record after shrinking. Shortest: record inside the shrink loop. This is the most
common source of off-by-one bugs.

## 6. Helpers you need
- `dict` / `collections.Counter` for counts. Delete keys whose count reaches 0 if you compare
  `len(dict)` or compare two Counters.
- `collections.deque` as a **monotonic deque** for window max/min: store indices, keep values
  decreasing, pop front when out of window, pop back while smaller than the new value. Each index
  is pushed and popped once, so O(n).
- A "missing" / "matches" counter makes the validity check O(1) (see `min_window`).

## 7. Complexity
Time O(n) (each pointer moves at most n times). Space O(1), O(alphabet) or O(k) depending on the
state. `Counter == Counter` comparison costs O(alphabet), which is fine for 26 letters but say so.

## 8. Common mistakes
- Using `if` instead of `while` when shrinking (window stays invalid).
- Recording the answer at the wrong place (see templates B vs C).
- Forgetting to delete zero-count keys, then `len(count)` overstates distinct characters.
- Slicing in the loop (`s[l:r+1]`) which silently makes it O(n^2).
- Moving `l` backwards when jumping past a repeat (use `l = max(l, last[ch] + 1)` or check
  `last[ch] >= l`).
- Applying a window to arrays with negatives and a sum constraint.
- `character_replacement`: `max_count` never needs to decrease; a stale larger value can only
  fail to shrink the window, and the window only matters when it beats the previous best.

## 9. Interview tips
- Say "window", define what it represents and its invariant before coding.
- State why it's O(n) despite the nested loop (amortised: each element enters/leaves once).
- Clarify: lowercase only? Unicode? Can k be 0 or larger than n? Empty input?
- Typical follow-ups: "what if the stream is infinite?" (state is O(1)/O(k), process online),
  "return the window itself, not the length" (track best_l), "exactly k" = atMost(k) - atMost(k-1).

## Your task
Fill in `exercises.py`, then run `pytest -q` in this folder. ~2 hrs on the templates (re-derive
each one on paper), ~5 hrs on problems. Do `min_window` and `max_sliding_window` last.
