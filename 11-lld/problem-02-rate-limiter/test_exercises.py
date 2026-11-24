import math
import threading

import pytest

from exercises import *


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---- ABC
def test_ratelimiter_is_abstract():
    with pytest.raises(TypeError):
        RateLimiter()


@pytest.mark.parametrize("cls", [TokenBucketLimiter, SlidingWindowLogLimiter, FixedWindowLimiter, CompositeLimiter])
def test_concrete_classes_are_ratelimiters(cls):
    assert issubclass(cls, RateLimiter)


# ---- token bucket
def tb(capacity=5, rate=1, clock=None):
    clock = clock or FakeClock()
    return TokenBucketLimiter(capacity, rate, clock), clock


@pytest.mark.parametrize("cap,rate", [(0, 1), (-1, 1), (1.5, 1), (5, 0), (5, -2), (True, 1)])
def test_tb_bad_config(cap, rate):
    with pytest.raises(ValueError):
        TokenBucketLimiter(cap, rate, FakeClock())


def test_tb_attrs():
    lim, _ = tb(7, 2)
    assert lim.capacity == 7 and lim.refill_rate == 2


def test_tb_burst_up_to_capacity_then_deny():
    lim, _ = tb(5, 1)
    assert [lim.allow("u") for _ in range(7)] == [True] * 5 + [False] * 2


def test_tb_refills_over_time():
    lim, clock = tb(5, 1)
    for _ in range(5):
        lim.allow("u")
    assert not lim.allow("u")
    clock.advance(1)
    assert lim.allow("u")
    assert not lim.allow("u")
    clock.advance(2.5)
    assert lim.allow("u") and lim.allow("u")
    assert not lim.allow("u")


def test_tb_refill_is_capped_at_capacity():
    lim, clock = tb(5, 1)
    for _ in range(5):
        lim.allow("u")
    clock.advance(1000)
    assert [lim.allow("u") for _ in range(6)] == [True] * 5 + [False]


def test_tb_keys_are_independent():
    lim, _ = tb(2, 1)
    assert lim.allow("a") and lim.allow("a") and not lim.allow("a")
    assert lim.allow("b") and lim.allow("b")


def test_tb_cost():
    lim, clock = tb(10, 2)
    assert lim.allow("u", cost=7)
    assert not lim.allow("u", cost=4)      # denied: nothing consumed
    assert lim.allow("u", cost=3)
    assert not lim.allow("u")
    clock.advance(2)                       # +4 tokens
    assert lim.allow("u", cost=4)


def test_tb_denied_request_consumes_nothing():
    lim, clock = tb(3, 1)
    lim.allow("u", cost=2)
    for _ in range(5):
        assert not lim.allow("u", cost=2)
    assert lim.allow("u", cost=1)


def test_tb_cost_larger_than_capacity():
    lim, _ = tb(3, 1)
    assert not lim.allow("u", cost=4)
    assert lim.retry_after("u", cost=4) == math.inf
    assert lim.allow("u", cost=3)          # bucket was not drained by the failed call


@pytest.mark.parametrize("cost", [0, -1, 1.5, True, "1"])
def test_cost_validation_all_limiters(cost):
    clock = FakeClock()
    for lim in (TokenBucketLimiter(5, 1, clock), SlidingWindowLogLimiter(5, 10, clock), FixedWindowLimiter(5, 10, clock)):
        with pytest.raises(ValueError):
            lim.allow("u", cost)
        with pytest.raises(ValueError):
            lim.retry_after("u", cost)


def test_tb_retry_after():
    lim, clock = tb(2, 2)                  # 2 tokens/sec
    assert lim.retry_after("u") == 0.0
    lim.allow("u")
    lim.allow("u")
    assert lim.retry_after("u") == pytest.approx(0.5)
    assert lim.retry_after("u", cost=2) == pytest.approx(1.0)
    clock.advance(0.25)
    assert lim.retry_after("u") == pytest.approx(0.25)
    clock.advance(0.25)
    assert lim.retry_after("u") == 0.0
    assert lim.allow("u")


