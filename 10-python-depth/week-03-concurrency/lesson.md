# Week 3: Concurrency

## 1. Three tools, three problems
- **Concurrency** = many tasks in progress (interleaved). **Parallelism** = tasks literally running at the same instant on several cores.
- **I/O-bound** work (HTTP, DB, disk) spends time waiting. **CPU-bound** work (parsing, math, image processing) spends time computing.

| Tool | Parallel CPU? | Overhead | Best for |
|---|---|---|---|
| `asyncio` | no (1 thread) | tiny | thousands of I/O waits (sockets, HTTP, DB with async driver) |
| `threading` | no for Python bytecode (GIL), yes while blocked in I/O or C code that releases the GIL | medium | blocking libraries, a few dozen I/O jobs |
| `multiprocessing` / `ProcessPoolExecutor` | yes | high (spawn, pickling) | CPU-bound work |

Rule of thumb: waiting on I/O with an async library -> asyncio; waiting on I/O with a blocking library -> threads; burning CPU -> processes.

## 2. The GIL
CPython has a Global Interpreter Lock: only one thread executes Python bytecode at a time (reference counting is not thread-safe without it). Consequences:
- Threads do NOT speed up CPU-bound pure-Python code.
- Threads DO help I/O: the GIL is released while waiting on sockets/files/`time.sleep`.
- The GIL does not make your code thread-safe: `x += 1` is several bytecodes and a thread switch can happen between them.
- Python 3.13+ has an experimental free-threaded build (no GIL); the default build still has it. Know this exists; don't rely on it.

## 3. Race conditions and locks
```python
import threading
lock = threading.Lock()
counter = 0
def inc():
    global counter
    with lock:            # read-modify-write is now atomic w.r.t. other lock users
        counter += 1
```
- Always `with lock:` (releases on exceptions).
- `RLock` can be re-acquired by the same thread. `Lock` cannot (deadlock).
- **Deadlock**: A holds L1 wants L2, B holds L2 wants L1. Fix: always acquire in a fixed global order, or use timeouts.
- Prefer sharing nothing: pass data through a `queue.Queue` instead of shared variables.

## 4. queue module (producer/consumer)
```python
import queue, threading
q = queue.Queue()                  # thread-safe, blocking get/put
def worker():
    while True:
        job = q.get()
        if job is None:            # sentinel = "no more work"
            return
        ...
```
`Queue(maxsize=n)` gives backpressure (`put` blocks when full). `q.task_done()` + `q.join()` waits until all jobs are processed. `asyncio.Queue` is the same idea for coroutines (not thread-safe).

## 5. concurrent.futures
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, urls))            # ordered results
    futs = [pool.submit(fetch, u) for u in urls]
    for f in as_completed(futs):                     # completion order
        print(f.result())                            # re-raises worker exception
```
A `Future` is a promise of a result: `.result()`, `.exception()`, `.cancel()`, `.done()`. Same API for processes. With processes, functions and arguments must be picklable (top-level functions, not lambdas) and on macOS/Windows use `if __name__ == "__main__":`.

## 6. asyncio basics
- `async def f()` returns a **coroutine object**; nothing runs until it is awaited or scheduled.
- `await x` suspends the current coroutine and hands control to the **event loop**, which runs something else until `x` is ready. Switching happens ONLY at `await` points (cooperative).
- `asyncio.run(main())` creates a loop, runs `main`, closes the loop. Call it once at the top level.
```python
import asyncio
async def fetch(i):
    await asyncio.sleep(0.1)      # stands in for network I/O
    return i
async def main():
    return await asyncio.gather(fetch(1), fetch(2), fetch(3))   # ~0.1s, not 0.3s
print(asyncio.run(main()))        # [1, 2, 3]
```
- **Task** = a coroutine scheduled to run in the background: `t = asyncio.create_task(coro())`. Keep a reference (the loop only keeps a weak one) and await it later.
- `gather(*aws)` returns results in argument order. By default the first exception propagates (others keep running); `return_exceptions=True` returns exceptions as values.
- **TaskGroup** (3.11+) is structured concurrency: `async with asyncio.TaskGroup() as tg: tg.create_task(...)`. If one task fails, the siblings are cancelled and errors surface as an `ExceptionGroup` (`except*`). Prefer it over bare `create_task`.

## 7. Timeouts and cancellation
```python
try:
    r = await asyncio.wait_for(slow(), timeout=1.0)
