"""Week 2 (python-depth) exercises: data model and memory.

Replace each `...` with your code. Run from this folder:
    ../../.venv/bin/pytest -q
"""
import copy, gc, weakref
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Generic, TypeVar

T = TypeVar("T")


# Exercise 1 -------------------------------------------------------------
def copy_pair(nested):
    """Return (shallow_copy, deep_copy) of `nested`.
    Hint: the copy module. The shallow copy shares inner objects with the
    original; the deep copy shares nothing."""
    ...


# Exercise 2 -------------------------------------------------------------
class Money:
    """Immutable value object.
    - __init__(amount, currency); read-only properties `amount` and `currency`
      (assigning to them must raise AttributeError).
    - Equal when both fields are equal; NOT equal to non-Money (return
      NotImplemented from __eq__ for foreign types).
    - Hashable, consistent with __eq__ (equal objects -> equal hashes), so it
      works in sets and as a dict key.
    - A helpful __repr__.
    Hint: hash a tuple of the fields. Store fields in underscore attributes."""
    ...


# Exercise 3 -------------------------------------------------------------
class SlottedPoint:
    """Point with x and y that uses __slots__ (no per-instance __dict__,
    and assigning any other attribute raises AttributeError)."""
    ...


# Exercise 4 -------------------------------------------------------------
class Positive:
    """Data descriptor that only accepts values > 0 (else ValueError).
    Implement __set_name__, __get__ and __set__. Store the value on the
    *instance* (e.g. under '_' + name), never on the descriptor itself.
    __get__ with obj None (class access) should return the descriptor."""
    ...


class Item:
    """Provided. Works once Positive works."""
    price = Positive()
    qty = Positive()

    def __init__(self, price, qty):
        self.price = price
        self.qty = qty


# Exercise 5 -------------------------------------------------------------
def top_words(text, n):
    """Return the n most common words (lowercased, split on whitespace) as a
    list of (word, count). Ties broken alphabetically.
    Hint: Counter, then sorted with key=(-count, word)."""
    ...


# Exercise 6 -------------------------------------------------------------
def group_by(items, key):
    """Group items into {key(item): [items...]} preserving order. Return a
    plain dict (not a defaultdict). Hint: defaultdict(list), then dict()."""
    ...


# Exercise 7 -------------------------------------------------------------
def last_n(iterable, n):
    """Return a list of the last n items of any iterable (even a generator)
    using O(n) memory. Hint: deque(maxlen=n)."""
    ...


# Exercise 8 -------------------------------------------------------------
def sort_employees(rows):
    """rows: list of dicts with name, dept, salary. Return a NEW list sorted
    by dept ascending, then salary descending, then name ascending. Do not
    mutate the input.
    Hint: sort stability. Either sort several times, last key first, or use a
    single key with a negated salary."""
    ...


# Exercise 9 -------------------------------------------------------------
@dataclass
class Task:
    """Make this a frozen, orderable dataclass with fields:
    priority: int, title: str (excluded from comparisons), tags: tuple = ().
    Hint: @dataclass(order=True, frozen=True) and field(compare=False).
    Frozen + eq gives a generated __hash__."""
    ...


# Exercise 10 ------------------------------------------------------------
class Priority(IntEnum):
    """LOW=1, MEDIUM=2, HIGH=3."""
    ...


def parse_priority(s):
    """'  high ' -> Priority.HIGH (case/space insensitive). Unknown names
    raise ValueError. Hint: Priority[name] raises KeyError; translate it
    (`raise ... from None`)."""
    ...


# Exercise 11 ------------------------------------------------------------
class Stack(Generic[T]):
    """Generic stack: push(item), pop() (IndexError when empty), peek(),
    len(stack)."""
    ...


def describe(x):
    """Type narrowing. None -> 'nothing'; bool -> 'bool'; int -> 'int:7';
    str -> 'str:hi'; list -> 'list of 3'; anything else -> 'other'.
    Gotcha: bool is a subclass of int, so check it first."""
    ...


# Exercise 12 ------------------------------------------------------------
class _Node:
    pass


def cycle_collected():
    """Make two _Node objects that reference each other (a.other = b,
    b.other = a), keep a weakref.ref to one, delete both names, call
    gc.collect(), and return True if the weakref is now dead. Shows that
    refcounting alone cannot free cycles and the cyclic GC can."""
    ...