def test_tb_retry_after_does_not_consume():
    lim, _ = tb(1, 1)
    for _ in range(5):
        assert lim.retry_after("u") == 0.0
    assert lim.allow("u")


def test_tb_clock_going_backwards_is_safe():
    lim, clock = tb(2, 1)
    clock.now = 100
    lim.allow("u")
    lim.allow("u")
    clock.now = 50                         # backwards
    assert not lim.allow("u")
    clock.now = 101
    assert lim.allow("u") and not lim.allow("u")


def test_tb_default_clock_is_usable():
    lim = TokenBucketLimiter(1, 1)
    assert lim.allow("u") is True


# ---- sliding window log
def sw(limit=3, window=10, clock=None):
    clock = clock or FakeClock()
    return SlidingWindowLogLimiter(limit, window, clock), clock


@pytest.mark.parametrize("limit,window", [(0, 1), (-1, 1), (2.5, 1), (3, 0), (3, -1)])
def test_sw_bad_config(limit, window):
    with pytest.raises(ValueError):
        SlidingWindowLogLimiter(limit, window, FakeClock())


def test_sw_limit_within_window():
    lim, clock = sw(3, 10)
    assert [lim.allow("u") for _ in range(4)] == [True, True, True, False]


def test_sw_entry_expires_exactly_at_window_end():
    lim, clock = sw(3, 10)
    for _ in range(3):
        lim.allow("u")
    clock.advance(9.99)
    assert not lim.allow("u")
    clock.advance(0.01)                    # t == 10: the t=0 entries stop counting
    assert lim.allow("u")


def test_sw_window_slides_entry_by_entry():
    lim, clock = sw(2, 10)
    lim.allow("u")                         # t=0
    clock.advance(4)
    lim.allow("u")                         # t=4
    assert not lim.allow("u")
    clock.advance(6)                       # t=10: first expired, second still counts
    assert lim.allow("u")
    assert not lim.allow("u")
    clock.advance(4)                       # t=14: t=4 entry expired
    assert lim.allow("u")


def test_sw_no_boundary_burst():
    lim, clock = sw(5, 10)
    clock.now = 9
    assert all(lim.allow("u") for _ in range(5))
    clock.now = 10                         # 1s later: still within 10s of the first batch
    assert not lim.allow("u")


def test_sw_keys_independent_and_cost():
    lim, _ = sw(5, 10)
    assert lim.allow("a", cost=4)
    assert not lim.allow("a", cost=2)
    assert lim.allow("a", cost=1)
    assert lim.allow("b", cost=5)


def test_sw_denied_request_does_not_log():
    lim, clock = sw(1, 10)
    assert lim.allow("u")
    clock.advance(5)
    assert not lim.allow("u")              # must not push the window forward
    clock.advance(5)
    assert lim.allow("u")


def test_sw_retry_after():
    lim, clock = sw(2, 10)
    assert lim.retry_after("u") == 0.0
    lim.allow("u")                         # t=0
    clock.advance(3)
    lim.allow("u")                         # t=3
    assert lim.retry_after("u") == pytest.approx(7.0)
    assert lim.retry_after("u", cost=2) == pytest.approx(10.0)
    clock.advance(7)
    assert lim.retry_after("u") == 0.0


def test_sw_cost_larger_than_limit():
    lim, _ = sw(2, 10)
    assert not lim.allow("u", cost=3)
    assert lim.retry_after("u", cost=3) == math.inf


def test_sw_memory_pruned():
    lim, clock = sw(3, 1)
    for i in range(1000):
        lim.allow("u")
        clock.advance(1)
    # behaves correctly after long history
    assert lim.allow("u") and lim.allow("u") and lim.allow("u") and not lim.allow("u")


# ---- fixed window
def fw(limit=3, window=10, clock=None):
    clock = clock or FakeClock()
    return FixedWindowLimiter(limit, window, clock), clock


@pytest.mark.parametrize("limit,window", [(0, 1), (3, 0), (1.5, 1)])
def test_fw_bad_config(limit, window):
    with pytest.raises(ValueError):
        FixedWindowLimiter(limit, window, FakeClock())


