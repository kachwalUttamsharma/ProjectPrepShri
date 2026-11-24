"""LLD 02: rate limiter (token bucket, sliding window log, fixed window, composite).

Read lesson.md for the full spec. Implement everything marked `...`.

Shared rules for every limiter
- `clock` is a zero-arg callable returning seconds as a float (default time.monotonic).
  Never call time.time()/sleep inside a limiter; always use the injected clock.
- State is kept PER KEY; keys are independent. State for a new key starts "fresh".
- `cost` must be an int >= 1 (bool rejected), else ValueError, from BOTH allow and retry_after.
- A denied request consumes NOTHING.
- `allow(key, cost=1) -> bool` and `retry_after(key, cost=1) -> float` are thread-safe
  (use a threading.Lock). retry_after never consumes anything.
- `retry_after` returns 0.0 if the request would be allowed right now, otherwise the
  number of seconds until it would be allowed if no other request arrives
  (math.inf if cost can never fit, i.e. cost > capacity / limit).
"""
import math
import threading
import time
from abc import ABC, abstractmethod
from collections import deque


class RateLimiter(ABC):
    """Abstract: allow(key, cost=1) -> bool and retry_after(key, cost=1) -> float."""

    @abstractmethod
    def allow(self, key, cost=1):
        ...

    @abstractmethod
    def retry_after(self, key, cost=1):
        ...


class TokenBucketLimiter(RateLimiter):
    """TokenBucketLimiter(capacity, refill_rate, clock=None).

    - capacity: int > 0 (max burst). refill_rate: number > 0, tokens per second.
      Invalid -> ValueError. Attributes: capacity, refill_rate.
    - A key's bucket starts FULL the first time it is seen.
    - Refill is lazy: on each call, tokens = min(capacity, tokens + elapsed * refill_rate).
      If the clock goes backwards, treat elapsed as 0 (never remove tokens) and keep the
      newest timestamp seen as the refill reference, so time is never counted twice.
    - allow: True and subtract `cost` tokens if tokens >= cost, else False.
    - retry_after: (cost - tokens) / refill_rate when short; 0.0 if enough; inf if cost > capacity.
    """

    def __init__(self, capacity, refill_rate, clock=None):
        ...

    def allow(self, key, cost=1):
        ...

    def retry_after(self, key, cost=1):
        ...


class SlidingWindowLogLimiter(RateLimiter):
    """SlidingWindowLogLimiter(limit, window, clock=None).

    - limit: int > 0 (max total cost per window). window: number > 0 seconds.
      Invalid -> ValueError. Attributes: limit, window.
    - Keeps a log of timestamps (one per unit of cost). A request at time t counts
      only log entries with timestamp > t - window (an entry made at t0 stops
      counting exactly at t0 + window).
    - allow: True (and append `cost` entries stamped now) if used + cost <= limit.
    - retry_after: 0.0 if it fits; inf if cost > limit; else time until enough old
      entries expire: (timestamp of the k-th oldest entry) + window - now, where
      k = used + cost - limit.
    Memory per key is O(limit); old entries are pruned on every call.
    """

    def __init__(self, limit, window, clock=None):
        ...

    def allow(self, key, cost=1):
        ...

    def retry_after(self, key, cost=1):
        ...


class FixedWindowLimiter(RateLimiter):
    """FixedWindowLimiter(limit, window, clock=None).

    - Windows are aligned to the clock: window start = floor(now / window) * window.
      The count resets when a new window begins. Same validation/attributes as above.
    - allow: True (and count += cost) if count + cost <= limit.
    - retry_after: 0.0 if it fits; inf if cost > limit; else (window end - now).
    Known weakness (explain it in the interview): up to 2x limit across a boundary.
    """

    def __init__(self, limit, window, clock=None):
        ...

    def allow(self, key, cost=1):
        ...

    def retry_after(self, key, cost=1):
        ...


class CompositeLimiter(RateLimiter):
    """CompositeLimiter(limiters): allow only if EVERY limiter would allow (e.g. 10/sec AND 1000/hour).

    - limiters: non-empty iterable of RateLimiter, else ValueError.
    - allow: if any child's retry_after(key, cost) > 0 -> False and NO child is charged
      (no partial consumption). Otherwise charge all children and return True.
      The check-then-charge must be atomic (own lock).
    - retry_after: the max of the children's retry_after.
    """

    def __init__(self, limiters):
        ...

    def allow(self, key, cost=1):
        ...

    def retry_after(self, key, cost=1):
        ...
