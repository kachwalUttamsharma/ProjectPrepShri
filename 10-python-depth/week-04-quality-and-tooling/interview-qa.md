# Week 4 interview Q&A: quality and tooling

**1. What is a pytest fixture and how does it differ from setUp/tearDown?**
A function marked `@pytest.fixture` whose return/yield value is injected into tests by parameter name. Code after `yield` is teardown. Unlike xUnit setUp, fixtures are explicit per test, composable (fixtures can request fixtures), scoped (function/class/module/session) and shareable via `conftest.py`.

**2. How does `parametrize` work and why use it?**
`@pytest.mark.parametrize("a,b", [...])` generates one independent test per tuple, each with its own id and failure report. It removes copy-paste tests and loops inside tests (where the first failure hides the rest).

**3. `Mock` vs `MagicMock` vs `patch` vs `monkeypatch`?**
`Mock` is a configurable stand-in recording calls. `MagicMock` adds magic-method support. `patch` temporarily replaces a named object (context manager/decorator). `monkeypatch` is pytest's fixture for setting attributes/env/dict items, auto-undone. Behaviourally similar; use monkeypatch for simple swaps, Mock for verifying interactions.

**4. Where do you patch?**
Where the name is looked up at call time, not where defined. If `app.py` does `from requests import get`, patch `app.get`. Patching `requests.get` leaves `app.get` pointing at the original.

**5. What is `autospec` and why use it?**
`patch(..., autospec=True)` or `create_autospec(obj)` builds a mock matching the real object's signature, so wrong argument counts or misspelled methods raise errors. Plain mocks accept anything and let broken code pass.

**6. How do you make tests deterministic around time, randomness and I/O?**
Inject the dependency (clock, RNG with seed, client, path) or patch the boundary. Use `tmp_path` for files, fake timers instead of sleeping, seeded `random.Random(0)`, and never hit real network. Flaky tests are worse than no tests.

**7. When should you NOT mock?**
When you would be mocking your own logic (test asserts nothing real), or when a cheap real object exists (in-memory SQLite, `io.StringIO`, a fake). Mock at architectural boundaries; prefer fakes for stateful collaborators.

**8. Explain `try / except / else / finally`.**
`except` handles listed errors; `else` runs only if the `try` raised nothing (keeps the `try` body minimal); `finally` always runs, even on return/raise, for cleanup. A `return` in `finally` swallows exceptions, avoid it.

**9. `raise X from Y` vs plain `raise X` inside `except`?**
`from Y` sets `__cause__` explicitly ("the direct cause"). Plain raise inside except sets `__context__` ("during handling of...") implicitly. `from None` suppresses the chain. Bare `raise` re-raises the current exception with its traceback intact.

**10. How would you design exceptions for a library?**
One base class (`MyLibError`) so callers can catch everything from you; specific subclasses per failure mode carrying useful attributes (code, resource id); keep them in one module; wrap low-level errors (`from exc`) so internals don't leak. Don't subclass `BaseException`; don't use exceptions for ordinary control flow.

**11. Why not `except:` or `except Exception: pass`?**
Bare except also catches `KeyboardInterrupt`/`SystemExit` and hides bugs. Swallowing hides failures. Catch specific errors; at boundaries catch `Exception`, log with `logger.exception`, and respond or re-raise.

**12. Why `logging` instead of `print`?**
Levels, timestamps, structured formatting, multiple destinations, per-module configuration, and the app (not the library) controls output. Use `logger = logging.getLogger(__name__)`, `logger.info("x %s", val)` (lazy), `logger.exception` in handlers.

**13. How does logger hierarchy and propagation work?**
Names are dotted (`a.b.c`); a record handled at `a.b.c` also propagates up to handlers on `a.b`, `a`, and root unless `propagate=False`. Duplicate output usually comes from a handler on both a child and the root, or from adding a handler on every call.

**14. How do you manage Python dependencies and environments?**
One venv per project (`python -m venv .venv`), dependencies declared in `pyproject.toml` (or requirements), apps pinned for reproducibility (lockfile / `pip freeze` / uv), libraries with compatible ranges, dev dependencies separated. Always `python -m pip` to target the right interpreter.

**15. What goes in `pyproject.toml`?**
`[build-system]` (backend), `[project]` metadata (name, version, requires-python, dependencies, optional-dependencies, scripts/entry points), and tool configuration (`[tool.pytest.ini_options]`, `[tool.ruff]`, `[tool.mypy]`). It replaced setup.py/setup.cfg/most dotfiles.

**16. How do you find why code is slow?**
Reproduce with a benchmark, profile (`python -m cProfile -s cumtime`, py-spy for live processes, line_profiler for hot functions), fix the biggest contributor (usually algorithm/data structure or I/O), re-measure. Use `timeit` with `repeat` and take the minimum for micro-benchmarks.

**17. Name five Python performance idioms.**
Use sets/dicts for membership; `"".join` over `+=`; generators for large streams; `deque` for FIFO; `lru_cache` for pure functions; comprehensions and builtins (C speed); `sorted(key=...)` over comparator funcs; avoid repeated attribute lookups only after profiling shows need.

**18. `timeit` pitfalls?**
Single runs are noisy; use `repeat` and take the min. Setup code must not be inside the timed statement. GC is disabled during timing by default. Measure realistic input sizes; micro-benchmarks can mislead about real workloads.

**19. What do ruff and mypy each do?**
ruff: linter/import sorter/formatter (replaces flake8, isort, black, pyupgrade) catching style issues and bugs such as unused imports, mutable defaults, bare except. mypy: static type checker reading annotations; finds `None` misuse, wrong argument types, missing returns. Neither runs your code. Run both in CI.

**20. What does test coverage tell you, and what doesn't it?**
Which lines/branches executed during tests. It does not prove assertions are meaningful; 100% coverage with weak asserts is false comfort. Use it to find untested paths, add branch coverage, and focus on critical behaviour.
