# Week 1: Big-O and complexity analysis

## 1. Concept (~2 hrs)
Big-O describes how runtime (or memory) **grows** as input size `n` grows, ignoring constants and lower-order terms. Interviewers always ask "what is the time and space complexity?" - you must answer without hesitation.

| Class | Name | Typical example |
|---|---|---|
| O(1) | constant | dict lookup, list index, append (amortized) |
| O(log n) | logarithmic | binary search, halving a number, heap push/pop |
| O(n) | linear | one loop, `in` on a list, sum |
| O(n log n) | linearithmic | sorting, merge sort |
| O(n^2) | quadratic | nested loops over the same input |
| O(2^n) | exponential | all subsets, naive Fibonacci |
| O(n!) | factorial | all permutations |

Rules:
- Drop constants: `O(2n)` -> `O(n)`. Drop lower terms: `O(n^2 + n)` -> `O(n^2)`.
- Sequential steps **add**, nested steps **multiply**.
- Different inputs get different variables: two arrays -> `O(n + m)` or `O(n * m)`, not `O(n)`.
- **Amortized**: `list.append` is O(1) amortized (occasional O(n) resize, averaging out).
- **Space** counts extra memory you allocate (not the input). Recursion depth counts too.
- Worst case unless stated otherwise (hash lookups are O(1) average, O(n) worst).

## 2. Python built-in costs (memorize)
| Structure | O(1) | O(n) | Notes |
|---|---|---|---|
| `list` | `a[i]`, `a[i]=x`, `append`, `pop()` | `insert(i,x)`, `pop(0)`, `x in a`, `remove`, `a.index`, `a[i:j]` (O(j-i)), `a + b`, `sorted` is O(n log n) | `pop(0)` and `insert(0,x)` shift everything |
| `dict` | get/set/del/`in` (avg) | iterate, copy, `keys()` list conversion | keys must be hashable; insertion-ordered |
| `set` | add/remove/`in` (avg) | iterate; `a & b` is O(min(n,m)), `a | b` is O(n+m) | |
| `collections.deque` | `append`, `appendleft`, `pop`, `popleft` | index in the middle is O(n) | use for queues |
| `str` | `s[i]`, `len` | `s + t` (new string), `in` (substring search), `s[i:j]`, `join` | immutable! |
| `heapq` | `heap[0]` | `heappush/heappop` O(log n), `heapify` O(n) | |

Classic trap: `result += ch` in a loop **may** be O(n^2) for strings (new string each time; CPython sometimes optimizes but never rely on it). Collect pieces in a list and `"".join(pieces)` once: O(n).
Another trap: `x in some_list` inside a loop -> accidental O(n^2). Convert to a `set` first.
Another trap: slicing `a[1:]` in recursion copies -> O(n) per call.

## 3. How to analyze code
1. Count loops: a loop over n is O(n); a loop that halves/doubles the counter is O(log n).
2. Nested loops multiply, unless the inner bound shrinks: `for i in range(n): for j in range(i)` is n(n-1)/2 = O(n^2).
3. Recursion: write the recurrence. `T(n) = T(n/2) + O(1)` -> O(log n). `T(n)=2T(n/2)+O(n)` -> O(n log n). `T(n)=2T(n-1)` -> O(2^n).
4. Hidden costs inside the loop body (slicing, `in list`, `sorted`, string concat).
5. Space: new containers + recursion stack.

## 4. Patterns to recognize
- "Find a pair/duplicate" with brute force O(n^2) -> trade space for time with a set/dict: O(n).
- Sorted input or "O(log n)" required -> binary search.
- "Do it in place / O(1) space" -> two pointers / index tricks.
- n up to 10^5 -> need O(n log n) or better. n up to ~20 -> exponential is OK. n up to ~1000 -> O(n^2) OK.

## 5. Template: trading space for time
```python
def has_pair_with_sum(nums, target):      # O(n) time, O(n) space
    seen = set()
    for x in nums:
        if target - x in seen:
            return True
        seen.add(x)
    return False
```
Template: fast exponentiation (halve the problem)
```python
def power(x, n):                          # O(log n)
    result = 1
    while n:
        if n & 1:
            result *= x
        x *= x
        n >>= 1
    return result
```

## 6. Common mistakes
- Saying O(n) for something that does `sorted` inside (it's O(n log n)).
- Forgetting that `str` slicing/concat and `list` slicing copy.
- Forgetting recursion stack space (a recursive O(n) depth is O(n) space).
- Treating `a.pop(0)`, `a.insert(0, x)`, `x in list` as O(1).
- Using one variable `n` for two different inputs.
- Calling two-pass approaches "O(2n)" - say O(n).

## 7. Interview tips
- State brute force first with its complexity, then improve. Say *why* the bottleneck is what it is.
- Always state both time and space, and mention average vs worst case for hashing.
- Clarify constraints (n, value range) - they tell you the intended complexity.
- Python-specific: mention that `sort` is Timsort O(n log n) and stable; `heapq` is a min-heap.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-01-big-o-complexity -q`. The tests include larger inputs: an accidentally quadratic solution will be noticeably slow.
