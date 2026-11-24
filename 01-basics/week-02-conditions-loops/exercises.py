"""Week 2 exercises. Replace each `...` with your code."""


def sign(n):
    """Return 'positive', 'negative' or 'zero' for the number n."""
    ...


def grade(score):
    """Return a letter: 90+ 'A', 80-89 'B', 70-79 'C', 60-69 'D', below 60 'F'.
    Hint: if / elif / else, check from the highest down."""
    ...


def sum_to_n(n):
    """Return 1 + 2 + ... + n. sum_to_n(0) -> 0. Hint: accumulator + range(1, n + 1)."""
    ...


def count_vowels(s):
    """Return how many vowels (a, e, i, o, u, either case) are in s."""
    ...


def fizzbuzz(n):
    """Return a list of strings for 1..n: 'Fizz' if divisible by 3, 'Buzz' if by 5,
    'FizzBuzz' if by both, otherwise the number as a string.
    fizzbuzz(5) -> ['1', '2', 'Fizz', '4', 'Buzz']
    Hint: check divisibility by 15 FIRST."""
    ...


def factorial(n):
    """Return n! = 1 * 2 * ... * n, with 0! = 1. Hint: accumulator starting at 1."""
    ...


def is_prime(n):
    """Return True if n is a prime number (only divisible by 1 and itself).
    Numbers below 2 are not prime. Hint: try divisors 2..n-1 and return False early."""
    ...


def collatz_steps(n):
    """Starting at n (>= 1): if even, n = n // 2; if odd, n = 3 * n + 1.
    Return how many steps until n becomes 1. collatz_steps(6) -> 8
    (6,3,10,5,16,8,4,2,1). collatz_steps(1) -> 0. Hint: while loop."""
    ...


def first_repeated_char(s):
    """Return the first character that appears a second time while scanning left to right,
    or None if there is none. 'abcba' -> 'b'. 'abc' -> None.
    Hint: keep a string of characters seen so far; use `in` and an early return."""
    ...


def right_triangle(n):
    """Return a string with n lines; line i has i '*' characters. Lines are joined with
    '\\n' and there is no trailing newline. right_triangle(3) -> '*\\n**\\n***'
    Hint: build a list of lines, then '\\n'.join(lines). Return '' for n = 0."""
    ...
