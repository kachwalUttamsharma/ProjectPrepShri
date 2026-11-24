# Week 3 interview Q&A: concurrency

**1. What is the GIL and why does it exist?**
A mutex in CPython so only one thread runs Python bytecode at a time. It protects the interpreter's internals, mainly reference counting, and makes single-threaded code and C extensions simple and fast. It limits CPU parallelism in threads, not I/O concurrency.

**2. Do threads help in Python?**
Yes for I/O-bound work: the GIL is released while blocked on I/O and in many C extensions (numpy, hashlib, zlib). No for CPU-bound pure-Python code; use processes. Free-threaded builds (3.13+, experimental) remove this limit.

**3. Threading vs multiprocessing vs asyncio: when each?**
CPU-bound -> multiprocessing (true parallelism, costs: startup, pickling, memory). I/O-bound with async-capable libs and many connections -> asyncio (cheap, single thread, explicit await points). I/O-bound with blocking libs -> threads.

**4. Does the GIL make my code thread-safe?**
No. Individual bytecodes are atomic, but `x += 1` or check-then-act spans several, so threads can interleave. Use locks, queues, or immutable data.

**5. What is a race condition? Give an example and a fix.**
Outcome depends on scheduling. Two threads doing `counter += 1` (load, add, store) can lose updates. Fix: `with lock:` around the read-modify-write, or funnel updates through a single thread/queue.

**6. What is a deadlock and how do you avoid it?**
Threads each hold a lock the other needs. Avoid with a global lock ordering, holding as few locks as possible, `acquire(timeout=...)`, or avoiding shared locks via message passing. `Lock` re-acquired by the same thread also deadlocks; use `RLock` if needed.

**7. Lock vs RLock vs Semaphore vs Event vs Condition?**
Lock: mutual exclusion, one holder. RLock: reentrant for the owning thread. Semaphore: up to N holders (limit concurrency). Event: boolean flag threads wait on (`set`/`wait`). Condition: wait until a predicate becomes true, with a lock.

**8. How does the queue module help?**
`queue.Queue` is thread-safe and blocking, enabling producer/consumer without explicit locks. `maxsize` gives backpressure, `task_done`/`join` track completion, sentinels (`None`) signal shutdown. `PriorityQueue` and `LifoQueue` variants exist.

**9. Explain concurrent.futures.**
High-level executors (`ThreadPoolExecutor`, `ProcessPoolExecutor`) with `submit` -> `Future` and `map`. `Future.result()` blocks and re-raises worker exceptions. `as_completed` yields futures as they finish; `map` preserves input order. Same API lets you swap threads for processes.

**10. What is the asyncio event loop?**
A single-threaded scheduler that runs ready callbacks/coroutines and uses OS I/O multiplexing (epoll/kqueue) to wake coroutines when sockets are ready. Coroutines yield control only at `await`, so it is cooperative multitasking.

**11. Coroutine vs Task vs Future?**
Coroutine: object from calling `async def`; inert until awaited. Task: wraps a coroutine and schedules it on the loop immediately (`create_task`). Future: low-level placeholder for a result set later; Task is a Future subclass.

**12. What does `await` do? What happens if I forget it?**
It suspends the current coroutine until the awaitable completes, letting the loop run others. Forgetting it yields a coroutine object that never runs (RuntimeWarning: never awaited), and you use the object instead of the result.

**13. gather vs TaskGroup vs wait?**
`gather` returns ordered results; on first exception it propagates but doesn't cancel the siblings (unless you cancel it). `TaskGroup` (3.11+) is structured: on failure it cancels siblings and raises an `ExceptionGroup`; the scope doesn't exit until all tasks finish. `asyncio.wait` gives (done, pending) sets with `FIRST_COMPLETED` etc. for finer control.

**14. How do cancellation and timeouts work?**
`task.cancel()` throws `CancelledError` into the coroutine at its next await; `finally`/`async with` cleanup runs. You should await the task afterwards. `wait_for`/`asyncio.timeout` cancel the inner work and raise `TimeoutError`. Never swallow `CancelledError`; re-raise it. It derives from `BaseException`, so `except Exception` won't catch it.

**15. A service calls 10 000 URLs; how do you do it safely?**
Use an `asyncio.Semaphore` (or a bounded worker pool on an `asyncio.Queue`) to cap in-flight requests, a shared `httpx.AsyncClient` with connection limits, timeouts on each call, retries with backoff and jitter, and `return_exceptions=True` or per-task error handling so one failure doesn't lose everything.

**16. What happens if you call blocking code in a coroutine?**
The event loop thread is blocked, so no other coroutine, timer, or request is serviced: latency spikes for everyone. Offload with `asyncio.to_thread` / `run_in_executor` (threads for blocking I/O, a process pool for CPU), or use an async library.

**17. How do async context managers and async generators differ from sync ones?**
Async CMs use `__aenter__`/`__aexit__` (awaitable), used with `async with`, e.g. DB connections and locks. Async generators use `async def` with `yield`, consumed by `async for`; they let you await between items (streaming responses, paginated APIs). Clean up with `aclose()` or `async with aclosing(...)`.

**18. How does FastAPI handle `def` vs `async def` endpoints?**
`async def` runs directly on the event loop; blocking inside it stalls the server. `def` is dispatched to a threadpool (default ~40 threads), so blocking calls are fine but limited by pool size. Choose by the libraries you call. Scale CPU via multiple uvicorn/gunicorn worker processes.

**19. asyncio.Lock vs threading.Lock?**
`asyncio.Lock` is awaited, not thread-safe, only for coroutines in one loop; it suspends the coroutine, not the thread. `threading.Lock` blocks the thread, and blocking the loop thread with it freezes the loop. Often you don't need a lock in asyncio at all: without an `await` in a critical section there is no interleaving.

**20. How do you share data between processes, and what are the pitfalls?**
Via pickling over pipes/queues (`multiprocessing.Queue`), shared memory (`shared_memory`, `Value`/`Array`), or a manager/external store (Redis, DB). Pitfalls: arguments and results must be picklable, big payloads are expensive to copy, `spawn` start method (macOS/Windows default) re-imports the module so guard with `if __name__ == "__main__":`, and `fork` with threads can deadlock.
