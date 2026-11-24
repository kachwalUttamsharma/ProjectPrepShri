import asyncio
import threading

import pytest

from exercises import *


def run(coro):
    """asyncio.run with a global safety timeout so a bug fails instead of hanging."""
    async def guarded():
        return await asyncio.wait_for(coro, 3)
    return asyncio.run(guarded())


async def val(x, delay=0.0):
    await asyncio.sleep(delay)
    return x


# 1
def test_gather_in_order():
    assert run(gather_in_order(val("a", 0.04), val("b"), val("c", 0.01))) == ["a", "b", "c"]
    assert run(gather_in_order()) == []


def test_gather_is_concurrent():
    async def main():
        a, b = asyncio.Event(), asyncio.Event()

        async def one():
            a.set()
            await b.wait()
            return 1

        async def two():
            b.set()
            await a.wait()
            return 2

        # sequential execution would deadlock; keep failure fast
        return await asyncio.wait_for(gather_in_order(one(), two()), 0.5)

    assert run(main()) == [1, 2]


# 2
def test_bounded_gather():
    state = {"cur": 0, "max": 0}

    async def job(i):
        state["cur"] += 1
        state["max"] = max(state["max"], state["cur"])
        for _ in range(3):
            await asyncio.sleep(0)
        state["cur"] -= 1
        return i * 10

    factories = [lambda i=i: job(i) for i in range(8)]
    assert run(bounded_gather(factories, 3)) == [i * 10 for i in range(8)]
    assert state["max"] == 3


def test_bounded_gather_limit_one():
    state = {"cur": 0, "max": 0}

    async def job():
        state["cur"] += 1
        state["max"] = max(state["max"], state["cur"])
        await asyncio.sleep(0)
        state["cur"] -= 1

    run(bounded_gather([job] * 4, 1))
    assert state["max"] == 1


# 3
def test_with_timeout():
    flag = {"cancelled": False}

    async def never():
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            flag["cancelled"] = True
            raise

    assert run(with_timeout(never(), 0.05, default="late")) == "late"
    assert flag["cancelled"] is True
    assert run(with_timeout(val(42), 1)) == 42
    assert run(with_timeout(never(), 0.02)) is None


# 4
def test_cancel_task():
    log = []

    async def main():
        async def worker():
            try:
                await asyncio.Event().wait()
            finally:
                log.append("cleaned")

        t = asyncio.create_task(worker())
        await asyncio.sleep(0)  # let it start
        result = await cancel_task(t)
        done = asyncio.create_task(val(1))
        await done
        return result, await cancel_task(done)

    assert run(main()) == (True, False)
    assert log == ["cleaned"]


# 5
def test_retry_async_succeeds_eventually():
    calls = []

    async def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("boom")
        return "ok"

    assert run(retry_async(flaky, 5)) == "ok"
    assert len(calls) == 3


def test_retry_async_gives_up_with_last_error():
    calls = []

    async def bad():
        calls.append(1)
        raise ValueError(f"fail {len(calls)}")

    with pytest.raises(ValueError, match="fail 3"):
        run(retry_async(bad, 3))
    assert len(calls) == 3


# 6
def test_async_resource():
    log = []

    async def ok():
        async with AsyncResource("db", log) as r:
            assert isinstance(r, AsyncResource)
            log.append("work")

    run(ok())
    assert log == ["open:db", "work", "close:db"]


def test_async_resource_does_not_swallow():
    log = []

    async def bad():
        async with AsyncResource("x", log):
            raise RuntimeError("no")

    with pytest.raises(RuntimeError):
        run(bad())
    assert log == ["open:x", "error:x", "close:x"]


# 7
def test_async_batches():
    async def source(n):
        for i in range(1, n + 1):
            await asyncio.sleep(0)
            yield i

    async def collect(n, size):
        return [b async for b in async_batches(source(n), size)]

    assert run(collect(5, 2)) == [[1, 2], [3, 4], [5]]
    assert run(collect(4, 2)) == [[1, 2], [3, 4]]
    assert run(collect(0, 3)) == []


# 8
def test_run_blocking_uses_thread_and_keeps_loop_free():
    gate = threading.Event()
    main_id = threading.get_ident()

    def blocking(x):
        # Waits for the event loop to set the gate. If run on the loop itself
        # the gate can never be set, so this times out and returns False.
        ok = gate.wait(1)
        return (threading.get_ident(), ok, x * 2)

    async def opener():
        await asyncio.sleep(0)
        gate.set()

    async def main():
        result, _ = await asyncio.gather(run_blocking(blocking, 21), opener())
        return result

    tid, ok, doubled = run(main())
    assert ok is True
    assert tid != main_id
    assert doubled == 42


# 9
def test_thread_safe_counter():
    c = ThreadSafeCounter()
    assert c.value == 0

    def work():
        for _ in range(5000):
            c.increment()

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert c.value == 40000
    c.increment(10)
    assert c.value == 40010


# 10
def test_worker_pool_queue_order_and_result():
    assert worker_pool_queue(list(range(20)), lambda x: x * x, 4) == [x * x for x in range(20)]
    assert worker_pool_queue([], lambda x: x, 3) == []


def test_worker_pool_queue_thread_count():
    ids = set()
    lock = threading.Lock()

    def fn(x):
        with lock:
            ids.add(threading.get_ident())
        return x

    worker_pool_queue(list(range(30)), fn, 3)
    assert 1 <= len(ids) <= 3
    assert threading.get_ident() not in ids
