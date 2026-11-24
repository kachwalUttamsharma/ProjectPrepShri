from exercises import *


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_average():
    assert average(1, 2, 3) == 2
    assert average(1, 2, 4) == 7 / 3


def test_is_even():
    assert is_even(4) is True
    assert is_even(7) is False
    assert is_even(0) is True


def test_minutes_to_hours_minutes():
    assert minutes_to_hours_minutes(135) == (2, 15)
    assert minutes_to_hours_minutes(59) == (0, 59)


def test_greet():
    assert greet("Sam", 30) == "Hello, Sam! You are 30 years old."


def test_first_and_last():
    assert first_and_last("python") == "pn"


def test_reverse():
    assert reverse("abc") == "cba"
    assert reverse("") == ""


def test_shout():
    assert shout("hi") == "HI!"


def test_middle():
    assert middle("abcde") == "c"
    assert middle("x") == "x"


def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212
