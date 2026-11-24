import dataclasses

import pytest

from exercises import *


def make(*users):
    m = ExpenseManager()
    for u in users:
        m.add_user(u)
    return m


# ---- split strategies
def test_split_strategy_is_abstract():
    with pytest.raises(TypeError):
        SplitStrategy()


def test_equal_split_even():
    assert EqualSplit(["a", "b"]).split(100) == {"a": 50, "b": 50}


def test_equal_split_remainder_goes_to_first_participants():
    assert EqualSplit(["a", "b", "c"]).split(100) == {"a": 34, "b": 33, "c": 33}
    assert EqualSplit(["a", "b", "c"]).split(2) == {"a": 1, "b": 1, "c": 0}
    assert EqualSplit(["c", "a", "b"]).split(101) == {"c": 34, "a": 34, "b": 33}


def test_equal_split_never_loses_cents():
    for n in range(1, 9):
        ids = [f"u{i}" for i in range(n)]
        for amount in (1, 7, 100, 999, 10_001):
            out = EqualSplit(ids).split(amount)
            assert sum(out.values()) == amount
            assert max(out.values()) - min(out.values()) <= 1
            assert list(out) == ids


def test_equal_split_validation():
    with pytest.raises(InvalidSplitError):
        EqualSplit([])
    with pytest.raises(InvalidSplitError):
        EqualSplit(["a", "a"])


def test_exact_split():
    s = ExactSplit({"a": 70, "b": 30})
    assert s.split(100) == {"a": 70, "b": 30}
    with pytest.raises(InvalidSplitError):
        s.split(101)


def test_exact_split_returns_copy_and_validates():
    amounts = {"a": 1, "b": 2}
    s = ExactSplit(amounts)
    out = s.split(3)
    out["a"] = 999
    assert s.split(3) == {"a": 1, "b": 2}
    with pytest.raises(InvalidSplitError):
        ExactSplit({})
    with pytest.raises(InvalidSplitError):
        ExactSplit({"a": 150, "b": -50})


def test_percent_split_basic():
    assert PercentSplit({"a": 50, "b": 30, "c": 20}).split(1000) == {"a": 500, "b": 300, "c": 200}


def test_percent_split_remainder_rule():
    out = PercentSplit({"a": 33, "b": 33, "c": 34}).split(10001)
    assert out == {"a": 3301, "b": 3300, "c": 3400}
    assert sum(out.values()) == 10001


def test_percent_split_zero_percent_gets_nothing():
    assert PercentSplit({"a": 0, "b": 100}).split(1) == {"a": 0, "b": 1}


def test_percent_split_never_loses_cents():
    p = PercentSplit({"a": 33, "b": 33, "c": 17, "d": 17})
    for amount in range(1, 300):
        assert sum(p.split(amount).values()) == amount


def test_percent_split_validation():
    with pytest.raises(InvalidSplitError):
        PercentSplit({"a": 50, "b": 40})
    with pytest.raises(InvalidSplitError):
        PercentSplit({"a": 120, "b": -20})
    with pytest.raises(InvalidSplitError):
        PercentSplit({})


# ---- users, groups, expenses
def test_add_user_duplicate():
    m = make("a")
    with pytest.raises(DuplicateError):
        m.add_user("a")


def test_exception_hierarchy():
    for e in (UnknownUserError, DuplicateError, InvalidSplitError, SettlementError):
        assert issubclass(e, ExpenseError)


def test_add_expense_returns_expense_and_sequential_ids():
    m = make("a", "b", "c")
    e1 = m.add_expense("a", 300, EqualSplit(["a", "b", "c"]), "dinner")
    e2 = m.add_expense("b", 100, EqualSplit(["a", "b"]))
    assert dataclasses.is_dataclass(e1)
    assert e1.expense_id == 1 and e2.expense_id == 2
    assert e1.description == "dinner" and e1.paid_by == "a" and e1.amount_cents == 300
    assert e1.shares == {"a": 100, "b": 100, "c": 100}
    assert e1.group_id is None
    assert m.expenses() == [e1, e2]


