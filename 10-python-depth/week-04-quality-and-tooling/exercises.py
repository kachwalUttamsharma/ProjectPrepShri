"""Week 4 exercises: quality and tooling. Replace each `...` with your code.

Run the tests from this folder:
    ../../.venv/bin/pytest -q
Read test_exercises.py too: it shows fixtures, parametrize, caplog, Mock,
monkeypatch and tmp_path in action. Copy those patterns into your own work.
"""
import cProfile  # noqa: F401  (hint for exercise 10)
import logging
import os  # noqa: F401  (hint for exercise 7)
import pstats  # noqa: F401  (hint for exercise 10)
import time
import timeit  # noqa: F401  (hint for exercise 9)
from pathlib import Path  # noqa: F401  (hint for exercise 8)


# Exercise 1 -------------------------------------------------------------
class AppError(Exception):
    """Base error for the app. Takes (message, code=500).

    Store them as .message and .code, and pass message to super().__init__
    so str(err) == message.
    """
    ...


class NotFoundError(AppError):
    """AppError with code 404. Constructor takes only (message)."""
    ...


class ValidationFailed(AppError):
    """AppError with code 422. Constructor takes only (message)."""
    ...


# Exercise 2 -------------------------------------------------------------
def parse_age(text):
    """Convert text to an int age in 0..150 inclusive.

    - not an int (e.g. 'abc', '', '3.5', None): raise ValidationFailed
      *chained* from the original error: `raise X(...) from exc`.
    - out of range: raise ValidationFailed.
    Hint: int(" 42 ") works; int(None) raises TypeError, int("x") ValueError.
    """
    ...


# Exercise 3 -------------------------------------------------------------
def retry(func, attempts=3, exceptions=(Exception,)):
    """Call func() up to `attempts` times and return its result.

    - Only exceptions in `exceptions` trigger a retry; others propagate at once.
    - If the last attempt fails, re-raise that exception (bare `raise`).
    - attempts < 1: raise ValueError.
    - Do NOT sleep (keeps tests fast; real code would back off).
    """
    ...


# Exercise 4 -------------------------------------------------------------
def get_logger(name, stream):
    """Return logging.getLogger(name) configured to write to `stream`.

    - level INFO, propagate = False
    - one StreamHandler(stream) with format '%(levelname)s:%(message)s'
    - calling twice with the same name must NOT add a second handler
      (check `logger.handlers`).
    """
    ...


# Exercise 5 -------------------------------------------------------------
def process_orders(orders, logger):
    """orders: list of dicts {'id': ..., 'amount': ...}. Return total amount.

    - amount < 0: logger.warning('skipping order %s: negative amount', id)
      and skip it.
    - otherwise: logger.info('processed order %s', id) and add to the total.
    Use lazy %-style args (not f-strings) in logging calls.
    """
    ...


# Exercise 6 -------------------------------------------------------------
def fetch_username(user_id, client):
    """Call client.get(f'/users/{user_id}') exactly once. Response has
    .status_code and .json().

    - 404: raise NotFoundError(f'user {user_id} not found')
    - any other status >= 400: raise AppError(f'upstream error {status}', code=502)
    - else return response.json()['name']
    The client is injected, so tests pass in a unittest.mock.Mock.
    """
    ...


# Exercise 7 -------------------------------------------------------------
def get_config():
    """Read settings from os.environ AT CALL TIME (so monkeypatch works).

    Return {'debug': bool, 'port': int, 'name': str}
    - APP_DEBUG: True only for '1' or 'true' (case-insensitive); default False
    - APP_PORT: int, default 8000
    - APP_NAME: default 'app'
    """
    ...


# Exercise 8 -------------------------------------------------------------
def count_words_in_file(path):
    """Return {word: count} for a text file; lowercase, split on whitespace.

    Hint: Path(path).read_text(). Accepts str or Path.
    """
    ...


# Exercise 9 -------------------------------------------------------------
def best_time(func, number=5, repeat=3, timer=time.perf_counter):
    """Return the best (minimum) seconds-per-call of func.

    Use timeit.Timer(func, timer=timer).repeat(repeat=repeat, number=number),
    then min(...) / number. `timer` is injectable so tests are deterministic.
    Why min and not mean? Noise only ever makes runs slower.
    """
    ...


# Exercise 10 ------------------------------------------------------------
def profile_calls(func):
    """Run func() under cProfile and return {function_name: call_count}.

    Hint: pr = cProfile.Profile(); pr.enable(); ...; pr.disable() (use
    try/finally so errors still disable it), then pstats.Stats(pr).stats maps
    (file, line, name) -> (cc, nc, tt, ct, callers). nc is the call count.
    If one name appears twice, sum the counts.
    """
    ...
