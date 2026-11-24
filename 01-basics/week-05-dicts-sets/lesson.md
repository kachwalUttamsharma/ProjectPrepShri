# Week 5: Dictionaries and sets

## 1. Dictionaries
A dict maps **keys** to **values**. Lookup by key is very fast, which is why dicts are central to interviews.
```python
ages = {"ann": 30, "bob": 25}
ages["ann"]            # 30
ages["cat"] = 41       # add or overwrite
del ages["bob"]        # remove (KeyError if missing)
"ann" in ages          # True (checks keys)
len(ages)              # 2
ages.get("zed")        # None   (no crash)
ages.get("zed", 0)     # 0      (custom default)
ages.pop("ann", None)  # remove, with default
```
Keys must be immutable (str, int, tuple), not lists. Insertion order is preserved.

## 2. Looping
```python
for key in ages: ...
for value in ages.values(): ...
for key, value in ages.items(): ...
```
Don't add or remove keys while looping over the dict.

## 3. Counting pattern
```python
counts = {}
for ch in "banana":
    counts[ch] = counts.get(ch, 0) + 1
# {'b': 1, 'a': 3, 'n': 2}
```
Shortcut: `from collections import Counter; Counter("banana")`.

## 4. Grouping pattern
```python
groups = {}
for word in ["apple", "avocado", "banana"]:
    groups.setdefault(word[0], []).append(word)
# {'a': ['apple', 'avocado'], 'b': ['banana']}
```
`defaultdict(list)` from `collections` does the same without `setdefault`.

## 5. Sets
An unordered collection of **unique** items. Membership tests are fast.
```python
s = {1, 2, 3}
s.add(4); s.discard(10)     # discard doesn't crash if missing
set([1, 1, 2])              # {1, 2}
empty = set()               # NOT {} (that's an empty dict)
```
Set operations:
```python
a = {1, 2, 3}; b = {2, 3, 4}
a | b    # union        {1, 2, 3, 4}
a & b    # intersection {2, 3}
a - b    # difference   {1}
a ^ b    # symmetric difference {1, 4}
a <= b   # subset?
```

## 6. Which to use?
- Need to ask "have I seen this?" -> set.
- Need to count or look something up by name -> dict.
- Need order and duplicates -> list.

## 7. Time cost (a first look at Big-O)
`x in list` checks items one by one (slow for big lists). `x in set` / `x in dict` is almost instant. Replacing a list lookup with a set or dict is a classic interview speed-up.

## Common mistakes
- `KeyError`: using `d[key]` for a missing key (use `.get` or check `in`).
- `{}` is an empty dict, not a set.
- Expecting sets to be ordered or indexable (`s[0]` fails).
- Using a list as a key (unhashable).
- Modifying a dict while iterating it.

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-05-dicts-sets -v`