def test_balances_after_equal_split():
    m = make("a", "b", "c")
    m.add_expense("a", 300, EqualSplit(["a", "b", "c"]))
    assert m.owes("b", "a") == 100 and m.owes("c", "a") == 100
    assert m.owes("a", "b") == 0 and m.owes("b", "c") == 0
    assert m.balances_for("a") == {"b": 100, "c": 100}
    assert m.balances_for("b") == {"a": -100}
    assert m.net_balance("a") == 200 and m.net_balance("b") == -100
    assert m.net_balances() == {"a": 200, "b": -100, "c": -100}


def test_payer_not_in_split():
    m = make("a", "b")
    m.add_expense("a", 500, ExactSplit({"b": 500}))
    assert m.owes("b", "a") == 500


def test_payer_only_participant_creates_no_debt():
    m = make("a", "b")
    m.add_expense("a", 500, EqualSplit(["a"]))
    assert m.balances_for("a") == {} and m.net_balances() == {}


def test_opposite_debts_are_netted():
    m = make("a", "b")
    m.add_expense("b", 500, ExactSplit({"a": 500}))   # a owes b 500
    m.add_expense("a", 200, ExactSplit({"b": 200}))   # b owes a 200
    assert m.owes("a", "b") == 300 and m.owes("b", "a") == 0
    assert m.balances_for("a") == {"b": -300}
    m.add_expense("a", 300, ExactSplit({"b": 300}))
    assert m.owes("a", "b") == 0 and m.owes("b", "a") == 0
    assert m.balances_for("a") == {}


def test_net_balances_sum_to_zero():
    m = make("a", "b", "c", "d")
    m.add_expense("a", 1001, EqualSplit(["a", "b", "c"]))
    m.add_expense("d", 777, PercentSplit({"a": 10, "b": 45, "d": 45}))
    m.add_expense("c", 50, EqualSplit(["a", "b", "c", "d"]))
    assert sum(m.net_balances().values()) == 0


def test_add_expense_validation_and_no_side_effects():
    m = make("a", "b")
    with pytest.raises(UnknownUserError):
        m.add_expense("zed", 100, EqualSplit(["a"]))
    with pytest.raises(UnknownUserError):
        m.add_expense("a", 100, EqualSplit(["a", "zed"]))
    for bad in (0, -5, 10.5, "100", True):
        with pytest.raises(InvalidSplitError):
            m.add_expense("a", bad, EqualSplit(["a", "b"]))
    with pytest.raises(InvalidSplitError):
        m.add_expense("a", 100, ExactSplit({"a": 10, "b": 10}))   # sums to 20
    assert m.expenses() == [] and m.net_balances() == {}
    assert m.add_expense("a", 100, EqualSplit(["a", "b"])).expense_id == 1


def test_owes_unknown_user():
    m = make("a")
    with pytest.raises(UnknownUserError):
        m.owes("a", "zed")
    with pytest.raises(UnknownUserError):
        m.owes("zed", "a")


# ---- groups
def test_groups():
    m = make("a", "b", "c")
    m.create_group("trip", ["a", "b"])
    with pytest.raises(DuplicateError):
        m.create_group("trip", ["a"])
    with pytest.raises(UnknownUserError):
        m.create_group("g2", ["a", "zed"])
    e = m.add_expense("a", 100, EqualSplit(["a", "b"]), group_id="trip")
    m.add_expense("a", 100, EqualSplit(["a", "c"]))                 # outside any group
    assert e.group_id == "trip"
    assert m.group_expenses("trip") == [e]
    assert m.owes("b", "a") == 50 and m.owes("c", "a") == 50        # balances are global


def test_group_membership_enforced():
    m = make("a", "b", "c")
    m.create_group("trip", ["a", "b"])
    with pytest.raises(InvalidSplitError):
        m.add_expense("a", 100, EqualSplit(["a", "c"]), group_id="trip")
    with pytest.raises(InvalidSplitError):
        m.add_expense("c", 100, EqualSplit(["a", "b"]), group_id="trip")
    with pytest.raises(UnknownUserError):
        m.add_expense("a", 100, EqualSplit(["a", "b"]), group_id="nope")
    with pytest.raises(UnknownUserError):
        m.group_expenses("nope")
    assert m.expenses() == []


