import pytest

from exercises import *


def test_point():
    p = Point(3, 4)
    assert (p.x, p.y) == (3, 4)
    assert p.distance_to(Point()) == 5.0
    assert p.translate(1, -1) is None
    assert (p.x, p.y) == (4, 3)
    q = Point()
    assert (q.x, q.y) == (0, 0)


def test_counter():
    c = Counter(5)
    assert c.value == 5
    c.increment()
    c.increment(10)
    assert c.value == 16
    c.decrement(6)
    assert c.value == 10
    c.reset()
    assert c.value == 5
    assert Counter().value == 0


def test_counters_independent():
    a, b = Counter(), Counter()
    a.increment()
    assert b.value == 0


def test_bank_account_basic():
    a = BankAccount("Sam", 100)
    assert a.owner == "Sam"
    assert a.deposit(50) == 150
    assert a.withdraw(30) == 120
    assert a.balance == 120
    assert BankAccount("Z").balance == 0


def test_bank_account_errors():
    a = BankAccount("Sam", 100)
    with pytest.raises(ValueError):
        a.deposit(0)
    with pytest.raises(ValueError):
        a.withdraw(-5)
    with pytest.raises(ValueError, match="insufficient funds"):
        a.withdraw(101)
    with pytest.raises(ValueError):
        BankAccount("X", -1)
    assert a.balance == 100


def test_transfer():
    a, b = BankAccount("a", 100), BankAccount("b", 10)
    a.transfer_to(b, 40)
    assert (a.balance, b.balance) == (60, 50)
    with pytest.raises(ValueError):
        a.transfer_to(b, 1000)
    assert (a.balance, b.balance) == (60, 50)


def test_rectangle():
    r = Rectangle(2, 3)
    assert r.area() == 6
    assert r.perimeter() == 10
    assert not r.is_square()
    assert Rectangle(4, 4).is_square()
    assert r.scale(2) is None
    assert (r.width, r.height) == (4, 6)
    with pytest.raises(ValueError):
        Rectangle(0, 1)
    with pytest.raises(ValueError):
        Rectangle(1, -1)


def test_student():
    s = Student("Ann")
    assert s.average() == 0.0
    assert s.highest() is None
    s.add_grade(80)
    s.add_grade(100)
    assert s.average() == 90
    assert s.highest() == 100
    with pytest.raises(ValueError):
        s.add_grade(101)
    with pytest.raises(ValueError):
        s.add_grade(-1)
    assert s.grades == [80, 100]


def test_student_grades_not_shared():
    a, b = Student("a"), Student("b")
    a.add_grade(50)
    assert b.grades == []


def test_dog_class_attributes():
    start = Dog.count
    d1, d2 = Dog("Rex"), Dog("Fido")
    assert Dog.count == start + 2
    assert d1.species == d2.species == "Canis familiaris"
    assert "count" not in vars(d1)
    assert "species" not in vars(d1)


def test_dog_tricks():
    d1, d2 = Dog("a"), Dog("b")
    d1.add_trick("sit")
    d1.add_trick("sit")
    assert d1.tricks == ["sit"]
    assert d2.tricks == []
    src = ["roll"]
    d3 = Dog("c", src)
    d3.add_trick("beg")
    assert src == ["roll"]  # argument must not be mutated
    assert d3.tricks == ["roll", "beg"]


def test_stack():
    s = Stack()
    assert s.is_empty() and s.size() == 0
    s.push(1)
    s.push(2)
    assert s.peek() == 2
    assert s.size() == 2
    assert s.pop() == 2
    assert s.pop() == 1
    assert s.is_empty()


def test_stack_empty_errors():
    s = Stack()
    with pytest.raises(IndexError, match="stack is empty"):
        s.pop()
    with pytest.raises(IndexError, match="stack is empty"):
        s.peek()


def test_cart():
    c = ShoppingCart()
    assert c.total() == 0 and c.item_count() == 0
    c.add("apple", 0.5, 4)
    c.add("pen", 2)
    c.add("apple", 99, 2)  # price stays 0.5
    assert c.item_count() == 7
    assert c.total() == pytest.approx(0.5 * 6 + 2)
    c.remove("pen")
    assert c.item_count() == 6
    with pytest.raises(KeyError):
        c.remove("pen")
    with pytest.raises(ValueError):
        c.add("x", -1)
    with pytest.raises(ValueError):
        c.add("x", 1, 0)


def test_team():
    a, b = Team("a"), Team("b")
    assert a.add("x") is True
    assert a.add("x") is False
    assert a.size() == 1 and b.size() == 0
    assert a in Team.all_teams and b in Team.all_teams


def test_make_points():
    pts = make_points([(1, 2), (3, 4)])
    assert all(isinstance(p, Point) for p in pts)
    assert [(p.x, p.y) for p in pts] == [(1, 2), (3, 4)]
    assert make_points([]) == []


def test_farthest():
    pts = make_points([(1, 1), (-5, 0), (2, 2)])
    assert farthest_from_origin(pts) is pts[1]
    assert farthest_from_origin([]) is None
