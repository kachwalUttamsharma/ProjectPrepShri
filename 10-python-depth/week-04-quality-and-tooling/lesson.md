# Week 4: Quality and tooling

Interviewers (and teammates) judge you by how you test, fail, log, ship and measure code, not just by whether it works once.

## 1. pytest essentials
```python
def test_add():
    assert add(2, 3) == 5          # plain assert; pytest rewrites it to show details

import pytest
with pytest.raises(ValueError, match="bad"):   # assert an exception (and its message regex)
    parse("x")
assert 0.1 + 0.2 == pytest.approx(0.3)         # floats: never use ==
```
**Fixtures** = reusable setup, injected by argument name.
```python
@pytest.fixture
def cart():
    c = Cart()
    yield c          # code after yield is teardown
    c.close()

def test_empty(cart):
    assert cart.total() == 0
```
Scopes: `function` (default), `class`, `module`, `session`. `conftest.py` shares fixtures across files with no imports. Built-ins: `tmp_path` (fresh temp dir), `monkeypatch`, `caplog`, `capsys`.

**parametrize** runs one test over many inputs (each is its own test id):
```python
@pytest.mark.parametrize("text,expected", [("1", 1), ("42", 42)])
def test_parse(text, expected):
    assert parse(text) == expected
```
Other marks: `skip`, `skipif`, `xfail`, custom marks (register them to avoid warnings). Run: `pytest -q`, `-x` (stop at first failure), `-k name`, `-v`, `--lf` (last failed), `-s` (show prints), `--pdb`.

## 2. Mocking
`unittest.mock.Mock` records calls and returns whatever you configure.
```python
from unittest.mock import Mock, patch
client = Mock()
client.get.return_value.status_code = 200
client.get.return_value.json.return_value = {"name": "Ada"}
...
client.get.assert_called_once_with("/users/7")
client.get.side_effect = TimeoutError      # or a list of results/exceptions
```
`patch` swaps a name **where it is looked up, not where it is defined**:
```python
# app.py does `from requests import get` -> patch "app.get", NOT "requests.get"
with patch("app.get") as m:
    m.return_value.status_code = 200
```
`MagicMock` also supports magic methods (`__len__`, `__enter__`). `autospec=True` / `create_autospec` makes the mock reject calls that do not match the real signature (catches typos and wrong arg counts).

**monkeypatch** (pytest) is simpler for env vars, attributes, cwd, dict items; undone automatically:
```python
monkeypatch.setenv("APP_PORT", "9000")
monkeypatch.setattr(module, "func", lambda: 42)
monkeypatch.delenv("X", raising=False)
```
Prefer **dependency injection** (pass the client in) over patching: simpler tests, fewer surprises. Mock the boundary (network, clock, disk), not your own logic. Over-mocking makes tests pass while the code is broken.

Good tests: fast, deterministic (no sleeps, no real network, inject clocks), one behaviour each, named for the behaviour, arrange-act-assert.

## 3. Exception design
- Catch the narrowest type you can handle. Never bare `except:`; `except Exception:` only at boundaries (top-level handler, worker loop) and log with traceback.
- Create a base exception per library/app, then subclass: callers can catch `AppError` or something specific.
```python
class AppError(Exception):
    def __init__(self, message, code=500):
        super().__init__(message)
        self.code = code
class NotFoundError(AppError): ...
```
- **Chaining**: `raise Domain(...) from exc` sets `__cause__` (explicit translation). Raising inside `except` without `from` sets `__context__` implicitly. `from None` hides the original.
- `try / except / else / finally`: `else` runs only if no exception (keep the `try` body tiny); `finally` always runs (cleanup). Prefer `with` for cleanup.
- EAFP ("ask forgiveness") is idiomatic: `try: d[k] except KeyError`. LBYL for cheap checks and race-free conditions.
- `raise` (bare) re-raises preserving traceback. `ExceptionGroup` / `except*` (3.11+) handle several simultaneous errors (e.g. `asyncio.TaskGroup`).
- Don't use exceptions for hot-path control flow when a simple check is clearer; do use `StopIteration`-style protocols where they exist.
- `add_note()` (3.11+) attaches context to an exception without changing its type.

## 4. Logging
```python
import logging
logger = logging.getLogger(__name__)      # one per module; never the root logger in libraries

logger.info("processed order %s", order_id)   # lazy formatting: not an f-string
logger.exception("failed")                    # ERROR + traceback; use inside except
```
Levels: DEBUG < INFO < WARNING < ERROR < CRITICAL. Pieces: **Logger** (named, hierarchical: `a.b` propagates to `a`), **Handler** (where: stream, file, rotating), **Formatter** (how), **Filter**. Application entrypoint configures once:
```python
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
```
Libraries add only `NullHandler` and let the app decide. Production: structured (JSON) logs, correlation/request ids (`contextvars` + filter), no secrets/PII, don't log in tight loops. Duplicate lines usually mean a handler added twice or propagation to root as well.

