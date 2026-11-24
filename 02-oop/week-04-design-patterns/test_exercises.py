import dataclasses

import pytest

from exercises import *


# 1
def test_engine_and_car():
    e = Engine(200)
    assert e.running is False
    car = Car("Civic", e)
    assert car.is_running is False
    assert car.start() == "Engine started (200 hp)"
    assert car.is_running is True and e.running is True


def test_car_swap_engine():
    old, new = Engine(100), Engine(300)
    car = Car("x", old)
    car.start()
    assert car.swap_engine(new) is old
    assert old.running is False
    assert car.is_running is False
    assert car.start() == "Engine started (300 hp)"
    assert not issubclass(Car, Engine)


# 2
def test_item():
    assert dataclasses.is_dataclass(Item)
    i = Item("pen", 2.5, 4)
    assert i.total == 10
    assert Item("a", 1).qty == 1
    assert Item("a", 1) == Item("a", 1)
    assert "Item(" in repr(i)
    with pytest.raises(ValueError):
        Item("a", -1)
    with pytest.raises(ValueError):
        Item("a", 1, 0)


def test_coordinate():
    c = Coordinate(1.0, 2.0)
    assert hash(c) == hash(Coordinate(1.0, 2.0))
    assert len({c, Coordinate(1.0, 2.0)}) == 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.lat = 5
    d = c.with_lat(9.0)
    assert d == Coordinate(9.0, 2.0) and c.lat == 1.0


def test_task_ordering():
    a, b, c = Task(3, "c"), Task(1, "a"), Task(2, "b")
    assert [t.name for t in sorted([a, b, c])] == ["a", "b", "c"]
    assert Task(1, "x") == Task(1, "different")  # name excluded from compare
    assert Task(1, "x").tags == []
    t1, t2 = Task(1, "a"), Task(1, "b")
    t1.tags.append("x")
    assert t2.tags == []


# 3
def test_status():
    assert Status.PENDING.value == "pending"
    assert [s.name for s in Status] == ["PENDING", "ACTIVE", "DONE"]
    assert Status("done") is Status.DONE
    assert parse_status("  Done ") is Status.DONE
    assert parse_status("ACTIVE") is Status.ACTIVE
    with pytest.raises(ValueError):
        parse_status("nope")


def test_direction():
    assert Direction.NORTH.turn_right() is Direction.EAST
    assert Direction.WEST.turn_right() is Direction.NORTH
    assert Direction.NORTH.turn_left() is Direction.WEST
    assert Direction.SOUTH.turn_left() is Direction.EAST


def test_priority_intenum():
    assert Priority.HIGH > Priority.LOW
    assert Priority.MEDIUM == 2
    assert sorted([Priority.HIGH, Priority.LOW, Priority.MEDIUM]) == [
        Priority.LOW,
        Priority.MEDIUM,
        Priority.HIGH,
    ]


# 4
class Sq:
    def draw(self):
        return "[]"


class Dot:
    def draw(self):
        return "."


def test_protocol():
    assert isinstance(Sq(), Drawable)
    assert not isinstance(object(), Drawable)
    assert render_all([Sq(), Dot(), Sq()]) == "[]\n.\n[]"
    assert render_all([]) == ""


# 5
def test_strategies():
    assert NoDiscount().apply(100) == 100
    assert PercentDiscount(25).apply(200) == 150
    assert FixedDiscount(30).apply(100) == 70
    assert FixedDiscount(500).apply(100) == 0
    for bad in (-1, 101):
        with pytest.raises(ValueError):
            PercentDiscount(bad)
    with pytest.raises(ValueError):
        FixedDiscount(-1)


def test_cart_strategy_swap():
    c = Cart()
    c.add(60)
    c.add(40)
    assert c.subtotal() == 100 and c.total() == 100
    c.set_strategy(PercentDiscount(10))
    assert c.total() == 90
    c.set_strategy(FixedDiscount(15))
    assert c.total() == 85
    assert Cart(PercentDiscount(50)).total() == 0


