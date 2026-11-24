"""Week 4 exercises: composition, dataclasses, enums, protocols, patterns, exceptions.

Replace each `...`. For dataclass/enum/protocol stubs you must also WRITE the
fields/members (the docstring tells you which). Keep names.
"""
from dataclasses import dataclass, field, replace
from enum import Enum, IntEnum
from typing import Protocol, runtime_checkable


# ---- 1. Composition ----------------------------------------------------------
class Engine:
    """Engine(horsepower). attrs: horsepower, running (False at first).
    start() -> sets running, returns 'Engine started (<hp> hp)'.
    stop() -> clears running, returns None.
    """

    def __init__(self, horsepower):
        ...

    def start(self):
        ...

    def stop(self):
        ...


class Car:
    """Car(name, engine): HAS an Engine (do not inherit!).
    start() delegates to the engine and returns its message.
    is_running (property) mirrors the engine.
    swap_engine(new_engine) installs the new engine (stopping the old one)
    and returns the old one.
    """

    def __init__(self, name, engine):
        ...

    def start(self):
        ...

    @property
    def is_running(self):
        ...

    def swap_engine(self, new_engine):
        ...


# ---- 2. Dataclasses ------------------------------------------------------------
@dataclass
class Item:
    """Fields: name: str, price: float, qty: int = 1.
    __post_init__: ValueError if price < 0 or qty < 1.
    Property `total` -> price * qty.
    """

    def __post_init__(self):
        ...

    @property
    def total(self):
        ...


@dataclass(frozen=True)
class Coordinate:
    """Fields: lat: float, lon: float. Frozen (hashable).
    with_lat(lat) -> a NEW Coordinate with the lat changed (use dataclasses.replace).
    """

    def with_lat(self, lat):
        ...


@dataclass(order=True)
class Task:
    """Fields in this order: priority: int, name: str (compare=False),
    tags: list[str] (default_factory=list, compare=False).
    Tasks sort by priority only.
    """


# ---- 3. Enums ------------------------------------------------------------------
class Status(Enum):
    """Members PENDING='pending', ACTIVE='active', DONE='done'."""


class Direction(Enum):
    """Members NORTH, EAST, SOUTH, WEST (in that clockwise order; values 0-3).
    turn_right() -> next clockwise member; turn_left() -> previous.
    Hint: list(Direction) and modulo.
    """

    def turn_right(self):
        ...

    def turn_left(self):
        ...


class Priority(IntEnum):
    """Members LOW=1, MEDIUM=2, HIGH=3."""


def parse_status(text):
    """'  Done ' -> Status.DONE (case-insensitive, strip). Unknown -> ValueError."""
    ...


# ---- 4. Protocol -----------------------------------------------------------------
@runtime_checkable
class Drawable(Protocol):
    """Anything with a draw() -> str method. (Add the method to this Protocol.)"""


def render_all(items):
    """'\\n'.join(item.draw() for each item)."""
    ...


# ---- 5. Strategy -----------------------------------------------------------------
class NoDiscount:
    """apply(total) -> total unchanged."""

    def apply(self, total):
        ...


class PercentDiscount:
    """PercentDiscount(percent): ValueError unless 0 <= percent <= 100.
    apply(total) -> total reduced by that percent.
    """

    def __init__(self, percent):
        ...

    def apply(self, total):
        ...


class FixedDiscount:
    """FixedDiscount(amount): ValueError if amount < 0.
    apply(total) -> total - amount but never below 0.
    """

    def __init__(self, amount):
        ...

    def apply(self, total):
        ...


class Cart:
    """Cart(strategy=None) (None -> NoDiscount()).
    add(price), subtotal() -> sum of prices, total() -> strategy.apply(subtotal()),
    set_strategy(strategy) swaps at runtime.
    """

    def __init__(self, strategy=None):
        ...

    def add(self, price):
        ...

    def subtotal(self):
        ...

    def total(self):
        ...

    def set_strategy(self, strategy):
        ...