## 5. Packaging, venv, pip, pyproject
- **venv** isolates dependencies per project: `python -m venv .venv`, `source .venv/bin/activate`. Never `pip install` into system Python. Always `python -m pip` so you know which interpreter.
- `pip install -r requirements.txt` (pinned for apps), `pip freeze`, `pip install -e .` (editable install of your own package). Tools like `uv`/`pip-tools`/`poetry` add lockfiles and speed.
- Libraries declare loose ranges (`requests>=2.31,<3`); apps pin exact versions (reproducible deploys). Separate dev dependencies (pytest, ruff, mypy).
- `pyproject.toml` is the single config file (PEP 517/518/621):
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "mypkg"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["httpx>=0.27"]
[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
[project.scripts]
mycli = "mypkg.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
[tool.ruff]
line-length = 100
[tool.mypy]
strict = true
```
- Layout: `src/mypkg/__init__.py` + `tests/`. A directory with `__init__.py` is a package; `if __name__ == "__main__":` guards script entry; `python -m mypkg` runs `__main__.py`.
- Import gotchas: circular imports (move import inside function or restructure), shadowing stdlib names (`random.py`), relative vs absolute imports (prefer absolute).

## 6. Profiling and performance
Measure first; guessing is usually wrong.
```python
import timeit
timeit.timeit("sum(range(1000))", number=10_000)
timeit.repeat(..., repeat=5, number=...)   # take the MIN: noise only slows runs
```
CLI: `python -m timeit "..."`. `time.perf_counter()` for manual timing (monotonic, high resolution).
```python
python -m cProfile -s cumtime script.py       # which functions take time
# programmatic: cProfile.Profile() + pstats.Stats(pr).sort_stats("cumtime").print_stats(10)
```
`tracemalloc` for memory allocations; `sys.getsizeof` is shallow only. Sampling profilers (py-spy) attach to running processes with low overhead. `line_profiler` shows per-line cost.

Idioms that matter:
- Right data structure: `x in set/dict` is O(1), `x in list` is O(n). `deque` for queues (`list.pop(0)` is O(n)). `bisect` on sorted data.
- `"".join(parts)` instead of `s += part` in a loop.
- Comprehensions / generator expressions beat manual append loops; generators avoid materialising big data. `sum(x for x ...)` not `sum([...])`.
- Hoist invariants out of loops; bind hot globals/methods to locals only when profiling says so.
- `functools.lru_cache` for pure repeated calls; `collections.Counter`/`defaultdict` over manual dict code.
- Use builtins (`sum`, `min`, `sorted(key=)`, `any`/`all`) which are C-speed. For numeric work use numpy; for CPU-bound parallelism use multiprocessing (week 3).
- Don't optimise before you have a profile; algorithmic wins (O(n^2) to O(n log n)) dwarf micro-tuning.

## 7. Style, linting, typing tools
- **PEP 8**: 4-space indent, `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants, imports grouped stdlib / third-party / local, line length ~88-100. **PEP 257**: docstrings.
- **ruff**: one very fast tool for lint + import sorting + (via `ruff format`) formatting. `ruff check .`, `ruff check --fix .`, `ruff format .`. Common rules: `E/F` (pycodestyle/pyflakes), `I` (isort), `B` (bugbear: mutable defaults, bare except), `UP` (modernise syntax).
- **mypy** (or pyright): static type checks from annotations, run in CI. `mypy src/`; `--strict` for new code; adopt gradually with `# type: ignore[code]` sparingly. Types are not enforced at runtime.
- Wire it together: pre-commit hooks or CI running `ruff check`, `ruff format --check`, `mypy`, `pytest`. A green pipeline is the team contract.
- Coverage (`pytest --cov`) shows untested lines, not test quality.

## Common mistakes
- Patching where a thing is defined instead of where it is used.
- `assert` on a tuple (`assert (x, "msg")` is always true); using `assert` for runtime validation (stripped under `-O`).
- Catching `Exception` and silently passing; swallowing the traceback (use `logger.exception` or `raise ... from`).
- f-strings in logging calls (formats even when the level is disabled).
- Adding handlers inside a function called repeatedly (duplicate log lines).
- Tests depending on order, wall-clock time, or network.
- Benchmarking once, or taking the mean of noisy runs.

## Your task
Fill in `exercises.py`, then run `../../.venv/bin/pytest -q` in this folder. After that, read `interview-qa.md` aloud, then `../rapid-fire.md`.
