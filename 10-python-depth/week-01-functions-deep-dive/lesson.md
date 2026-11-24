# Week 1: Functions deep-dive

Goal: by the end you can explain and write closures, decorators (plain, with arguments, class decorators), context managers, generators and custom iterators, and use `functools`/`itertools` fluently. These are the "Python depth" questions that separate a strong candidate from someone who only knows syntax. Budget ~8 hours: lesson + experiments in the REPL (3h), exercises (4h), `interview-qa.md` out loud (1h).

## 1. Functions are objects
Functions are first-class: you can store them in variables, pass them as arguments, return them, and attach attributes.
```python
def greet(name): return f"hi {name}"
f = greet                 # no call, just another name for the same object
fs = {"g": greet}         # store in a dict
greet.calls = 0           # attributes on functions are legal (we use this for decorators)
```
`def` is an executable statement: it runs at definition time and binds a name. Defaults and decorators are evaluated at that moment too.

## 2. Arguments and evaluation order
```python
def f(a, b=2, *args, c, d=4, **kwargs): ...
#      positional  *args  keyword-only   **kwargs
def g(a, b, /, c, *, d): ...     # a, b positional-only; d keyword-only
```
- Arguments are evaluated **left to right**, positional first, then keywords, at call time: `f(a(), b(), c=c())` calls a, b, c in that order. The function is looked up (the expression before the parentheses) **before** its arguments are evaluated.
- Python passes **object references by value** ("call by assignment"): the parameter name is bound to the same object. Mutating it is visible to the caller; rebinding the name is not.
- Unpacking: `f(*lst, **dct)`; `[*a, *b]`, `{**d1, **d2}` (later keys win).

### Mutable default arguments (top interview trap)
```python
def add(x, bucket=[]):      # the list is created ONCE, when `def` runs
    bucket.append(x); return bucket
add(1); add(2)              # [1, 2]  (shared state!)
def add(x, bucket=None):    # fix: None sentinel, create inside
    if bucket is None: bucket = []
```
You can see the stored default in `add.__defaults__`. Use a sentinel `object()` when `None` is itself a valid value.

## 3. Scope: LEGB
Name lookup order: **L**ocal -> **E**nclosing function -> **G**lobal (module) -> **B**uilt-in.
```python
x = "global"
def outer():
    x = "enclosing"
    def inner():
        print(x)        # finds "enclosing" (E)
    inner()
```
- Assigning to a name anywhere in a function makes it **local for the whole function**: reading it before assignment raises `UnboundLocalError`.
- `global x` rebinds a module-level name; `nonlocal x` rebinds a name in the nearest enclosing function.
- Class bodies are not enclosing scopes for methods. Comprehensions have their own scope (the loop variable does not leak).

## 4. Closures
A closure is a function plus the variables it captured from an enclosing scope. Python keeps them in "cells" (`fn.__closure__`).
```python
def make_counter():
    n = 0
    def counter():
        nonlocal n          # without this: UnboundLocalError
        n += 1
        return n
    return counter
```
**Late binding trap**: closures capture the *variable*, not the value at that moment.
```python
fs = [lambda: i for i in range(3)]
[f() for f in fs]           # [2, 2, 2]
fs = [lambda i=i: i for i in range(3)]   # [0, 1, 2]  (default evaluated now)
```

