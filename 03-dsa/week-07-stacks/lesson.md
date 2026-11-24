# Week 7: Stacks (including monotonic stacks)

## 1. Concept
A stack is Last-In-First-Out (LIFO). In Python use a plain `list`:
```python
st = []
st.append(x)    # push, O(1) amortized
st[-1]          # peek, O(1)  (check `if st` first!)
st.pop()        # pop, O(1)   (IndexError on empty)
```
Do not use `list.pop(0)` or `insert(0, x)` (O(n)); that is a queue job (week 8).

## 2. How to recognize a stack problem
- Matching / nesting: brackets, nested tags, `decode "3[a2[c]]"`.
- "Undo" the most recent thing: remove adjacent duplicates, backspace, path `..`.
- Expression evaluation: RPN, calculators, operator precedence.
- "Next greater / next smaller / previous greater" element -> **monotonic stack**.
- Simulating collisions where the latest item interacts with the new one.
- Anything recursive you want to make iterative (DFS) -> explicit stack.

## 3. Templates

### Matching
```python
pairs = {')': '(', ']': '[', '}': '{'}
st = []
for ch in s:
    if ch in pairs:
        if not st or st.pop() != pairs[ch]:
            return False
    else:
        st.append(ch)
return not st
```

### Monotonic stack: next greater element (store INDICES)
```python
res = [-1] * n
st = []                       # indices; values at those indices are decreasing
for i, x in enumerate(nums):
    while st and nums[st[-1]] < x:
        res[st.pop()] = x     # x is the next greater for the popped index
    st.append(i)
# whatever is left in st has no next greater element
```
Variants: flip the comparison for "next smaller"; iterate `range(2*n)` with `i % n` for circular arrays; iterate right-to-left for "previous".

### Stack with extra state
Push tuples: `(char, count)`, `(value, current_min)`, `(prev_string, repeat_count)`.

## 4. Complexity
Each element is pushed once and popped at most once, so a monotonic stack loop is **O(n) time** even though there is a nested `while`. Space O(n).

## 5. Common mistakes
- Popping or peeking an empty stack. Guard with `while st and ...`.
- Forgetting to check the stack is empty at the end (`"(("` is invalid).
- Storing values when you need indices (distance / width problems need indices).
- Strict vs non-strict comparison (`<` vs `<=`) with duplicates.
- RPN division: `int(a / b)` truncates toward zero, `a // b` floors (differs for negatives).
- Using `str +=` in a loop for big inputs; collect into a list and `"".join`.

## 6. Interview tips
- Say "monotonic stack" out loud and state its invariant (decreasing / increasing).
- Explain the amortized O(n) argument: each element is popped once.
- For histograms/rectangles: add a sentinel (0 height) at the end to flush the stack.
- Clarify edge cases: empty input, invalid characters, integer overflow rules.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-07-stacks -q` (from the repo root).
