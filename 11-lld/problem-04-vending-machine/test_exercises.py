import dataclasses

import pytest

from exercises import *

CHIPS = Product("Chips", 65)
GUM = Product("Gum", 50)
WATER = Product("Water", 100)


def make_inventory():
    inv = Inventory()
    inv.add_product("A1", CHIPS, 2)
    inv.add_product("A2", GUM, 1)
    inv.add_product("B1", WATER, 0)
    return inv


def make_machine(stock=None, inv=None):
    if stock is None:
        stock = {Coin.NICKEL: 5, Coin.DIME: 5, Coin.QUARTER: 5}
    return VendingMachine(inv or make_inventory(), stock)


def insert(m, *coins):
    for c in coins:
        m.insert_coin(c)


# ---- value objects
def test_coin_values():
    assert [c.value for c in Coin] == [5, 10, 25, 100]


def test_product_and_result_are_frozen_dataclasses():
    assert dataclasses.is_dataclass(CHIPS) and dataclasses.is_dataclass(DispenseResult)
    assert CHIPS == Product("Chips", 65) and hash(CHIPS) == hash(Product("Chips", 65))
    with pytest.raises(dataclasses.FrozenInstanceError):
        CHIPS.price = 1
    r = DispenseResult(CHIPS, (Coin.DIME,))
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.change = ()


def test_error_hierarchy():
    for exc in (InvalidSelectionError, SoldOutError, InsufficientFundsError,
                CannotMakeChangeError, InvalidOperationError, MachineOutOfServiceError):
        assert issubclass(exc, VendingError)


# ---- inventory
def test_inventory_basics():
    inv = make_inventory()
    assert inv.codes() == ["A1", "A2", "B1"]
    assert inv.get_product("A1") == CHIPS and inv.quantity("A1") == 2
    assert inv.is_available("A1") and not inv.is_available("B1") and not inv.is_available("Z9")


def test_inventory_take():
    inv = make_inventory()
    assert inv.take("A2") == GUM
    assert inv.quantity("A2") == 0
    with pytest.raises(SoldOutError):
        inv.take("A2")
    with pytest.raises(SoldOutError):
        inv.take("B1")
    with pytest.raises(InvalidSelectionError):
        inv.take("Z9")


def test_inventory_unknown_code():
    inv = make_inventory()
    with pytest.raises(InvalidSelectionError):
        inv.get_product("Z9")
    with pytest.raises(InvalidSelectionError):
        inv.quantity("Z9")


def test_inventory_restock_and_conflicts():
    inv = make_inventory()
    inv.add_product("A1", CHIPS, 3)
    assert inv.quantity("A1") == 5
    with pytest.raises(ValueError):
        inv.add_product("A1", GUM, 1)
    with pytest.raises(ValueError):
        inv.add_product("C1", GUM, -1)
    assert "C1" not in inv.codes()


# ---- initial state
def test_initial_state():
    m = make_machine()
    assert m.state_name == "idle" and isinstance(m.state, IdleState)
    assert m.balance == 0


def test_state_is_abstract():
    with pytest.raises(TypeError):
        State()


def test_coin_stock_defaults_and_is_a_copy():
    m = VendingMachine(make_inventory())
    assert m.coin_stock == {c: 0 for c in Coin}
    s = m.coin_stock
    s[Coin.DIME] = 99
    assert m.coin_stock[Coin.DIME] == 0


# ---- idle / has_money
def test_insert_coin_moves_to_has_money():
    m = make_machine()
    m.insert_coin(Coin.QUARTER)
    assert m.state_name == "has_money" and isinstance(m.state, HasMoneyState)
    assert m.balance == 25
    insert(m, Coin.DIME, Coin.NICKEL)
    assert m.balance == 40


def test_insert_non_coin_rejected():
    m = make_machine()
    with pytest.raises(ValueError):
        m.insert_coin(25)
    assert m.state_name == "idle" and m.balance == 0


def test_idle_rejects_select_and_dispense_and_cancel_is_noop():
    m = make_machine()
    with pytest.raises(InvalidOperationError):
        m.select_product("A1")
    with pytest.raises(InvalidOperationError):
        m.dispense()
    assert m.cancel() == []
    assert m.state_name == "idle"


def test_has_money_rejects_dispense():
    m = make_machine()
    m.insert_coin(Coin.DOLLAR)
    with pytest.raises(InvalidOperationError):
        m.dispense()


def test_select_unknown_code():
    m = make_machine()
    m.insert_coin(Coin.DOLLAR)
    with pytest.raises(InvalidSelectionError):
        m.select_product("Z9")
    assert m.state_name == "has_money" and m.balance == 100


def test_select_sold_out_checked_before_funds():
    m = make_machine()
    m.insert_coin(Coin.NICKEL)
    with pytest.raises(SoldOutError):
        m.select_product("B1")
    assert m.state_name == "has_money" and m.balance == 5


def test_insufficient_funds_then_top_up():
    m = make_machine()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    with pytest.raises(InsufficientFundsError):
        m.select_product("A1")
    assert m.balance == 50 and m.state_name == "has_money"
    insert(m, Coin.QUARTER)
    m.select_product("A1")
    assert m.state_name == "dispensing"


# ---- successful sale
def test_exact_payment():
    m = make_machine()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")
    assert m.state_name == "dispensing" and isinstance(m.state, DispensingState)
    assert m.balance == 0
    result = m.dispense()
    assert result == DispenseResult(GUM, ())
    assert m.state_name == "idle"
    assert m.inventory.quantity("A2") == 0