# 6
def test_factory():
    assert isinstance(create_notifier("email"), EmailNotifier)
    assert isinstance(create_notifier("SMS"), SmsNotifier)
    assert create_notifier("push").send("hi") == "[push] hi"
    assert create_notifier("email").send("yo") == "[email] yo"
    assert create_notifier("sms").send("yo") == "[sms] yo"
    with pytest.raises(ValueError):
        create_notifier("pigeon")


def test_factory_register():
    class Slack:
        def send(self, m):
            return f"[slack] {m}"

    register_notifier("Slack", Slack)
    assert create_notifier("slack").send("x") == "[slack] x"


# 7
def test_emitter():
    em, log = EventEmitter(), []
    h1 = lambda *a, **k: log.append(("h1", a, k))
    h2 = lambda *a, **k: log.append(("h2", a, k))
    em.subscribe("save", h1)
    em.subscribe("save", h2)
    assert em.emit("save", 1, x=2) == 2
    assert log == [("h1", (1,), {"x": 2}), ("h2", (1,), {"x": 2})]
    assert em.emit("other") == 0
    em.unsubscribe("save", h1)
    em.unsubscribe("save", h1)  # no error
    assert em.emit("save") == 1


def test_emitter_self_unsubscribe():
    em, calls = EventEmitter(), []

    def once():
        calls.append("once")
        em.unsubscribe("e", once)

    em.subscribe("e", once)
    em.subscribe("e", lambda: calls.append("other"))
    assert em.emit("e") == 2
    assert calls == ["once", "other"]
    assert em.emit("e") == 1


# 8
def test_singleton():
    Config.reset_instance()
    a, b = Config(), Config()
    assert a is b
    a.set("debug", True)
    assert Config().get("debug") is True
    assert Config().get("missing", 7) == 7
    assert Config().get("missing") is None


def test_singleton_reset():
    Config.reset_instance()
    a = Config()
    a.set("k", 1)
    Config.reset_instance()
    b = Config()
    assert b is not a
    assert b.get("k") is None


# 9
def test_exception_hierarchy():
    assert issubclass(InsufficientFundsError, BankError)
    assert issubclass(AccountFrozenError, BankError)
    assert issubclass(BankError, Exception)


def test_wallet_errors():
    w = Wallet(10)
    with pytest.raises(InsufficientFundsError) as ei:
        w.withdraw(50)
    assert ei.value.balance == 10 and ei.value.requested == 50
    assert str(ei.value) == "Insufficient funds: balance 10, requested 50"
    with pytest.raises(BankError):
        w.withdraw(50)
    with pytest.raises(AccountFrozenError):
        Wallet(1000, frozen=True).withdraw(1)
    with pytest.raises(ValueError):
        w.withdraw(0)
    assert w.withdraw(4) == 6


def test_parse_age():
    assert parse_age("42") == 42
    with pytest.raises(ValidationError) as ei:
        parse_age("abc")
    assert str(ei.value) == "invalid age: 'abc'"
    assert isinstance(ei.value.__cause__, ValueError)
    with pytest.raises(ValidationError, match="out of range") as ei:
        parse_age("200")
    assert ei.value.__cause__ is None
    with pytest.raises(ValidationError):
        parse_age("-1")


# 10
def test_user_service():
    svc = UserService(InMemoryUserRepo())
    assert svc.register("  Sam ") == "sam"
    assert svc.register("Ann") == "ann"
    assert svc.list_users() == ["ann", "sam"]
    with pytest.raises(DuplicateUserError):
        svc.register("SAM")
    with pytest.raises(ValueError):
        svc.register("   ")


def test_user_service_uses_injected_repo():
    class FakeRepo:
        def __init__(self):
            self.calls = []

        def add(self, name):
            self.calls.append(("add", name))

        def exists(self, name):
            self.calls.append(("exists", name))
            return False

        def all_names(self):
            return ["zed"]

    repo = FakeRepo()
    svc = UserService(repo)
    assert svc.register("Bob") == "bob"
    assert ("add", "bob") in repo.calls
    assert svc.list_users() == ["zed"]


def test_repo():
    r = InMemoryUserRepo()
    r.add("b")
    r.add("a")
    assert r.exists("a") and not r.exists("c")
    assert r.all_names() == ["a", "b"]
