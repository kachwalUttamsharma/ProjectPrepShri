# Week 3: Functions

## 1. Defining and calling
A function is a named, reusable block of code.
```python
def greet(name):
    return "Hello, " + name

msg = greet("Sam")      # msg is "Hello, Sam"
```
- `name` is a **parameter** (the placeholder). `"Sam"` is the **argument** (the real value).
- `return` sends a value back and ends the function immediately.
- Without `return`, a function gives back `None`.

## 2. print vs return
`print` shows text on screen. `return` hands a value to the caller so it can be reused. Tests check what you **return**.

## 3. Default and keyword arguments
```python
def power(base, exp=2):
    return base ** exp

power(3)           # 9   (exp uses default)
power(3, 3)        # 27
power(exp=3, base=2)   # 8  (keyword arguments, any order)
```
Parameters with defaults must come after those without.

## 4. *args and **kwargs
```python
def total(*nums):          # nums is a tuple of all extra positional args
    return sum(nums)
total(1, 2, 3)             # 6

def show(**info):          # info is a dict of keyword args
    return info
show(a=1, b=2)             # {'a': 1, 'b': 2}
```

## 5. Returning several values
```python
def min_max(a, b):
    return min(a, b), max(a, b)    # a tuple
lo, hi = min_max(5, 2)             # unpacking
```

## 6. Scope
Variables created inside a function exist only there (**local**). A function can read outer (global) variables, but assigning to a name inside creates a new local one. Avoid globals; pass values in and return results.

## 7. Docstrings
The string right under `def` describes the function. `help(greet)` shows it.

## 8. Recursion (intro)
A function that calls itself on a smaller problem. Needs:
1. a **base case** (stops the recursion),
2. a **recursive case** (moves toward the base case).
```python
def countdown_sum(n):
    if n == 0:             # base case
        return 0
    return n + countdown_sum(n - 1)
```
Forgetting the base case gives `RecursionError`.

## 9. Mutable default trap
Never write `def f(x, items=[])`: the list is shared between calls. Use `items=None` and create a new list inside.

## Common mistakes
- Using `print` instead of `return`.
- Code after `return` never runs.
- Forgetting to call: `greet` is the function, `greet("Sam")` is the result.
- Mutable default arguments (above).
- Recursion without a base case.

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-03-functions -v`
