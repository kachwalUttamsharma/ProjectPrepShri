"""LLD problem 04: vending machine (State pattern). Read lesson.md for the spec.

Enums, exceptions and the State ABC are provided. Implement everything marked `...`.
All money is an int number of cents.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Coin(Enum):
    NICKEL = 5
    DIME = 10
    QUARTER = 25
    DOLLAR = 100


class VendingError(Exception):
    """Base class for all vending errors."""


class InvalidSelectionError(VendingError):
    """Unknown slot code."""


class SoldOutError(VendingError):
    """Slot exists but has quantity 0."""


class InsufficientFundsError(VendingError):
    """Balance is below the product price."""


class CannotMakeChangeError(VendingError):
    """Machine cannot return the exact change."""


class InvalidOperationError(VendingError):
    """Operation not allowed in the current state."""


class MachineOutOfServiceError(VendingError):
    """Machine is out of service."""


@dataclass(frozen=True)
class Product:
    """Fields: name: str, price: int (cents, > 0)."""


@dataclass(frozen=True)
class DispenseResult:
    """Fields: product: Product, change: tuple[Coin, ...] (largest coin first)."""


class Inventory:
    """Slots keyed by code (e.g. "A1"). Each slot holds one Product + a quantity.

    add_product(code, product, quantity): quantity < 0 -> ValueError. A new code
        creates the slot; an existing code with the SAME product adds to its
        quantity; an existing code with a DIFFERENT product -> ValueError.
    get_product(code) -> Product; unknown code -> InvalidSelectionError.
    quantity(code) -> int; unknown code -> InvalidSelectionError.
    is_available(code) -> bool: slot exists and quantity > 0 (False if unknown).
    take(code) -> Product: decrement quantity by 1 and return the product.
        Unknown -> InvalidSelectionError; quantity 0 -> SoldOutError.
    codes() -> sorted list of slot codes.
    """

    def __init__(self):
        ...

    def add_product(self, code, product, quantity):
        ...

    def get_product(self, code):
        ...

    def quantity(self, code):
        ...

    def is_available(self, code):
        ...

    def take(self, code):
        ...

    def codes(self):
        ...


class State(ABC):
    """Abstract state. Each concrete state has a class attribute `name` and
    implements the four events. `machine` is the VendingMachine (the context);
    states call helper methods on it and switch state through it. How the
    machine exposes those helpers is up to you."""

    name = ""

    @abstractmethod
    def insert_coin(self, machine, coin):
        ...

    @abstractmethod
    def select_product(self, machine, code):
        ...

    @abstractmethod
    def dispense(self, machine):
        ...

    @abstractmethod
    def cancel(self, machine):
        ...


class IdleState(State):
    """name = "idle". No money inserted.
    insert_coin: accept (balance += coin value), move to HasMoneyState.
    select_product / dispense: InvalidOperationError.
    cancel: returns [] (nothing to refund), stays idle.
    """

    name = "idle"

    def insert_coin(self, machine, coin):
        ...

    def select_product(self, machine, code):
        ...

    def dispense(self, machine):
        ...

    def cancel(self, machine):
        ...


class HasMoneyState(State):
    """name = "has_money". balance > 0, nothing selected yet.
    insert_coin: accept more money.
    select_product(code): checks in THIS order, each failure leaves the machine
        completely unchanged (still has_money, same balance/stock/inventory):
        1. unknown code -> InvalidSelectionError
        2. quantity 0 -> SoldOutError
        3. balance < price -> InsufficientFundsError
        4. change = balance - price must be made by greedy change-making (see
           VendingMachine) -> CannotMakeChangeError
        On success: inserted coins join the coin stock, change coins leave it,
        the inventory loses one unit, balance becomes 0, the pending sale (product +
        change) is stored, and the machine moves to DispensingState.
    dispense: InvalidOperationError.
    cancel: refund exactly the coins inserted (largest first) as a list, balance
        0, back to IdleState. Coin stock is unchanged.
    """

    name = "has_money"

    def insert_coin(self, machine, coin):
        ...

    def select_product(self, machine, code):
        ...

    def dispense(self, machine):
        ...

    def cancel(self, machine):
        ...


class DispensingState(State):
    """name = "dispensing". A sale was accepted; the product is waiting.
    dispense: return the DispenseResult, clear the pending sale, go to IdleState.
    insert_coin / select_product / cancel: InvalidOperationError.
    """

    name = "dispensing"

    def insert_coin(self, machine, coin):
        ...

    def select_product(self, machine, code):
        ...

    def dispense(self, machine):
        ...

    def cancel(self, machine):
        ...


class OutOfServiceState(State):
    """name = "out_of_service". Every event raises MachineOutOfServiceError."""

    name = "out_of_service"

    def insert_coin(self, machine, coin):
        ...

    def select_product(self, machine, code):
        ...

    def dispense(self, machine):
        ...

    def cancel(self, machine):
        ...


class VendingMachine:
    """VendingMachine(inventory, coin_stock=None).

    `coin_stock`: optional dict {Coin: count} of the machine's float; missing
    coins start at 0. The machine starts in IdleState.

    Properties / attributes:
      inventory   -> the Inventory passed in
      state       -> current State instance
      state_name  -> state.name ("idle", "has_money", "dispensing", "out_of_service")
      balance     -> int cents inserted for the current transaction
      coin_stock  -> NEW dict {Coin: int} with an entry for EVERY Coin (a copy;
                     mutating it must not affect the machine)

    Events (delegated to the current state):
      insert_coin(coin) -> None. A non-Coin argument -> ValueError (checked first,
          in every state except out_of_service).
      select_product(code) -> None
      dispense() -> DispenseResult
      cancel() -> list[Coin]

    Admin:
      set_out_of_service(): only from idle, else InvalidOperationError.
      restore(): only from out_of_service (-> idle), else InvalidOperationError.

    Greedy change-making: coins available for change = coin_stock PLUS the coins
    inserted this transaction. Walk denominations from largest to smallest; take
    min(available count, remaining // value) of each. If remaining != 0 at the end
    -> CannotMakeChangeError. (Greedy is a deliberate simplification; the lesson
    discusses where it fails and how DP fixes it.) `change` in DispenseResult is a
    tuple of Coin, largest first.
    """

    def __init__(self, inventory, coin_stock=None):
        ...

    @property
    def state(self):
        ...

    @property
    def state_name(self):
        ...

    @property
    def balance(self):
        ...

    @property
    def coin_stock(self):
        ...

    def insert_coin(self, coin):
        ...

    def select_product(self, code):
        ...

    def dispense(self):
        ...

    def cancel(self):
        ...

    def set_out_of_service(self):
        ...

    def restore(self):
        ...
