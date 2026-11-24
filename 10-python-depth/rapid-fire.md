# Python rapid-fire: 40 questions

Answer each out loud in 15 seconds or less, then check. Spans weeks 1-4 of `10-python-depth`.

## Functions and iteration (week 1)
1. **Why is `def f(x, items=[])` a bug?** Defaults are evaluated once at definition, so the same list is shared across calls. Use `None` and create inside.
2. **What is a closure?** A function that remembers variables from its enclosing scope after that scope has returned (`__closure__` cells).
3. **Why do lambdas in a loop all return the last value?** Closures capture variables, not values; bind with a default arg `lambda i=i: i`.
4. **What does `functools.wraps` do?** Copies `__name__`, `__doc__`, `__wrapped__` etc. from the wrapped function onto the wrapper so introspection/debugging still work.
5. **How does a decorator with arguments work?** Three layers: `deco(args)` returns a decorator, which takes `func` and returns the wrapper.
6. **`nonlocal` vs `global`?** `nonlocal` rebinds a variable in the nearest enclosing function; `global` rebinds a module-level name. Reading needs neither.
7. **Name the scope lookup order.** LEGB: Local, Enclosing, Global, Builtin.
8. **Generator vs list?** A generator yields lazily, O(1) memory, single pass; a list holds everything and is re-iterable.
9. **Iterable vs iterator?** Iterable has `__iter__` returning an iterator; iterator has `__next__` (raises `StopIteration`) and `__iter__` returning itself.
10. **What do `with` and `__enter__/__exit__` guarantee?** Cleanup runs even on exceptions; returning true from `__exit__` suppresses the exception. `contextlib.contextmanager` makes one from a generator.
11. **What does `lru_cache` require?** Hashable arguments and a pure function; unbounded growth with `maxsize=None`; `cache_clear()` to reset.
12. **`*args` / `**kwargs`?** Collect extra positional args into a tuple / keyword args into a dict; also used to unpack at call sites.

## Data model and memory (week 2)
13. **`is` vs `==`?** `is` compares identity (same object), `==` compares value via `__eq__`. Use `is` for `None`.
14. **Shallow vs deep copy?** Shallow copies the container but shares inner objects; `copy.deepcopy` recursively copies (handling cycles).
15. **Which types are hashable?** Immutable ones (int, str, tuple of hashables, frozenset); lists/dicts/sets are not. Equal objects must have equal hashes.
16. **How does CPython free memory?** Reference counting immediately at zero, plus a cyclic garbage collector for reference cycles.
17. **What does `__slots__` do?** Replaces the per-instance `__dict__` with fixed fields: less memory, faster attribute access, no arbitrary new attributes.
18. **Are dicts ordered?** Yes, insertion-ordered (guaranteed since 3.7); average O(1) lookups via a hash table.
19. **Is `sorted` stable?** Yes; equal keys keep original order, which enables multi-key sorts by sorting in passes.
20. **`defaultdict` vs `Counter` vs `deque`?** Missing-key factory dict; multiset counting with `most_common`; O(1) appends/pops at both ends.
21. **What does `@dataclass` generate?** `__init__`, `__repr__`, `__eq__` (and ordering/hash with options); `frozen=True` for immutability; use `field(default_factory=list)` for mutable defaults.
22. **`Protocol` vs ABC?** Protocol is structural (duck typing checked statically); ABC is nominal (must inherit/register).
23. **What does `Optional[int]` mean?** `int | None`; it does not mean the argument is optional. Narrow with `if x is not None`.
24. **What is a descriptor?** An object with `__get__`/`__set__`/`__delete__` stored on a class; it powers properties, methods and `__slots__`.
25. **When use `Enum`?** A closed set of named constants with identity and iteration, instead of magic strings/ints.

## Concurrency (week 3)
26. **What is the GIL?** A CPython lock so only one thread runs Python bytecode at a time; threads still help for I/O (the lock is released while waiting). 3.13+ has an optional free-threaded build.
27. **Threads, processes or asyncio?** I/O-bound with few connections: threads; I/O-bound at massive scale: asyncio; CPU-bound: multiprocessing / process pool.
28. **What is a race condition and how to prevent it?** Outcome depends on interleaving (e.g. `counter += 1` is read-modify-write). Use a `Lock`, a queue, or avoid shared mutable state.
29. **`asyncio.gather` vs `create_task`?** `gather` awaits several awaitables and returns results in order; `create_task` schedules a coroutine to run concurrently right away. `TaskGroup` adds structured cancellation.
30. **Why does `time.sleep` in an `async def` hurt?** It blocks the whole event loop. Use `await asyncio.sleep` or `run_in_executor`/`to_thread` for blocking calls.
31. **How do you cancel a task / add a timeout?** `task.cancel()` raises `CancelledError` at the next await (re-raise it); `asyncio.timeout()` / `wait_for` for deadlines.
32. **What does `async def` vs `def` do in FastAPI?** `async def` handlers run on the event loop (must not block); plain `def` handlers run in a threadpool.
33. **What limits concurrency in asyncio?** `asyncio.Semaphore` caps simultaneous operations (e.g. 10 outbound requests).

## Quality and tooling (week 4)
34. **Fixture vs parametrize?** Fixture provides setup/objects to tests; parametrize runs one test over many inputs.
35. **Where do you `patch`?** Where the name is looked up (the consumer module), not where it is defined.
36. **`raise X from e`?** Explicitly chains the cause; `__cause__` shows in the traceback. `from None` suppresses it.
37. **Why `logger.info("a %s", x)` not an f-string?** Formatting is deferred until the record is actually emitted, and log aggregators can group by template.
38. **What is a venv and why?** An isolated environment with its own interpreter links and site-packages so projects don't clash on versions.
39. **How to benchmark reliably?** `timeit.repeat`, take the minimum, realistic inputs, profile with `cProfile` before optimising.
40. **What do ruff and mypy catch?** ruff: lint/format/import issues and common bugs; mypy: type inconsistencies from annotations, before running code.
