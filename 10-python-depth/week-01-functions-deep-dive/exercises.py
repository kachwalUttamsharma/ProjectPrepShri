"""Week 1 exercises: functions deep-dive.

Replace each `...` with your code. Read the docstring and hint first.
Run tests:  ../../.venv/bin/pytest -q
"""
import functools
import itertools
from contextlib import contextmanager


# Exercise 1 -------------------------------------------------------------
def make_counter(start=0):
    """Return a function `counter()` that returns start+1, start+2, ... on
    successive calls. Each make_counter() call has its own independent state.

    Hint: closure + `nonlocal`.
    """
    ...


# Exercise 2 -------------------------------------------------------------
def make_multipliers(n):
    """Return a list of n functions; the function at index i multiplies its
    argument by i. make_multipliers(3)[2](10) == 20.

    Hint: the classic late-binding trap. `lambda x: x * i` inside a loop sees
    the FINAL i. Bind it with a default argument (i=i) or functools.partial.
    """
    ...


# Exercise 3 -------------------------------------------------------------
def append_item(item, items=[]):
    """Append item to items and return items. If no list is passed, a FRESH
    list must be used on every call (append_item(1) then append_item(2)
    returns [2], not [1, 2]).

    Hint: this signature is buggy on purpose. Use `items=None` and create the
    list inside the function.
    """
    ...


# Exercise 4 -------------------------------------------------------------
def count_calls(func):
    """Decorator. The wrapped function must still work normally, expose the
    number of calls so far as attribute `.calls` (starts at 0), and keep the
    original __name__ and __doc__.

    Hint: functools.wraps; store the counter on the wrapper function object.
    """
    ...


# Exercise 5 -------------------------------------------------------------
def retry(times, exceptions=(Exception,)):
    """Decorator FACTORY: @retry(3) calls the function up to `times` total
    attempts, retrying only when one of `exceptions` is raised. If every
    attempt fails, re-raise the last exception. Return the first success.
    Other exception types propagate immediately. No sleeping.

    Hint: three nested levels: retry -> decorator -> wrapper. Use functools.wraps.
    """
    ...


# Exercise 6 -------------------------------------------------------------
def singleton(cls):
    """Class decorator: after `@singleton class A`, calling A(...) always
    returns the SAME instance (created on the first call with the first
    call's arguments; later arguments are ignored).

    Hint: keep a dict/closure variable of instances; return a function.
    """
    ...


# Exercise 7 -------------------------------------------------------------
@contextmanager
def temp_attr(obj, name, value):
    """Context manager: set obj.<name> = value inside the with-block, then
    restore the old value afterwards (even if the block raised). If the
    attribute did not exist before, delete it on exit.

    Hint: @contextmanager generator; try/finally around the yield.
    Use hasattr/getattr/setattr/delattr.
    """
    ...


# Exercise 8 -------------------------------------------------------------
class Countdown:
    """Iterator class: iterating Countdown(3) yields 3, 2, 1 and then stops.
    It is a one-shot iterator: once exhausted, iterating again yields nothing.

    Hint: implement __iter__ (return self) and __next__ (raise StopIteration
    when done).
    """

    def __init__(self, start):
        ...

    def __iter__(self):
        ...

    def __next__(self):
        ...


# Exercise 9 -------------------------------------------------------------
def chunked(iterable, n):
    """Generator: yield lists of up to n items from any iterable (the last
    chunk may be shorter). Must be lazy: it must work on an infinite iterator.
    n < 1 raises ValueError (when iteration starts is fine).

    chunked(range(5), 2) -> [0, 1], [2, 3], [4]
    Hint: iterator = iter(iterable); itertools.islice(iterator, n) in a loop.
    """
    ...


# Exercise 10 ------------------------------------------------------------
def fib(n):
    """Return the nth Fibonacci number (fib(0)=0, fib(1)=1) with the naive
    recursive definition, but make it fast with functools.lru_cache so that
    fib(90) is instant and fib.cache_info() works.

    Hint: one decorator line. Use @functools.lru_cache(maxsize=None).
    """
    ...


def compose(*funcs):
    """Return a function applying funcs right to left:
    compose(f, g, h)(x) == f(g(h(x))). compose() is the identity function.

    Hint: functools.reduce over reversed(funcs).
    """
    ...


# Exercise 11 ------------------------------------------------------------
def run_length_encode(s):
    """Return a list of (char, count) for consecutive runs.
    'aaabcc' -> [('a', 3), ('b', 1), ('c', 2)]; '' -> [].

    Hint: itertools.groupby(s); count with sum(1 for _ in group).
    """
    ...
