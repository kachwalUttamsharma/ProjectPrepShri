"""Week 2 exercises: encapsulation, properties, dunder methods.

Replace each `...`. Keep names and signatures.
"""
from functools import total_ordering
import math


class Temperature:
    """Temperature(celsius).

    - property `celsius` (get/set). Setting below -273.15 raises ValueError.
      The constructor must also validate (so assign through the property).
    - property `fahrenheit` (get/set): F = C * 9/5 + 32. Setting converts to
      Celsius and goes through the same validation.
    - read-only property `kelvin` = celsius + 273.15 (assigning raises AttributeError).
    """

    def __init__(self, celsius):
        ...


class Circle:
    """Circle(radius). `radius` is a property; must be > 0 else ValueError
    (also in the constructor).

    Read-only properties: `diameter` and `area` (math.pi * r ** 2).
    """

    def __init__(self, radius):
        ...


class Vector2D:
    """Immutable-ish 2D vector.

    - repr: 'Vector2D(1, 2)'   str: '(1, 2)'
    - == compares x and y (NotImplemented for other types)
    - hashable and consistent with ==  (hint: hash((x, y)))
    - v1 + v2 -> new Vector2D;  v * 3 -> new Vector2D (scalar on the right)
    - abs(v) -> length (float)   Hint: __abs__ and math.hypot
    - bool(v) is False only for the zero vector (__bool__)
    """

    def __init__(self, x, y):
        ...


@total_ordering
class Version:
    """Version('1.10.2') compares numerically, not as strings.

    - attribute `parts`: tuple of ints, e.g. (1, 10, 2)
    - __eq__ / __lt__ compare `parts` (hint: tuples compare element-wise).
      Missing parts count as zero: Version('1.0') == Version('1.0.0').
    - total_ordering gives you <=, >, >= (already applied).
    - repr: "Version('1.10.2')"; str: '1.10.2' (the original text)
    - hashable and consistent with == (careful with the '1.0' vs '1.0.0' case!
      hint: strip trailing zeros when hashing).
    """

    def __init__(self, text):
        ...

    def __eq__(self, other):
        ...

    def __lt__(self, other):
        ...


class Playlist:
    """A collection of song titles.

    Playlist(songs=()) copies the songs. Support:
    - len(p), bool(p) (empty -> False)
    - p[i] returns a title; p[1:3] returns a LIST of titles
    - iteration via __iter__ (must work repeatedly)
    - 'x' in p  (__contains__)
    - add(title): append and return self (so calls can be chained)
    """

    def __init__(self, songs=()):
        ...


class Countdown:
    """Countdown(start): iterating yields start, start-1, ..., 1.

    Must be re-iterable: `list(c) == list(c)`. Hint: make __iter__ a generator
    (use `yield`). len(c) == start.
    """

    def __init__(self, start):
        ...


class Person:
    """Person(name, age).

    - @staticmethod is_adult(age) -> age >= 18
    - @classmethod from_string('Sam,30') -> Person (use `cls`, strip spaces)
    - @classmethod from_birth_year(name, birth_year, current_year=2026)
    - repr: "Person('Sam', 30)"
    - instance method is_adult_person() uses the staticmethod.
    """

    def __init__(self, name, age):
        ...

    @staticmethod
    def is_adult(age):
        ...

    @classmethod
    def from_string(cls, text):
        ...

    @classmethod
    def from_birth_year(cls, name, birth_year, current_year=2026):
        ...

    def is_adult_person(self):
        ...


class Card:
    """Playing card Card(rank, suit), e.g. Card('A', 'spades').

    Equal when rank and suit match; hashable so a set removes duplicates and
    cards work as dict keys. repr: "Card('A', 'spades')".
    """

    def __init__(self, rank, suit):
        ...


class Fraction:
    """Fraction(num, den) always stored in lowest terms with den > 0.

    - den == 0 -> ZeroDivisionError
    - Fraction(2, -4) -> numerator -1, denominator 2   (attrs: numerator, denominator)
    - + and * with another Fraction -> new Fraction
    - == compares value; hashable; repr 'Fraction(1, 2)'; str '1/2' ('3' if den == 1)
    - float(f) works (__float__)
    Hint: math.gcd.
    """

    def __init__(self, numerator, denominator=1):
        ...


class PasswordVault:
    """Stores secrets behind a master password using name mangling.

    - PasswordVault(master)
    - set(master, key, value) / get(master, key)
    - wrong master -> PermissionError; missing key -> KeyError
    - store data in `self.__data` and password in `self.__master`
      (so `vault.__data` outside the class fails, and no plain `.data` attribute exists)
    - keys(master) -> sorted list of keys
    """

    def __init__(self, master):
        ...

    def set(self, master, key, value):
        ...

    def get(self, master, key):
        ...

    def keys(self, master):
        ...