def test_fw_limit_and_reset_at_aligned_boundary():
    lim, clock = fw(3, 10)
    clock.now = 3
    assert [lim.allow("u") for _ in range(4)] == [True, True, True, False]
    clock.now = 9.99
    assert not lim.allow("u")
    clock.now = 10                         # new aligned window
    assert [lim.allow("u") for _ in range(4)] == [True, True, True, False]


def test_fw_boundary_burst_is_allowed_unlike_sliding_window():
    lim, clock = fw(5, 10)
    clock.now = 9
    assert all(lim.allow("u") for _ in range(5))
    clock.now = 10
    assert all(lim.allow("u") for _ in range(5))   # 10 requests in 1 second


def test_fw_skipped_windows_reset():
    lim, clock = fw(1, 10)
    assert lim.allow("u")
    clock.now = 55
    assert lim.allow("u")


def test_fw_keys_cost_retry_after():
    lim, clock = fw(5, 10)
    clock.now = 4
    assert lim.allow("a", cost=5)
    assert lim.allow("b", cost=1)
    assert not lim.allow("a")
    assert lim.retry_after("a") == pytest.approx(6.0)
    assert lim.retry_after("b") == 0.0
    assert lim.retry_after("a", cost=6) == math.inf
    clock.now = 10
    assert lim.retry_after("a") == 0.0


# ---- composite
def test_composite_requires_all_and_has_no_partial_consumption():
    clock = FakeClock()
    per_sec = SlidingWindowLogLimiter(2, 1, clock)
    per_min = SlidingWindowLogLimiter(3, 60, clock)
    both = CompositeLimiter([per_sec, per_min])
    assert both.allow("u") and both.allow("u")
    assert not both.allow("u")             # per-second exhausted
    clock.advance(1)
    assert both.allow("u")                 # 3rd of the minute
    clock.advance(1)
    assert not both.allow("u")             # per-minute exhausted
    # the denied calls above must not have been charged to per_sec
    assert per_sec.retry_after("u") == 0.0


def test_composite_retry_after_is_max():
    clock = FakeClock()
    a = SlidingWindowLogLimiter(1, 5, clock)
    b = SlidingWindowLogLimiter(1, 20, clock)
    both = CompositeLimiter([a, b])
    assert both.allow("u")
    assert both.retry_after("u") == pytest.approx(20.0)
    clock.advance(5)
    assert both.retry_after("u") == pytest.approx(15.0)


def test_composite_validates():
    with pytest.raises(ValueError):
        CompositeLimiter([])
    c = CompositeLimiter([TokenBucketLimiter(2, 1, FakeClock())])
    with pytest.raises(ValueError):
        c.allow("u", 0)


def test_composite_mixes_algorithms_and_cost():
    clock = FakeClock()
    c = CompositeLimiter([TokenBucketLimiter(4, 1, clock), FixedWindowLimiter(10, 100, clock)])
    assert c.allow("u", cost=4)
    assert not c.allow("u", cost=1)
    clock.advance(2)
    assert c.allow("u", cost=2)


# ---- concurrency (frozen clock => exact counts, deterministic)
def hammer(lim, threads=16, per_thread=50, **kw):
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(threads)

    def work():
        barrier.wait()
        local = [lim.allow("shared", **kw) for _ in range(per_thread)]
        with lock:
            results.extend(local)

    ts = [threading.Thread(target=work) for _ in range(threads)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    return results


def test_tb_thread_safe_exact_count():
    lim = TokenBucketLimiter(100, 1, FakeClock())
    assert sum(hammer(lim)) == 100


def test_sw_thread_safe_exact_count():
    lim = SlidingWindowLogLimiter(100, 10, FakeClock())
    assert sum(hammer(lim)) == 100


def test_fw_thread_safe_exact_count():
    lim = FixedWindowLimiter(100, 10, FakeClock())
    assert sum(hammer(lim)) == 100


def test_composite_thread_safe_exact_count():
    clock = FakeClock()
    c = CompositeLimiter([TokenBucketLimiter(100, 1, clock), SlidingWindowLogLimiter(60, 10, clock)])
    assert sum(hammer(c)) == 60