## 5. Decorators
`@d` above `def f` is exactly `f = d(f)`.
```python
import functools

def timed(func):
    @functools.wraps(func)            # copies __name__, __doc__, __wrapped__...
    def wrapper(*args, **kwargs):
        # before
        result = func(*args, **kwargs)
        # after
        return result
    return wrapper
```
Without `functools.wraps`, `f.__name__` becomes `"wrapper"`, docs and introspection (and FastAPI's signature inspection!) break.

**Decorators with arguments** add one more level (a decorator *factory*):
```python
def retry(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*a, **k): ...
        return wrapper
    return decorator

@retry(3)          # == f = retry(3)(f)
def fetch(): ...
```
**Stacking**: `@a @b def f` == `f = a(b(f))`; b wraps first (innermost), a runs first at call time.

**Class decorators** take a class and return a class (or anything):
```python
def register(cls):
    REGISTRY[cls.__name__] = cls
    return cls
```
**Class-based decorators** implement `__call__` (and `functools.update_wrapper(self, func)` for metadata). Decorating methods: the wrapper is a plain function, so it becomes a method automatically via the descriptor protocol; the first `*args` item is `self`.

Real examples you already use: `@app.get(...)` (registers and returns the function), `@property`, `@staticmethod`, `@functools.lru_cache`, `@pytest.fixture`.

## 6. Context managers
`with` guarantees cleanup. The protocol:
```python
class Timer:
    def __enter__(self): self.start = time.perf_counter(); return self
    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self.start
        return False        # True would SUPPRESS the exception
```
`__exit__` receives the exception info (or `None, None, None`). Return a truthy value only when you deliberately swallow the error.

The shortcut, `contextlib.contextmanager`:
```python
from contextlib import contextmanager
@contextmanager
def opened(path):
    f = open(path)
    try:
        yield f             # value bound by `as`
    finally:
        f.close()           # runs on success AND exception
```
Without `try/finally`, an exception in the block is re-raised at the `yield` and cleanup is skipped. Other tools: `contextlib.suppress(KeyError)`, `ExitStack` (dynamic number of contexts), `closing`, `redirect_stdout`, and `asynccontextmanager` (week 3). Multiple managers: `with a() as x, b() as y:`.

## 7. Iterators and generators
- **Iterable**: has `__iter__` returning an iterator (list, dict, str, file).
- **Iterator**: has `__next__` (raises `StopIteration` at the end) and `__iter__` returning itself. One-shot.
- `for x in obj` is: `it = iter(obj)`, then `next(it)` until `StopIteration`.

A **generator function** has `yield`; calling it returns a generator (an iterator) without running the body. Execution pauses at each `yield` and keeps local state.
```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1
```
- Generators are lazy and use O(1) memory: great for large files and streams.
- Generator expression: `sum(x*x for x in range(10**6))` (parentheses, not brackets).
- `yield from sub` delegates to a sub-iterator.
- `send()` / `close()` / `throw()` make generators coroutines (the ancestor of `async`).
- `return value` inside a generator ends it; the value rides on `StopIteration.value`.
- A generator can only be consumed once. `list(g)` twice gives `[...]` then `[]`.
- A list comprehension builds everything now; a generator computes on demand.

## 8. functools
```python
from functools import lru_cache, cache, partial, reduce, wraps, cached_property, singledispatch, total_ordering

@lru_cache(maxsize=256)     # memoize; args must be hashable; fn.cache_info(), fn.cache_clear()
def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)

pow2 = partial(pow, exp=2)  # freeze arguments
reduce(lambda a, b: a * b, [1, 2, 3, 4])   # 24 (fold left)
```
`@cache` = unbounded `lru_cache`. Caveats: caching methods keeps `self` alive (memory leak) and caches mutable results by reference. `cached_property` computes once per instance.

## 9. itertools (lazy building blocks)
| Tool | Example |
|---|---|
| `chain(a, b)` / `chain.from_iterable(xs)` | concatenate / flatten one level |
| `islice(it, 5)` / `islice(it, 2, 8, 2)` | slice any iterator |
| `count(10)`, `cycle("ab")`, `repeat(0, 3)` | infinite/finite sources |
| `groupby(data, key)` | group **consecutive** items; sort first for full grouping |
| `product(a, b)`, `permutations(x, r)`, `combinations(x, r)` | combinatorics |
| `accumulate(xs)` | running totals |
| `zip_longest(a, b, fillvalue=0)` | zip without truncating |
| `pairwise(xs)` | (x0,x1), (x1,x2), ... (3.10+) |
| `batched(xs, n)` | chunks as tuples (3.12+) |
| `tee(it, 2)` | independent copies of an iterator |
| `takewhile`, `dropwhile`, `filterfalse`, `starmap` | predicate helpers |

## Common mistakes
- Mutable default arguments; closures in loops (late binding).
- Forgetting `functools.wraps`, or forgetting `return func(...)` in the wrapper (function now returns `None`).
- `@retry` instead of `@retry(3)` for a decorator factory (the function ends up passed as `times`).
- `groupby` on unsorted data; reusing an exhausted generator/iterator.
- `@contextmanager` without `try/finally`; returning `True` from `__exit__` by accident.
- `lru_cache` on functions with unhashable arguments (list/dict) -> `TypeError`.

## Experiments to run in the REPL
1. `def f(x, l=[]): ...` then inspect `f.__defaults__` after two calls.
2. Print `make_counter().__closure__[0].cell_contents` after a few calls.
3. Stack two decorators that print "enter"/"exit" and observe the order.
4. `g = (i for i in range(3)); list(g); list(g)`.
5. `fib.cache_info()` before and after `fib(30)`.

## Your task
Fill in `exercises.py`, then run `../../.venv/bin/pytest -q` from this folder. Then answer every question in `interview-qa.md` out loud without looking.
