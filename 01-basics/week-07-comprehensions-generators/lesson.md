# Week 7: Comprehensions, lambda, iterators and generators

## 1. List comprehensions
A short way to build a list from a loop.
```python
squares = [n * n for n in range(5)]            # [0, 1, 4, 9, 16]
evens   = [n for n in range(10) if n % 2 == 0] # filter with `if`
labels  = ["even" if n % 2 == 0 else "odd" for n in range(3)]  # if/else goes BEFORE `for`
pairs   = [(a, b) for a in "ab" for b in (1, 2)]               # nested loops
```
Same as the loop: `result = []; for n in ...: if ...: result.append(expr)`. If it gets hard to read, use a normal loop.

## 2. Dict and set comprehensions
```python
{w: len(w) for w in ["a", "bb"]}   # {'a': 1, 'bb': 2}
{n % 3 for n in range(10)}         # {0, 1, 2}
```

## 3. lambda
A tiny anonymous one-expression function.
```python
double = lambda x: x * 2
double(4)             # 8
```
Mostly used as a `key=` argument or inside `map`/`filter`. For anything longer, use `def`.

## 4. sorted with key=
```python
words = ["pear", "fig", "banana"]
sorted(words, key=len)                       # ['fig', 'pear', 'banana']
sorted(words, key=lambda w: w[-1])           # by last letter
people = [("ann", 30), ("bob", 25)]
sorted(people, key=lambda p: p[1])           # by age
sorted(words, key=lambda w: (len(w), w))     # by length, then alphabetically (tuple key)
sorted(words, reverse=True)
```
Sorting is stable: ties keep their original order. `min` and `max` also accept `key=`.

## 5. enumerate and zip
```python
for i, ch in enumerate("abc"):           # (0,'a') (1,'b') (2,'c')
for i, ch in enumerate("abc", start=1):  # start counting at 1
for a, b in zip([1, 2, 3], "xyz"):       # (1,'x') (2,'y') (3,'z')
dict(zip(["a", "b"], [1, 2]))            # {'a': 1, 'b': 2}
```
`zip` stops at the shortest input.

## 6. map, filter, any, all
```python
list(map(str, [1, 2]))                   # ['1', '2']
list(filter(lambda n: n > 1, [1, 2, 3])) # [2, 3]
any(n > 2 for n in [1, 2, 3])            # True
all(n > 0 for n in [1, 2, 3])            # True
```
`map` and `filter` return lazy objects; wrap in `list(...)` to see them. A comprehension is usually clearer.

## 7. Iterators and generators
An **iterable** is anything you can loop over (list, str, dict, file). An **iterator** hands out one item at a time with `next()`.

A **generator** function uses `yield` instead of `return`. It pauses after each `yield` and continues on the next request, so it produces values lazily without storing them all.
```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

list(countdown(3))      # [3, 2, 1]
gen = countdown(2)
next(gen)               # 2
next(gen)               # 1
next(gen)               # StopIteration
```
A generator expression is like a list comprehension with parentheses: `sum(n * n for n in range(1000000))` uses almost no memory. Generators can be infinite; take a few with `itertools.islice(gen, 5)`. A generator can be used only once.

## Common mistakes
- Writing `[x for x in data if x else 0]` (an `else` needs to go before `for`).
- Packing too much logic into one comprehension.
- Printing a `map`/generator object instead of `list(...)` of it.
- Reusing an exhausted generator (it's empty the second time).
- `sorted(...)` returns a new list; `.sort()` changes in place and returns `None`.

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-07-comprehensions-generators -v`
