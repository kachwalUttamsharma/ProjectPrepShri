import pytest

from exercises import *


def test_temperature():
    t = Temperature(100)
    assert t.celsius == 100
    assert t.fahrenheit == 212
    t.fahrenheit = 32
    assert t.celsius == 0
    assert t.kelvin == pytest.approx(273.15)
    t.celsius = 25
    assert t.celsius == 25


def test_temperature_validation():
    with pytest.raises(ValueError):
        Temperature(-300)
    t = Temperature(0)
    with pytest.raises(ValueError):
        t.celsius = -273.16
    with pytest.raises(ValueError):
        t.fahrenheit = -1000
    assert t.celsius == 0
    with pytest.raises(AttributeError):
        t.kelvin = 5
    assert isinstance(Temperature.celsius, property)


def test_circle():
    c = Circle(2)
    assert c.diameter == 4
    assert c.area == pytest.approx(12.566370614)
    c.radius = 3
    assert c.diameter == 6
    with pytest.raises(ValueError):
        c.radius = 0
    with pytest.raises(ValueError):
        Circle(-1)
    with pytest.raises(AttributeError):
        c.area = 1


def test_vector_basics():
    v = Vector2D(1, 2)
    assert repr(v) == "Vector2D(1, 2)"
    assert str(v) == "(1, 2)"
    assert v == Vector2D(1, 2)
    assert v != Vector2D(2, 1)
    assert v != (1, 2)
    assert v + Vector2D(3, 4) == Vector2D(4, 6)
    assert v * 3 == Vector2D(3, 6)
    assert abs(Vector2D(3, 4)) == 5
    assert bool(Vector2D(0, 0)) is False
    assert bool(v) is True


def test_vector_hash():
    assert hash(Vector2D(1, 2)) == hash(Vector2D(1, 2))
    assert len({Vector2D(1, 2), Vector2D(1, 2), Vector2D(0, 0)}) == 2
    assert {Vector2D(1, 1): "a"}[Vector2D(1, 1)] == "a"


def test_version_ordering():
    vs = [Version("1.10.0"), Version("1.2.0"), Version("1.2"), Version("0.9.9")]
    assert [str(v) for v in sorted(vs)] == ["0.9.9", "1.2.0", "1.2", "1.10.0"]
    assert Version("1.10") > Version("1.9")
    assert Version("1.0") <= Version("1.0.0")
    assert Version("2.0") >= Version("1.99.99")
    assert max(vs) == Version("1.10.0")
    assert Version("1.0.3").parts == (1, 0, 3)


def test_version_eq_hash_repr():
    assert Version("1.0") == Version("1.0.0")
    assert hash(Version("1.0")) == hash(Version("1.0.0"))
    assert len({Version("1.0"), Version("1.0.0"), Version("1.1")}) == 2
    assert repr(Version("1.10.2")) == "Version('1.10.2')"
    assert str(Version("1.10.2")) == "1.10.2"
    assert Version("1.0") != "1.0"


def test_playlist():
    p = Playlist(["a", "b", "c"])
    assert len(p) == 3
    assert p[0] == "a" and p[-1] == "c"
    assert p[1:3] == ["b", "c"]
    assert list(p) == ["a", "b", "c"]
    assert list(p) == ["a", "b", "c"]
    assert "b" in p and "z" not in p
    assert bool(Playlist()) is False
    assert p.add("d") is p
    assert len(p) == 4


def test_playlist_copies_input():
    src = ["a"]
    p = Playlist(src)
    p.add("b")
    assert src == ["a"]


def test_countdown():
    c = Countdown(3)
    assert list(c) == [3, 2, 1]
    assert list(c) == [3, 2, 1]
    assert len(c) == 3
    assert sum(c) == 6
    assert list(Countdown(0)) == []


def test_person():
    assert Person.is_adult(18) is True
    assert Person.is_adult(17) is False
    p = Person.from_string(" Sam , 30")
    assert (p.name, p.age) == ("Sam", 30)
    assert isinstance(p, Person)
    q = Person.from_birth_year("Al", 2000)
    assert q.age == 26
    assert Person.from_birth_year("Al", 2000, current_year=2020).age == 20
    assert repr(p) == "Person('Sam', 30)"
    assert p.is_adult_person()


def test_person_classmethod_subclass():
    class Kid(Person):
        pass

    assert type(Kid.from_string("a,5")) is Kid


def test_card():
    a, b = Card("A", "spades"), Card("A", "spades")
    assert a == b and a is not b
    assert a != Card("K", "spades")
    assert len({a, b, Card("K", "hearts")}) == 2
    assert {a: 1}[b] == 1
    assert repr(a) == "Card('A', 'spades')"


def test_fraction():
    f = Fraction(2, 4)
    assert (f.numerator, f.denominator) == (1, 2)
    g = Fraction(2, -4)
    assert (g.numerator, g.denominator) == (-1, 2)
    assert Fraction(1, 2) + Fraction(1, 3) == Fraction(5, 6)
    assert Fraction(2, 3) * Fraction(3, 4) == Fraction(1, 2)
    assert hash(Fraction(1, 2)) == hash(Fraction(2, 4))
    assert repr(Fraction(1, 2)) == "Fraction(1, 2)"
    assert str(Fraction(1, 2)) == "1/2"
    assert str(Fraction(4, 2)) == "2"
    assert float(Fraction(1, 4)) == 0.25
    with pytest.raises(ZeroDivisionError):
        Fraction(1, 0)
    assert Fraction(3) == Fraction(6, 2)


def test_vault():
    v = PasswordVault("pw")
    v.set("pw", "email", "secret")
    v.set("pw", "bank", "1234")
    assert v.get("pw", "email") == "secret"
    assert v.keys("pw") == ["bank", "email"]
    with pytest.raises(PermissionError):
        v.get("bad", "email")
    with pytest.raises(PermissionError):
        v.set("bad", "x", "y")
    with pytest.raises(PermissionError):
        v.keys("bad")
    with pytest.raises(KeyError):
        v.get("pw", "nope")


def test_vault_mangled():
    v = PasswordVault("pw")
    assert not hasattr(v, "data")
    assert not hasattr(v, "master")
    assert "_PasswordVault__data" in vars(v)
    assert "_PasswordVault__master" in vars(v)
