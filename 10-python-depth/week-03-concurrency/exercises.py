"""Week 3 exercises: concurrency (asyncio + threads).

Replace each `...` with your code. Tests use asyncio.run (no pytest-asyncio)
and never touch the network. Run them with:
    ../../.venv/bin/pytest -q
"""
import asyncio
import queue
import threading
import contextlib  # handy for suppress()


# Exercise 1 -------------------------------------------------------------
async def gather_in_order(*coros):
    """Run all coroutines concurrently; return their results as a list in the
    SAME order as the arguments (not completion order).
    Hint: asyncio.gather returns a list in argument order.
    """
    ...


# Exercise 2 -------------------------------------------------------------
async def bounded_gather(factories, limit):
    """`factories` is a list of zero-arg callables, each returning a coroutine.
    Run them all concurrently but never more than `limit` at the same time.
    Return results in input order.
    Hint: asyncio.Semaphore(limit) + `async with sem:` inside a small wrapper.
    """
    ...


# Exercise 3 -------------------------------------------------------------
async def with_timeout(coro, seconds, default=None):
    """Await `coro`; if it takes longer than `seconds`, cancel it and return
    `default` instead of raising.
    Hint: asyncio.wait_for raises asyncio.TimeoutError (alias of TimeoutError)
    and cancels the inner coroutine for you.
    """
    ...


# Exercise 4 -------------------------------------------------------------
async def cancel_task(task):
    """Cancel `task`, wait for it to finish unwinding (its finally blocks must
    run), swallow the CancelledError, and return True if the task ended up
    cancelled, False otherwise (e.g. it had already finished).
    Hint: task.cancel(); then `await task` inside contextlib.suppress(...);
    finally return task.cancelled().
    """
    ...


# Exercise 5 -------------------------------------------------------------
async def retry_async(factory, attempts):
    """`factory` is a zero-arg callable returning a fresh coroutine each call.
    Try up to `attempts` times; return the first successful result. If every
    attempt raises, re-raise the LAST exception. No sleeping between tries.
    Hint: a coroutine can only be awaited once, so call factory() each time.
    """
    ...


# Exercise 6 -------------------------------------------------------------
class AsyncResource:
    """Async context manager that records events in the shared list `log`:
      enter           -> appends "open:<name>" and returns self
      exit (ok)       -> appends "close:<name>"
      exit (exception)-> appends "error:<name>" then "close:<name>"
    It must NOT swallow exceptions.
    Hint: __aenter__ / __aexit__(self, exc_type, exc, tb); return False/None.
    """

    def __init__(self, name, log):
        ...

    async def __aenter__(self):
        ...

    async def __aexit__(self, exc_type, exc, tb):
        ...


# Exercise 7 -------------------------------------------------------------
async def async_batches(agen, size):
    """Async generator: consume the async iterator `agen` and yield lists of
    `size` items; the final list may be shorter. [1..5], size 2 -> [1,2] [3,4] [5]
    Hint: `async for`, a buffer list, and `yield` inside an `async def`.
    """
    ...


# Exercise 8 -------------------------------------------------------------
async def run_blocking(fn, *args):
    """Run the BLOCKING function fn(*args) in a worker thread so the event
    loop stays free, and return its result.
    Hint: asyncio.to_thread (or loop.run_in_executor(None, ...)).
    """
    ...


# Exercise 9 -------------------------------------------------------------
class ThreadSafeCounter:
    """Counter safe to use from many threads.
    increment(n=1) adds n; `value` (a property) returns the current total.
    Hint: `self._v += n` is read-modify-write, not atomic. Guard it with a
    threading.Lock.
    """

    def __init__(self):
        ...

    def increment(self, n=1):
        ...

    @property
    def value(self):
        ...


# Exercise 10 ------------------------------------------------------------
def worker_pool_queue(items, fn, n_workers):
    """Process `items` with exactly `n_workers` threads pulling jobs from a
    queue.Queue. Return [fn(item) ...] in INPUT order. Empty input -> [].
    Hint: enqueue (index, item) pairs, then one None sentinel per worker;
    workers loop `q.get()` until they see None; write results[index]; join all.
    """
    ...
