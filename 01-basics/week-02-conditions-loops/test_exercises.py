from exercises import *


def test_sign():
    assert sign(5) == "positive"
    assert sign(-2) == "negative"
    assert sign(0) == "zero"
    assert sign(0.5) == "positive"


def test_grade():
    assert grade(100) == "A"
    assert grade(90) == "A"
    assert grade(89) == "B"
    assert grade(80) == "B"
    assert grade(79) == "C"
    assert grade(70) == "C"
    assert grade(69) == "D"
    assert grade(60) == "D"
    assert grade(59) == "F"
    assert grade(0) == "F"


def test_sum_to_n():
    assert sum_to_n(0) == 0
    assert sum_to_n(1) == 1
    assert sum_to_n(10) == 55
    assert sum_to_n(100) == 5050


def test_count_vowels():
    assert count_vowels("") == 0
    assert count_vowels("rhythm") == 0
    assert count_vowels("Hello World") == 3
    assert count_vowels("AEIOUaeiou") == 10


def test_fizzbuzz():
    assert fizzbuzz(0) == []
    assert fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]
    result = fizzbuzz(15)
    assert len(result) == 15
    assert result[14] == "FizzBuzz"
    assert result[2] == "Fizz"
    assert result[9] == "Buzz"
    assert result[10] == "11"


def test_factorial():
    assert factorial(0) == 1
    assert factorial(1) == 1
    assert factorial(5) == 120
    assert factorial(10) == 3628800


def test_is_prime():
    assert is_prime(0) is False
    assert is_prime(1) is False
    assert is_prime(-7) is False
    assert is_prime(2) is True
    assert is_prime(3) is True
    assert is_prime(4) is False
    assert is_prime(17) is True
    assert is_prime(21) is False
    assert is_prime(97) is True


def test_collatz_steps():
    assert collatz_steps(1) == 0
    assert collatz_steps(2) == 1
    assert collatz_steps(6) == 8
    assert collatz_steps(27) == 111


def test_first_repeated_char():
    assert first_repeated_char("abcba") == "b"
    assert first_repeated_char("abc") is None
    assert first_repeated_char("") is None
    assert first_repeated_char("aab") == "a"
    assert first_repeated_char("abba") == "b"


def test_right_triangle():
    assert right_triangle(0) == ""
    assert right_triangle(1) == "*"
    assert right_triangle(3) == "*\n**\n***"
