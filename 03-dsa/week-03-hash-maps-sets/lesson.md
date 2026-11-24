# Week 3: Hash maps and sets

## 1. Concept (~2 hrs)
A hash map (`dict`) stores key -> value; a set stores unique keys. Both give **O(1) average** insert, lookup and delete, at the cost of O(n) memory. Keys must be hashable (int, str, tuple of hashables; NOT list/dict/set). Worst case is O(n) with many collisions, but in interviews you say "O(1) average".

Useful tools: `dict.get(k, default)`, `setdefault`, `collections.Counter`, `collections.defaultdict(list/int/set)`, `frozenset`, `tuple(sorted(s))` as a hashable key.

## 2. How to recognize the pattern
- "Have I seen this before?" / duplicates -> set.
- "Find a pair/complement" -> dict from value to index (one pass).
- "Count frequency", "most common", "anagram" -> Counter or a 26-length tuple key.
- "Group by some property" -> dict of key -> list, where the key is a canonical form.
- "Subarray with sum k" -> prefix sums + dict of prefix -> count.
- "Longest consecutive / sequence in unsorted data in O(n)" -> set + only start from sequence starts.
- "Cache / O(1) get and put with eviction" -> dict + doubly linked list (or OrderedDict).

## 3. Templates
Complement lookup:
```python
seen = {}
for i, x in enumerate(nums):
    if target - x in seen:
        return [seen[target - x], i]
    seen[x] = i
```
Group by canonical key:
```python
groups = defaultdict(list)
for w in words:
    groups[tuple(sorted(w))].append(w)
```
Prefix-sum counting:
```python
count = {0: 1}; total = 0; ans = 0
for x in nums:
    total += x
    ans += count.get(total - k, 0)
    count[total] = count.get(total, 0) + 1
```
Longest consecutive run:
```python
s = set(nums)
for x in s:
    if x - 1 not in s:        # x starts a run
        y = x
        while y + 1 in s: y += 1
```
Two-way mapping check (isomorphic/pattern): maintain map a->b and b->a, both must stay consistent.

## 4. Complexity
Building a map/set of n items is O(n) time/space. Order the check-then-insert carefully so each element is processed once. Sorting-based keys cost O(k log k) per key (k = key length); counting-based keys cost O(k).

## 5. Common mistakes
- Inserting before checking the complement (a number pairing with itself).
- Using a list as a dict key (TypeError); use a tuple.
- Forgetting `count[0] = 1` for prefix sums (misses subarrays starting at index 0).
- Iterating a dict while mutating it.
- Using `in list` where a set would do (silently O(n^2)).
- In the consecutive-sequence problem, expanding from every number (O(n^2)).
- LRU: forgetting to refresh recency on `get`.

## 6. Interview tips
- Say the trade-off aloud: "O(n) extra space to reduce O(n^2) to O(n)".
- Clarify duplicates, negatives, and whether exactly one answer exists.
- Know `OrderedDict.move_to_end` / `popitem(last=False)` for LRU, but be ready to hand-build the linked list version (week 9).
- Normal Python dicts preserve insertion order; mention it when relevant.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 03-dsa/week-03-hash-maps-sets -q`.