# ---- settle up
def test_settle_up_partial_and_full():
    m = make("a", "b")
    m.add_expense("a", 1000, EqualSplit(["a", "b"]))                # b owes a 500
    m.settle_up("b", "a", 200)
    assert m.owes("b", "a") == 300
    m.settle_up("b", "a", 300)
    assert m.owes("b", "a") == 0
    assert m.balances_for("b") == {} and m.net_balances() == {}


def test_settle_up_errors_change_nothing():
    m = make("a", "b")
    m.add_expense("a", 1000, EqualSplit(["a", "b"]))
    with pytest.raises(SettlementError):
        m.settle_up("b", "a", 501)                                  # more than owed
    with pytest.raises(SettlementError):
        m.settle_up("a", "b", 1)                                    # wrong direction: a owes nothing
    with pytest.raises(SettlementError):
        m.settle_up("a", "a", 1)
    with pytest.raises(SettlementError):
        m.settle_up("b", "a", 0)
    with pytest.raises(SettlementError):
        m.settle_up("b", "a", -5)
    with pytest.raises(UnknownUserError):
        m.settle_up("b", "zed", 1)
    assert m.owes("b", "a") == 500


# ---- simplify
def test_simplify_empty():
    assert make("a", "b").simplify_debts() == []


def test_simplify_chain_collapses():
    m = make("a", "b", "c")
    m.add_expense("b", 10, ExactSplit({"a": 10}))                   # a owes b 10
    m.add_expense("c", 10, ExactSplit({"b": 10}))                   # b owes c 10
    assert m.simplify_debts() == [Transfer("a", "c", 10)]


def test_simplify_cycle_cancels_out():
    m = make("a", "b", "c")
    m.add_expense("b", 10, ExactSplit({"a": 10}))
    m.add_expense("c", 10, ExactSplit({"b": 10}))
    m.add_expense("a", 10, ExactSplit({"c": 10}))
    assert m.simplify_debts() == []


def _four_user_ledger():
    m = make("a", "b", "c", "d")
    m.add_expense("c", 30, ExactSplit({"a": 15, "b": 15}))
    m.add_expense("d", 70, ExactSplit({"a": 35, "b": 35}))
    return m                                                        # a:-50 b:-50 c:+30 d:+70


def test_simplify_greedy_order_and_tie_breaks():
    m = _four_user_ledger()
    assert m.net_balances() == {"a": -50, "b": -50, "c": 30, "d": 70}
    assert m.simplify_debts() == [
        Transfer("a", "d", 50),
        Transfer("b", "c", 30),
        Transfer("b", "d", 20),
    ]


def test_simplify_does_not_mutate_and_is_repeatable():
    m = _four_user_ledger()
    before = m.net_balances()
    first = m.simplify_debts()
    assert m.net_balances() == before
    assert m.simplify_debts() == first


def test_simplify_transfers_zero_every_balance():
    m = make("a", "b", "c", "d", "e")
    m.add_expense("a", 1003, EqualSplit(["a", "b", "c", "d"]))
    m.add_expense("e", 4000, PercentSplit({"a": 25, "b": 25, "c": 25, "e": 25}))
    m.add_expense("c", 123, ExactSplit({"d": 100, "e": 23}))
    net = dict(m.net_balances())
    transfers = m.simplify_debts()
    assert len(transfers) <= len(net) - 1
    for t in transfers:
        assert t.amount_cents > 0
        net[t.from_user] = net.get(t.from_user, 0) + t.amount_cents
        net[t.to_user] = net.get(t.to_user, 0) - t.amount_cents
    assert all(v == 0 for v in net.values())


def test_transfer_is_frozen_dataclass():
    t = Transfer("a", "b", 5)
    assert dataclasses.is_dataclass(t)
    with pytest.raises(dataclasses.FrozenInstanceError):
        t.amount_cents = 6
