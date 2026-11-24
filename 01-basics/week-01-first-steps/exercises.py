"""Week 1 exercises. Replace each `...` with your code."""


def add(a, b):
    """Return the sum of a and b."""
    ...
    return a+b

def average(a, b, c):
    """Return the average of three numbers (a float)."""
    ...
    return float((a+b+c)/3)


def is_even(n):
    """Return True if n is even, else False. Hint: %"""
    ...
    return n%2==0


def minutes_to_hours_minutes(total_minutes):
    """Return (hours, minutes). e.g. 135 -> (2, 15). Hint: // and %"""
    ...
    return (total_minutes // 60, total_minutes % 60)

def greet(name, age):
    """Return 'Hello, Sam! You are 30 years old.' using an f-string."""
    ...
    return f"Hello, {name}! You are {age} years old."


def first_and_last(s):
    """Return the first and last characters joined. 'python' -> 'pn'"""
    ...
    return s[0]+s[-1]


def reverse(s):
    """Return s reversed. 'abc' -> 'cba'. Hint: slice with a step of -1."""
    ...
    return s[::-1]


def shout(s):
    """Return s in uppercase with '!' added at the end. 'hi' -> 'HI!'"""
    ...
    return s.upper()+"!"


def middle(s):
    """Return the middle character of an odd-length string. 'abcde' -> 'c'"""
    ...
    length = len(s)
    return s[int(length/2)];


def celsius_to_fahrenheit(c):
    """F = C * 9/5 + 32"""
    ...
    return c*(9/5)+32