# ---- 6. Factory ------------------------------------------------------------------
class EmailNotifier:
    def send(self, message):
        """-> '[email] <message>'"""
        ...


class SmsNotifier:
    def send(self, message):
        """-> '[sms] <message>'"""
        ...


class PushNotifier:
    def send(self, message):
        """-> '[push] <message>'"""
        ...


_REGISTRY = {}  # kind (lowercase str) -> class. Fill with the three above.


def register_notifier(kind, cls):
    """Add (or replace) a kind in the registry (lowercased key)."""
    ...


def create_notifier(kind):
    """create_notifier('SMS') -> SmsNotifier() (case-insensitive).
    Unknown kind -> ValueError. No if/elif chain: use the registry.
    """
    ...


# ---- 7. Observer -----------------------------------------------------------------
class EventEmitter:
    """subscribe(event, handler); unsubscribe(event, handler) (ignore if absent);
    emit(event, *args, **kwargs) calls each handler for that event in subscription
    order with those args and returns how many handlers ran (0 for unknown events).
    A handler may unsubscribe itself while being called: iterate over a copy.
    """

    def __init__(self):
        ...

    def subscribe(self, event, handler):
        ...

    def unsubscribe(self, event, handler):
        ...

    def emit(self, event, *args, **kwargs):
        ...


# ---- 8. Singleton (and its caveat) ------------------------------------------------
class Config:
    """Singleton via __new__: Config() is Config() is True.
    Instance state: `settings` dict created ONCE (careful: __init__ runs on every
    Config() call, so don't reset state there; set it up in __new__).
    set(key, value); get(key, default=None).
    @classmethod reset_instance(): forget the instance (needed to isolate tests;
    that need is itself the caveat of singletons).
    """

    _instance = None

    def __new__(cls):
        ...

    def set(self, key, value):
        ...

    def get(self, key, default=None):
        ...

    @classmethod
    def reset_instance(cls):
        ...


# ---- 9. Exceptions as classes -----------------------------------------------------
class BankError(Exception):
    """Base class for this module's bank errors."""


class InsufficientFundsError(BankError):
    """InsufficientFundsError(balance, requested): attrs `balance`, `requested`;
    str(e) == 'Insufficient funds: balance 10, requested 50'.
    """

    def __init__(self, balance, requested):
        ...


class AccountFrozenError(BankError):
    """No custom code needed beyond the right base class."""


class Wallet:
    """Wallet(balance=0, frozen=False). withdraw(amount) -> new balance.
    frozen -> AccountFrozenError (checked first); amount > balance ->
    InsufficientFundsError; amount <= 0 -> ValueError.
    """

    def __init__(self, balance=0, frozen=False):
        ...

    def withdraw(self, amount):
        ...


class ValidationError(Exception):
    """Plain custom exception."""


def parse_age(text):
    """'42' -> 42. Non-integer text -> raise ValidationError(f'invalid age: {text!r}')
    chained from the original ValueError (`raise ... from err`).
    Outside 0..150 -> ValidationError('age out of range') (no cause).
    """
    ...


# ---- 10. Dependency inversion -------------------------------------------------------
class DuplicateUserError(Exception):
    """Raised when registering an existing user."""


class InMemoryUserRepo:
    """add(name), exists(name) -> bool, all_names() -> sorted list."""

    def __init__(self):
        ...

    def add(self, name):
        ...

    def exists(self, name):
        ...

    def all_names(self):
        ...


class UserService:
    """UserService(repo): the repo is INJECTED (any object with add/exists/all_names).
    register(name): normalise with strip().lower(); empty -> ValueError;
      already exists -> DuplicateUserError; otherwise repo.add and return the
      normalised name.
    list_users() -> repo.all_names()
    """

    def __init__(self, repo):
        ...

    def register(self, name):
        ...

    def list_users(self):
        ...
