"""Week 3 exercises: inheritance, polymorphism, ABCs, MRO, duck typing.

Replace each `...`. Keep names and signatures.
"""
from abc import ABC, abstractmethod
import json
import math


# ---- 1. Animals: override + super() ---------------------------------------
class Animal:
    """Animal(name).

    speak() raises NotImplementedError (subclasses must override).
    describe() -> '<name> says <speak()>' (uses polymorphism; defined ONCE here).
    """

    def __init__(self, name):
        ...

    def speak(self):
        ...

    def describe(self):
        ...


class Dog(Animal):
    """speak() -> 'Woof'"""

    def speak(self):
        ...


class Cat(Animal):
    """speak() -> 'Meow'"""

    def speak(self):
        ...


class Puppy(Dog):
    """speak() -> the Dog sound lowercased plus '!' i.e. 'woof!' (call super())."""

    def speak(self):
        ...


def chorus(animals):
    """Return a list of every animal's describe() string."""
    ...


# ---- 2. Employee / Manager --------------------------------------------------
class Employee:
    """Employee(name, salary). annual_pay() -> salary.
    describe() -> '<name> earns <annual_pay()>'.
    """

    def __init__(self, name, salary):
        ...

    def annual_pay(self):
        ...

    def describe(self):
        ...


class Manager(Employee):
    """Manager(name, salary, reports=None): `reports` is a list of Employees (copied).

    annual_pay() -> super().annual_pay() + 1000 per report.
    add_report(employee) appends. describe() is inherited and must reflect the bonus.
    """

    def __init__(self, name, salary, reports=None):
        ...

    def add_report(self, employee):
        ...

    def annual_pay(self):
        ...


# ---- 3. Abstract shapes -----------------------------------------------------
class Shape(ABC):
    """Abstract: area() and perimeter() are abstractmethods.
    Concrete describe() -> '<ClassName> area=<area:.2f> perimeter=<perimeter:.2f>'
    """

    @abstractmethod
    def area(self):
        ...

    @abstractmethod
    def perimeter(self):
        ...

    def describe(self):
        ...


class Rectangle(Shape):
    """Rectangle(width, height)."""

    def __init__(self, width, height):
        ...

    def area(self):
        ...

    def perimeter(self):
        ...


class Square(Rectangle):
    """Square(side): reuse Rectangle via super().__init__."""

    def __init__(self, side):
        ...


class Circle(Shape):
    """Circle(radius)."""

    def __init__(self, radius):
        ...

    def area(self):
        ...

    def perimeter(self):
        ...


def total_area(shapes):
    """Sum of area() over any shapes."""
    ...


def largest_shape(shapes):
    """The shape with the biggest area, or None for an empty list."""
    ...


# ---- 4. MRO and cooperative super() ----------------------------------------
class A:
    """who() -> ['A']"""

    def who(self):
        ...


class B(A):
    """who() -> ['B'] + super().who()"""

    def who(self):
        ...


class C(A):
    """who() -> ['C'] + super().who()"""

    def who(self):
        ...


class D(B, C):
    """who() -> ['D'] + super().who().  D().who() should be ['D', 'B', 'C', 'A']."""

    def who(self):
        ...


def mro_names(cls):
    """Return the names of cls's MRO, e.g. mro_names(D) -> ['D','B','C','A','object']."""
    ...


# ---- 5. Duck typing ---------------------------------------------------------
class Duck:
    """quack() -> 'Quack!'"""

    def quack(self):
        ...


class Robot:
    """quack() -> 'Beep quack'"""

    def quack(self):
        ...


def make_it_quack(things):
    """Return the quack() result of every item that has a callable `quack`,
    skipping the rest. No isinstance checks! Hint: getattr(obj, 'quack', None).
    """
    ...


# ---- 6. Type checks ---------------------------------------------------------
def classify(obj):
    """Return one of 'bool','int','float','str','list','other'.
    Careful: isinstance(True, int) is True, so check bool first.
    """
    ...


# ---- 7. Mixin ---------------------------------------------------------------
class JsonMixin:
    """Adds to_json() -> json.dumps(vars(self), sort_keys=True)
    and @classmethod from_json(text) -> cls(**json.loads(text)).
    """

    def to_json(self):
        ...

    @classmethod
    def from_json(cls, text):
        ...


class User(JsonMixin):
    """User(name, age) plain attributes."""

    def __init__(self, name, age):
        ...


# ---- 8. Subclassing a built-in ---------------------------------------------
class CountingList(list):
    """A list that counts mutations in attribute `ops` (starts at 0).

    append -> +1, extend(iterable) -> + number of items added, pop -> +1.
    Must still behave as a list (indexing, len, iteration, init from iterable).
    Hint: super().append(x); materialize extend's argument with list() first.
    """

    def __init__(self, iterable=()):
        ...

    def append(self, item):
        ...

    def extend(self, items):
        ...

    def pop(self, *args):
        ...


# ---- 9. Template method -----------------------------------------------------
class Report(ABC):
    """generate() builds text from: header(), body_lines(), footer().

    generate() -> '\\n'.join(non-empty parts) where parts = [header()] +
    body_lines() + [footer()].
    Defaults: header() -> '== <title> ==' ; footer() -> '-- end --'.
    Abstract: `title` (property) and body_lines() -> list[str].
    """

    @property
    @abstractmethod
    def title(self):
        ...

    @abstractmethod
    def body_lines(self):
        ...

    def header(self):
        ...

    def footer(self):
        ...

    def generate(self):
        ...


class SalesReport(Report):
    """SalesReport(sales: dict name -> amount). title 'Sales'.
    body_lines: 'name: amount' lines sorted by name.
    """

    def __init__(self, sales):
        ...

    @property
    def title(self):
        ...

    def body_lines(self):
        ...


class BriefSalesReport(SalesReport):
    """Same as SalesReport but with an empty footer (so it disappears)."""

    def footer(self):
        ...
