"""LLD problem 08: Splitwise-style expense sharing. Read lesson.md.

Exceptions, dataclasses and the ABC are provided. Implement everything marked `...`.
ALL money is an int number of cents. Never use float for money.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ExpenseError(Exception):
    """Base class for all errors in this module."""


class UnknownUserError(ExpenseError):
    """A user id or group id that was never registered."""


class DuplicateError(ExpenseError):
    """add_user / create_group with an id that already exists."""


class InvalidSplitError(ExpenseError):
    """Bad amount, bad split definition, or a participant outside the group."""


class SettlementError(ExpenseError):
    """settle_up with self-payment, non-positive amount, or more than is owed."""


@dataclass(frozen=True)
class Expense:
    """expense_id (1, 2, 3, ...), description, paid_by, amount_cents,
    shares: dict[user_id, cents owed] (sums to amount_cents; the payer may appear),
    group_id (None if not in a group)."""
    expense_id: int
    description: str
    paid_by: str
    amount_cents: int
    shares: dict
    group_id: object = None


@dataclass(frozen=True)
class Transfer:
    """'from_user pays to_user amount_cents' - one step of a simplified settlement."""
    from_user: str
    to_user: str
    amount_cents: int


class SplitStrategy(ABC):
    """Abstract: split(amount_cents) -> dict[user_id, int].

    The result's keys are the participants in a deterministic order, values are
    non-negative ints, and sum(values) == amount_cents exactly (no lost cents).
    """

    @abstractmethod
    def split(self, amount_cents):
        ...


class EqualSplit(SplitStrategy):
    """EqualSplit(participants: list[str]).

    Empty list or duplicate ids -> InvalidSplitError (raised in __init__).
    share = amount // n for everyone; the remainder r = amount % n is handed out as
    one extra cent each to the FIRST r participants in the order given.
    e.g. EqualSplit(["a","b","c"]).split(100) == {"a": 34, "b": 33, "c": 33}.
    """

    def __init__(self, participants):
        ...

    def split(self, amount_cents):
        ...


class ExactSplit(SplitStrategy):
    """ExactSplit(amounts: dict[str, int]) - explicit cents per participant.

    Empty dict or any negative amount -> InvalidSplitError (in __init__).
    split(amount_cents) returns a copy of `amounts` (same order) but raises
    InvalidSplitError if sum(amounts.values()) != amount_cents.
    """

    def __init__(self, amounts):
        ...

    def split(self, amount_cents):
        ...


class PercentSplit(SplitStrategy):
    """PercentSplit(percents: dict[str, int]) - whole-number percentages.

    Empty dict, any negative percent, or sum != 100 -> InvalidSplitError (in __init__).
    split: base share = amount_cents * percent // 100 (floor) for each participant.
    The leftover cents (amount - sum of base shares) are handed out one extra cent each
    to participants WITH percent > 0, in the dict's insertion order, starting from the
    first. (The leftover is always smaller than the number of such participants.)
    e.g. {"a":33,"b":33,"c":34}.split(10001) == {"a":3301,"b":3300,"c":3400}.
    """

    def __init__(self, percents):
        ...

    def split(self, amount_cents):
        ...


class ExpenseManager:
    """ExpenseManager(). The whole in-memory ledger.

    Users / groups
    - add_user(user_id): DuplicateError if it exists.
    - create_group(group_id, member_ids): DuplicateError if the group exists,
      UnknownUserError if any member is not a registered user.
    - group_expenses(group_id) -> list[Expense] in creation order;
      UnknownUserError for an unknown group.

    Expenses
    - add_expense(paid_by, amount_cents, split, description="", group_id=None) -> Expense
        * amount_cents must be an int (not bool) > 0, else InvalidSplitError.
        * paid_by must be a registered user, every participant of the split must be a
          registered user, else UnknownUserError. Unknown group_id -> UnknownUserError.
        * if group_id is given, payer and every participant must be members of that
          group, else InvalidSplitError.
        * shares = split.split(amount_cents) (its InvalidSplitError propagates).
        * Each participant u != paid_by now owes paid_by shares[u] cents. The payer's
          own share creates no debt. The payer need not be a participant.
        * Expense ids are 1, 2, 3, ... A FAILED call must not consume an id or change
          any balance.
    - expenses() -> list[Expense] copy, in creation order.

    Balances (global across groups)
    - owes(debtor, creditor) -> int: the NET cents debtor owes creditor. Debts in
      opposite directions cancel: if a owes b 500 and b owes a 200, owes(a, b) == 300
      and owes(b, a) == 0. Unknown user -> UnknownUserError.
    - balances_for(user_id) -> dict[other_id, int]: only non-zero entries; positive =
      `other` owes user_id, negative = user_id owes `other`.
    - net_balance(user_id) -> int: sum of balances_for(user_id).values(); positive means
      the user is owed money overall.
    - net_balances() -> dict[user_id, int]: only users with non-zero net balance.
      The values always sum to 0.

    Settling
    - settle_up(payer, receiver, amount_cents): payer hands receiver real money, which
      reduces owes(payer, receiver) by amount_cents. UnknownUserError for unknown users;
      SettlementError if payer == receiver, amount is not an int > 0, or amount >
      owes(payer, receiver). A failed call changes nothing.
    - simplify_debts() -> list[Transfer]: does NOT modify the ledger. Using net
      balances, repeat until nobody is owed: pick the debtor with the LARGEST debt (ties:
      smallest user_id by normal string ordering) and the creditor with the LARGEST
      credit (ties: smallest user_id); emit Transfer(debtor, creditor, min(debt, credit))
      and reduce both. Returns transfers in emission order ([] if all settled).
      Executing every transfer zeroes every net balance, in at most (users - 1) steps.
    """

    def __init__(self):
        ...

    def add_user(self, user_id):
        ...

    def create_group(self, group_id, member_ids):
        ...

    def group_expenses(self, group_id):
        ...

    def add_expense(self, paid_by, amount_cents, split, description="", group_id=None):
        ...

    def expenses(self):
        ...

    def owes(self, debtor, creditor):
        ...

    def balances_for(self, user_id):
        ...

    def net_balance(self, user_id):
        ...

    def net_balances(self):
        ...

    def settle_up(self, payer, receiver, amount_cents):
        ...

    def simplify_debts(self):
        ...