except TimeoutError:         # asyncio.TimeoutError is TimeoutError since 3.11
    ...
async with asyncio.timeout(1.0):      # 3.11+, scope-based
    await slow()
```
- `task.cancel()` schedules a `CancelledError` thrown into the coroutine at its next `await`. The coroutine can run `finally` blocks for cleanup. Then `await task` (suppress `CancelledError`) to wait for cleanup to finish.
- **Never swallow `CancelledError`** without re-raising; it breaks timeouts and shutdown. Catch `Exception`, not `BaseException` (`CancelledError` is a `BaseException`).
- `asyncio.shield(aw)` protects an inner awaitable from outer cancellation (rarely needed).

## 8. Limiting concurrency
```python
sem = asyncio.Semaphore(10)
async def limited(x):
    async with sem:
        return await call_api(x)
await asyncio.gather(*(limited(x) for x in xs))
```
Launching 10 000 requests at once exhausts sockets and rate limits; a semaphore caps in-flight work. `asyncio.Lock`, `Event`, `Condition`, `Queue` mirror the threading primitives but are for coroutines in ONE loop.

## 9. Async context managers and generators
```python
class Conn:
    async def __aenter__(self): await self.open(); return self
    async def __aexit__(self, et, ev, tb): await self.close()    # falsy return = don't swallow

async with Conn() as c: ...

async def ticker(n):             # async generator
    for i in range(n):
        await asyncio.sleep(0)
        yield i
async for i in ticker(3): ...
```
`@contextlib.asynccontextmanager` builds an async CM from an async generator with one `yield`. Async comprehensions: `[x async for x in agen()]`.

## 10. Blocking code inside async: the #1 bug
Any blocking call (`time.sleep`, `requests.get`, heavy CPU loop, sync DB driver) inside a coroutine freezes the WHOLE loop: every other request waits. Fix:
```python
result = await asyncio.to_thread(blocking_fn, arg)            # thread pool (3.9+)
result = await loop.run_in_executor(None, blocking_fn, arg)   # same, older API
result = await loop.run_in_executor(process_pool, cpu_fn, arg)  # CPU-bound -> processes
```
Also: `await asyncio.sleep(x)`, never `time.sleep(x)`, in async code. Debug mode (`asyncio.run(main(), debug=True)`) warns about slow callbacks.

## 11. How FastAPI uses this
- `async def` endpoint: runs ON the event loop. Great if you only `await` async libraries; a blocking call inside stalls every request.
- plain `def` endpoint: FastAPI runs it in a **threadpool** (AnyIO, 40 threads default) so blocking code is OK there.
- So: use `async def` + async drivers (httpx, asyncpg), or `def` for blocking libraries (requests, sync SQLAlchemy). Never mix blocking code into `async def`.
- `BackgroundTasks` run after the response; for heavy or must-not-lose work use a real queue (Celery, RQ, SQS).
- Under uvicorn, scale CPU with multiple worker processes (`--workers N`), each with its own loop. Shared in-memory state is per process.
- Dependencies declared `def` also go to the threadpool; `async def` ones run on the loop.

## 12. Choosing (interview cheat sheet)
1. Is it CPU-bound? -> `ProcessPoolExecutor` / multiprocessing (or numpy/C extension that releases the GIL).
2. I/O-bound, async library available, many connections? -> asyncio.
3. I/O-bound with blocking library, modest concurrency? -> `ThreadPoolExecutor`.
4. Shared mutable state across threads? -> lock it or, better, use a queue.

## Common mistakes
- Forgetting `await`: you get a coroutine object and a "never awaited" warning, and the code didn't run.
- `await`-ing coroutines one after another in a loop (sequential!) instead of `gather`/`TaskGroup`.
- `asyncio.run()` inside an already running loop (Jupyter, FastAPI) -> use `await`.
- `time.sleep` / `requests` in `async def`.
- Fire-and-forget `create_task` without storing the reference: task may be garbage-collected, and exceptions go unnoticed.
- Swallowing `CancelledError` or using bare `except:`.
- Assuming the GIL makes `+=` / check-then-act thread-safe.
- Sharing a lambda/closure with `ProcessPoolExecutor` (not picklable).
- Using `threading.Lock` in coroutines (blocks the loop) instead of `asyncio.Lock`.

## Your task
Fill in `exercises.py`, then run the tests:
`../../.venv/bin/pytest -q` from this folder. Then drill `interview-qa.md` aloud.
