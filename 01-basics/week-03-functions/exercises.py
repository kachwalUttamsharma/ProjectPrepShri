"""Week 3 exercises. Replace each `...` with your code."""


def square(n):
    """Return n squared."""
    ...


def power(base, exp=2):
    """Return base raised to exp. Default exp is 2. power(3) -> 9, power(2, 5) -> 32."""
    ...


def min_max(numbers):
    """Return (smallest, largest) of a non-empty list. min_max([3, 1, 2]) -> (1, 3).
    Hint: you may use min() and max()."""
    ...


def total(*nums):
    """Return the sum of any number of arguments. total() -> 0, total(1, 2, 3) -> 6."""
    ...


def make_greeting(name, greeting="Hello", punctuation="!"):
    """Return greeting + ', ' + name + punctuation.
    make_greeting('Sam') -> 'Hello, Sam!'
    make_greeting('Sam', punctuation='?') -> 'Hello, Sam?'"""
    ...


def describe(**info):
    """Take keyword arguments and return a string of 'key=value' pairs sorted by key,
    joined by ', '. describe(b=2, a=1) -> 'a=1, b=2'. describe() -> ''.
    Hint: info is a dict; sorted(info) gives sorted keys."""
    ...


def append_item(item, items=None):
    """Return a list with item added at the end. If items is given, return a NEW list
    (do not change the original). If not, start from an empty list.
    append_item(1) -> [1]; append_item(2, [1]) -> [1, 2].
    Each call with no items must return a fresh list (avoid the mutable default trap)."""
    ...


def factorial(n):
    """Recursive factorial (no loops). factorial(0) -> 1, factorial(5) -> 120.
    Base case: n <= 1."""
    ...


def fibonacci(n):
    """Return the n-th Fibonacci number, recursively. fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2).
    fibonacci(10) -> 55. (Slow for big n, that's fine for now.)"""
    ...


def sum_digits(n):
    """Return the sum of digits of a non-negative int, recursively.
    sum_digits(1234) -> 10. sum_digits(0) -> 0.
    Hint: n % 10 is the last digit, n // 10 is the rest."""
    ...


def is_palindrome(s):
    """Recursively check if s reads the same backwards, ignoring case.
    Empty and 1-char strings are palindromes. 'Racecar' -> True, 'abca' -> False.
    Hint: compare first and last, then recurse on s[1:-1]."""
    ...