def test_exact_payment_adds_coins_to_stock():
    m = make_machine({})
    insert(m, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")
    stock = m.coin_stock
    assert stock[Coin.QUARTER] == 2 and stock[Coin.DOLLAR] == 0


def test_change_comes_from_stock_largest_first():
    m = make_machine()
    m.insert_coin(Coin.DOLLAR)
    m.select_product("A1")  # 35 change
    result = m.dispense()
    assert result.product == CHIPS
    assert result.change == (Coin.QUARTER, Coin.DIME)
    stock = m.coin_stock
    assert stock[Coin.DOLLAR] == 1 and stock[Coin.QUARTER] == 4 and stock[Coin.DIME] == 4
    assert stock[Coin.NICKEL] == 5


def test_change_may_use_just_inserted_coins():
    m = make_machine({})
    insert(m, Coin.QUARTER, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")  # 75 - 50 = 25 from inserted quarter
    assert m.dispense().change == (Coin.QUARTER,)
    assert m.coin_stock[Coin.QUARTER] == 2


def test_inventory_decremented_once_per_sale():
    m = make_machine()
    insert(m, Coin.DOLLAR)
    m.select_product("A1")
    m.dispense()
    assert m.inventory.quantity("A1") == 1


def test_two_sales_in_a_row_and_sold_out():
    m = make_machine()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")
    m.dispense()
    m.insert_coin(Coin.DOLLAR)
    with pytest.raises(SoldOutError):
        m.select_product("A2")
    m.select_product("A1")
    assert m.dispense().product == CHIPS


# ---- change failures
def test_cannot_make_change_leaves_everything_unchanged():
    m = make_machine({})
    m.insert_coin(Coin.DOLLAR)
    with pytest.raises(CannotMakeChangeError):
        m.select_product("A1")  # needs 35 back, machine has nothing
    assert m.state_name == "has_money" and m.balance == 100
    assert m.inventory.quantity("A1") == 2
    assert m.coin_stock == {c: 0 for c in Coin}
    assert m.cancel() == [Coin.DOLLAR]


def test_greedy_change_with_limited_stock_fails_when_greedy_gets_stuck():
    # Needs 30 back. Greedy takes the only quarter, then cannot make 5.
    # (A DP solution would use 3 dimes; this spec deliberately says greedy.)
    m = make_machine({Coin.QUARTER: 1, Coin.DIME: 3})
    m.insert_coin(Coin.DOLLAR)
    inv_product = Product("Mints", 70)
    m.inventory.add_product("C1", inv_product, 1)
    with pytest.raises(CannotMakeChangeError):
        m.select_product("C1")
    assert m.balance == 100 and m.inventory.quantity("C1") == 1


def test_change_uses_smaller_coins_when_large_exhausted():
    m = make_machine({Coin.DIME: 2, Coin.NICKEL: 1})
    m.insert_coin(Coin.DOLLAR)
    m.inventory.add_product("C1", Product("Mints", 75), 1)
    m.select_product("C1")  # 25 back = 10 + 10 + 5
    assert m.dispense().change == (Coin.DIME, Coin.DIME, Coin.NICKEL)
    assert m.coin_stock[Coin.DIME] == 0 and m.coin_stock[Coin.NICKEL] == 0


# ---- dispensing state
def test_dispensing_state_rejects_other_events():
    m = make_machine()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")
    with pytest.raises(InvalidOperationError):
        m.insert_coin(Coin.DIME)
    with pytest.raises(InvalidOperationError):
        m.select_product("A1")
    with pytest.raises(InvalidOperationError):
        m.cancel()
    assert m.state_name == "dispensing"


def test_dispense_twice_fails():
    m = make_machine()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    m.select_product("A2")
    m.dispense()
    with pytest.raises(InvalidOperationError):
        m.dispense()


# ---- cancel
def test_cancel_refunds_inserted_coins_largest_first():
    m = make_machine()
    insert(m, Coin.DIME, Coin.QUARTER, Coin.NICKEL)
    before = m.coin_stock
    assert m.cancel() == [Coin.QUARTER, Coin.DIME, Coin.NICKEL]
    assert m.balance == 0 and m.state_name == "idle"
    assert m.coin_stock == before


def test_cancel_refunds_even_when_stock_empty():
    m = make_machine({})
    insert(m, Coin.DIME, Coin.DIME, Coin.DIME)
    assert m.cancel() == [Coin.DIME] * 3


def test_cancel_then_new_transaction():
    m = make_machine()
    insert(m, Coin.DOLLAR)
    m.cancel()
    insert(m, Coin.QUARTER, Coin.QUARTER)
    assert m.balance == 50


# ---- out of service
def test_out_of_service_blocks_everything():
    m = make_machine()
    m.set_out_of_service()
    assert m.state_name == "out_of_service" and isinstance(m.state, OutOfServiceState)
    with pytest.raises(MachineOutOfServiceError):
        m.insert_coin(Coin.DIME)
    with pytest.raises(MachineOutOfServiceError):
        m.select_product("A1")
    with pytest.raises(MachineOutOfServiceError):
        m.dispense()
    with pytest.raises(MachineOutOfServiceError):
        m.cancel()


def test_restore():
    m = make_machine()
    m.set_out_of_service()
    m.restore()
    assert m.state_name == "idle"
    m.insert_coin(Coin.DIME)
    assert m.balance == 10


def test_set_out_of_service_only_from_idle():
    m = make_machine()
    m.insert_coin(Coin.DIME)
    with pytest.raises(InvalidOperationError):
        m.set_out_of_service()
    assert m.state_name == "has_money"


def test_restore_only_from_out_of_service():
    m = make_machine()
    with pytest.raises(InvalidOperationError):
        m.restore()
