# Week 4: Lists, tuples, strings in depth

## 1. Lists
An ordered, changeable collection.
```python
nums = [5, 2, 9]
nums[0]            # 5
nums[-1]           # 9
nums.append(7)     # [5, 2, 9, 7]
nums.insert(1, 8)  # [5, 8, 2, 9, 7]
nums.pop()         # removes and returns last (7)
nums.remove(8)     # removes first 8
len(nums); 9 in nums; sum(nums); max(nums)
nums.extend([1, 2])   # add many
```

## 2. Slicing (works on lists, strings, tuples)
`seq[start:stop:step]`, stop excluded, all parts optional.
```python
a = [0, 1, 2, 3, 4, 5]
a[1:4]    # [1, 2, 3]
a[:2]     # [0, 1]
a[-2:]    # [4, 5]
a[::2]    # [0, 2, 4]
a[::-1]   # reversed copy
```
Slicing makes a NEW list. Out-of-range slices don't crash.

## 3. Tuples
Like lists but **immutable** (can't change). Written with parentheses.
```python
point = (3, 4)
x, y = point          # unpacking
single = (5,)         # note the comma
```
Use tuples for fixed groups of values.

## 4. Sorting
```python
sorted(nums)               # returns a NEW sorted list
nums.sort()                # sorts IN PLACE, returns None
sorted(nums, reverse=True)
sorted(words, key=len)     # sort by length
```
`.sort()` returning `None` catches many beginners: `x = x.sort()` makes `x` None.

## 5. Copy vs reference
```python
a = [1, 2]
b = a            # same list! two names
b.append(3)      # a is now [1, 2, 3] too
c = a.copy()     # or a[:] or list(a): independent (shallow) copy
```
Shallow copy: nested lists inside are still shared. Use `copy.deepcopy` to copy fully.

## 6. Nested lists
```python
grid = [[1, 2, 3],
        [4, 5, 6]]
grid[1][2]       # 6   (row 1, column 2)
for row in grid:
    for val in row: ...
```
Trap: `[[0] * 3] * 2` repeats the SAME inner list. Build rows with a loop instead.

## 7. Useful string methods
```python
s = "  Hello, World  "
s.strip()              # 'Hello, World'
s.lower(); s.upper()
"a,b,c".split(",")     # ['a', 'b', 'c']
"a b  c".split()       # ['a', 'b', 'c']  (any whitespace)
"-".join(["a", "b"])   # 'a-b'
s.replace("l", "L")
"hello".startswith("he"); "hello".find("l")   # 2 (-1 if missing)
"abc".isalpha(); "123".isdigit()
"hello".count("l")     # 2
```
Strings never change; every method returns a new string.

## 8. Looping tools
`for i in range(len(a))` gives indexes; `for x in a` gives items; `for i, x in enumerate(a)` gives both.

## Common mistakes
- `IndexError`: index past the end (last valid index is `len(a) - 1`).
- Changing a list while looping over it.
- `b = a` does not copy.
- `x = x.sort()` / `x = x.append(1)` set x to None.
- Calling `s.upper()` without using the result.

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-04-lists-tuples -v`
