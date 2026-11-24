import pytest

from exercises import *


def test_copy_pair():
    orig = {"a": [1, 2], "b": {"c": [3]}}
    shallow, deep = copy_pair(orig)
    assert shallow == deep == orig
    assert shallow is not orig and deep is not orig
    assert shallow["a"] is orig["a"]          # shallow shares inner objects
    assert deep["a"] is not orig["a"]
    assert deep["b"]["c"] is not orig["b"]["c"]
    orig["a"].append(99)
    assert shallow["a"] == [1, 2, 99]
    assert deep["a"] == [1, 2]


def test_money_equality_and_hash():
    a, b = Money(5, "USD"), Money(5, "USD")
    assert a == b and hash(a) == hash(b)
    assert a != Money(5, "EUR")
    assert (a == 5) is False
    assert len({a, b, Money(6, "USD")}) == 2
    assert {a: "x"}[b] == "x"


def test_money_immutable():
    m = Money(1, "USD")
    assert m.amount == 1 and m.currency == "USD"
    with pytest.raises(AttributeError):
        m.amount = 2


def test_slotted_point():
    p = SlottedPoint(1, 2)
    assert (p.x, p.y) == (1, 2)
    assert not hasattr(p, "__dict__")
    with pytest.raises(AttributeError):
        p.z = 3
    assert SlottedPoint.__slots__ == ("x", "y") or list(SlottedPoint.__slots__) == ["x", "y"]


def test_positive_descriptor():
    it = Item(10, 2)
    assert it.price == 10 and it.qty == 2
    with pytest.raises(ValueError):
        it.price = 0
    with pytest.raises(ValueError):
        Item(1, -1)
    it.price = 5
    assert it.price == 5
    # per-instance storage, not shared on the descriptor
    other = Item(7, 1)
    assert it.price == 5 and other.price == 7
    assert isinstance(Item.price, Positive)


def test_top_words():
    text = "the cat and The dog and the bird"
    assert top_words(text, 2) == [("the", 3), ("and", 2)]
    assert top_words("b a c a b", 3) == [("a", 2), ("b", 2), ("c", 1)]
    assert top_words("", 3) == []


def test_group_by():
    r = group_by(["apple", "avocado", "banana", "blueberry", "cherry"], key=lambda s: s[0])
    assert r == {"a": ["apple", "avocado"], "b": ["banana", "blueberry"], "c": ["cherry"]}
    assert type(r) is dict
    assert group_by([], key=len) == {}
    with pytest.raises(KeyError):
        r["z"]  # plain dict: no default creation


def test_last_n():
    assert last_n(range(10), 3) == [7, 8, 9]
    assert last_n([1, 2], 5) == [1, 2]
    assert last_n((x for x in "abcd"), 2) == ["c", "d"]
    assert last_n([], 2) == []


def test_sort_employees_stable_multikey():
    rows = [
        {"name": "Zed", "dept": "eng", "salary": 100},
        {"name": "Amy", "dept": "eng", "salary": 100},
        {"name": "Bob", "dept": "eng", "salary": 200},
        {"name": "Cat", "dept": "art", "salary": 50},
    ]
    out = sort_employees(rows)
    assert [r["name"] for r in out] == ["Cat", "Bob", "Amy", "Zed"]
    assert [r["name"] for r in rows] == ["Zed", "Amy", "Bob", "Cat"]  # input untouched


def test_task_dataclass():
    t1 = Task(2, "write")
    t2 = Task(1, "read", ("x",))
    assert t1.tags == ()
    assert t2 < t1
    assert sorted([t1, t2]) == [t2, t1]
    assert Task(1, "different title") == Task(1, "other title")  # title excluded from compare
    with pytest.raises(Exception):
        t1.priority = 9                                          # frozen
    assert hash(t1) == hash(Task(2, "anything"))


def test_priority_enum():
    assert Priority.HIGH > Priority.LOW
    assert Priority.MEDIUM == 2
    assert sorted([Priority.HIGH, Priority.LOW]) == [Priority.LOW, Priority.HIGH]
    assert parse_priority("high") is Priority.HIGH
    assert parse_priority("  Low ") is Priority.LOW
    with pytest.raises(ValueError):
        parse_priority("urgent")


def test_stack_generic():
    s = Stack[int]()
    assert len(s) == 0
    s.push(1)
    s.push(2)
    assert s.peek() == 2 and len(s) == 2
    assert s.pop() == 2 and s.pop() == 1
    with pytest.raises(IndexError):
        s.pop()
    assert Stack[str].__origin__ is Stack


def test_describe_narrowing():
    assert describe(None) == "nothing"
    assert describe(True) == "bool"       # bool is a subclass of int: check it first
    assert describe(7) == "int:7"
    assert describe("hi") == "str:hi"
    assert describe([1, 2, 3]) == "list of 3"
    assert describe(2.5) == "other"


def test_cycle_collected():
    assert cycle_collected() is True
