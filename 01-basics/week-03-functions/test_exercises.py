import pytest
from exercises import *


def test_square():
    assert square(4) == 16
    assert square(-3) == 9
    assert square(0) == 0


def test_power():
    assert power(3) == 9
    assert power(2, 5) == 32
    assert power(exp=3, base=2) == 8
    assert power(5, 0) == 1


def test_min_max():
    assert min_max([3, 1, 2]) == (1, 3)
    assert min_max([7]) == (7, 7)
    assert min_max([-5, -1, -9]) == (-9, -1)


def test_total():
    assert total() == 0
    assert total(5) == 5
    assert total(1, 2, 3) == 6
    assert total(1.5, 2.5) == 4.0


def test_make_greeting():
    assert make_greeting("Sam") == "Hello, Sam!"
    assert make_greeting("Sam", "Hi") == "Hi, Sam!"
    assert make_greeting("Sam", punctuation="?") == "Hello, Sam?"
    assert make_greeting("Ann", greeting="Yo", punctuation=".") == "Yo, Ann."


def test_describe():
    assert describe() == ""
    assert describe(a=1) == "a=1"
    assert describe(b=2, a=1) == "a=1, b=2"
    assert describe(name="x", age=3) == "age=3, name=x"


def test_append_item():
    assert append_item(1) == [1]
    assert append_item(1) == [1]  # fresh list each time
    original = [1]
    result = append_item(2, original)
    assert result == [1, 2]
    assert original == [1]  # not modified


def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800


def test_fibonacci():
    assert [fibonacci(i) for i in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert fibonacci(15) == 610


def test_sum_digits():
    assert sum_digits(0) == 0
    assert sum_digits(7) == 7
    assert sum_digits(1234) == 10
    assert sum_digits(1000) == 1


def test_is_palindrome():
    assert is_palindrome("") is True
    assert is_palindrome("a") is True
    assert is_palindrome("Racecar") is True
    assert is_palindrome("abba") is True
    assert is_palindrome("abca") is False
    assert is_palindrome("ab") is False
