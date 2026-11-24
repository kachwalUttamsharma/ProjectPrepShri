# Week 1 interview Q&A: functions deep-dive

Answer each one out loud first, then compare. Aim for 30-60 seconds each.

**1. What is a closure?**
A function that remembers variables from the enclosing scope it was defined in, even after that scope has returned. Python stores them in cells (`fn.__closure__`). Use `nonlocal` to rebind them.

**2. Explain LEGB.**
Name lookup order: Local, Enclosing, Global, Built-in. Assignment anywhere in a function makes the name local for the entire function, so reading it earlier gives `UnboundLocalError`. `global`/`nonlocal` change where assignment binds.

**3. Why does `[lambda: i for i in range(3)]` return `[2, 2, 2]` when called, and how do you fix it?**
Closures capture the variable `i`, not its value; all lambdas see the final `i`. Fix with a default argument (`lambda i=i: i`) or `functools.partial`, or a factory function that takes `i` as a parameter.

**4. What's wrong with `def f(x, items=[])`?**
The default is evaluated once at definition time, so every call that omits `items` shares the same list. Use `items=None` and create the list inside. Defaults are stored in `f.__defaults__`.

**5. What does `@decorator` desugar to?**
`f = decorator(f)` at definition time. Stacked decorators apply bottom-up (`@a @b def f` is `a(b(f))`), and execute outermost-first when called.

**6. Why use `functools.wraps`?**
It copies `__name__`, `__doc__`, `__module__`, `__dict__`, and sets `__wrapped__` so the wrapper looks like the original. Without it, debugging, logging, docs, `inspect.signature` and frameworks like FastAPI/pytest see `wrapper`.

**7. How do you write a decorator that takes arguments?**
A factory returning a decorator returning a wrapper: three nested functions. `@retry(3)` means `f = retry(3)(f)`. Common bug: using `@retry` without parentheses.

**8. What is a class decorator, and how does it differ from a class-based decorator?**
A class decorator receives a class and returns a class (or other object), e.g. registering or adding methods. A class-based decorator is a class with `__call__` used to decorate functions, often holding state such as call counts.

**9. How does a `with` statement work?**
It calls `__enter__` (its return is bound by `as`), runs the block, then calls `__exit__(exc_type, exc, tb)` always. If `__exit__` returns truthy the exception is suppressed; otherwise it propagates.

**10. How does `@contextlib.contextmanager` work and what's the pitfall?**
The generator runs up to `yield` (enter), the yielded value is bound by `as`, and the code after `yield` is the exit. If the block raises, the exception is thrown into the generator at `yield`, so you need `try/finally` for guaranteed cleanup.

**11. Iterable vs iterator vs generator?**
Iterable has `__iter__` returning an iterator. An iterator has `__next__` and `__iter__` returning itself; it is consumed once. A generator is an iterator created by a function with `yield` or a generator expression.

**12. What does `for x in obj` do under the hood?**
Calls `iter(obj)`, then repeatedly `next()` on the result until `StopIteration` is raised, which ends the loop silently.

**13. Why use generators? Give a use case.**
Lazy evaluation and O(1) memory: processing a huge log file line by line, streaming rows from a DB, infinite sequences, pipelines of composable stages. Downside: single pass, no `len` or indexing.

**14. What does `yield from` do?**
Delegates to a sub-iterator, forwarding values (and `send`/`throw`), and evaluates to the sub-generator's return value. Cleaner than a manual loop for flattening and for composing generators.

**15. What is `lru_cache` and what are its limits?**
Memoization with least-recently-used eviction (`maxsize`). Arguments must be hashable, the function should be pure, it holds references to arguments/results (can leak, e.g. methods keep `self`), and `cache_info()` / `cache_clear()` expose stats. `@cache` is the unbounded version.

**16. `functools.partial` vs a lambda?**
`partial(f, a, b=1)` creates a callable with arguments pre-filled; it's picklable, introspectable (`.func`, `.args`, `.keywords`) and doesn't suffer late binding since it stores values immediately.

**17. What does `reduce` do? When would you avoid it?**
Folds an iterable left to right with a binary function: `reduce(f, [a,b,c]) == f(f(a,b),c)`. Often `sum`, `max`, `any`, or a loop is clearer; give an initial value so empty input works.

**18. Why does `itertools.groupby` give surprising results?**
It groups only *consecutive* equal keys, so sort by the same key first. Also each group is a lazy view tied to the iterator; consume it before advancing.

**19. In what order are arguments evaluated in `f(a(), b(), c=d())`?**
First the expression `f`, then arguments left to right (positional, then keyword): `f`, `a()`, `b()`, `d()`, then the call. Same left-to-right rule in tuples and in operands like `x() + y()`.

**20. Is Python pass by value or by reference?**
Neither exactly: "pass by object reference" (call by assignment). The parameter is a new name bound to the same object. Mutating a mutable argument is visible outside; rebinding the parameter is not.
