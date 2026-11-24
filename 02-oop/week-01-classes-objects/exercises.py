"""Week 1 exercises: classes and objects. Replace each `...` with your code.

Every exercise is a class: fill in the method bodies. Keep the signatures.
"""


class Point:
    """A point in 2D.

    Point(x, y) stores x and y as attributes (defaults 0, 0).
    distance_to(other) -> float Euclidean distance. Hint: math.hypot
    translate(dx, dy) -> moves THIS point (mutates, returns None).
    """

    def __init__(self, x=0, y=0):
        ...

    def distance_to(self, other):
        ...

    def translate(self, dx, dy):
        ...


class Counter:
    """Counts things.

    - starts at `start` (default 0), stored in attribute `value`
    - increment(by=1) / decrement(by=1) change value and return nothing
    - reset() sets value back to the ORIGINAL start value
    """

    def __init__(self, start=0):
        ...

    def increment(self, by=1):
        ...

    def decrement(self, by=1):
        ...

    def reset(self):
        ...


class BankAccount:
    """A simple bank account.

    - BankAccount(owner, balance=0): ValueError if balance < 0
    - deposit(amount): amount must be > 0 else ValueError. Returns new balance.
    - withdraw(amount): amount must be > 0 else ValueError;
      if amount > balance raise ValueError("insufficient funds"). Returns new balance.
    - transfer_to(other, amount): withdraw from self, deposit into other.
      If the withdraw fails, `other` must be unchanged.
    """

    def __init__(self, owner, balance=0):
        ...

    def deposit(self, amount):
        ...

    def withdraw(self, amount):
        ...

    def transfer_to(self, other, amount):
        ...


class Rectangle:
    """Rectangle(width, height). Both must be > 0 else ValueError.

    area(), perimeter() -> numbers; is_square() -> bool.
    scale(factor): multiplies width and height IN PLACE (mutates, returns None).
    """

    def __init__(self, width, height):
        ...

    def area(self):
        ...

    def perimeter(self):
        ...

    def is_square(self):
        ...

    def scale(self, factor):
        ...


class Student:
    """Student(name). Keeps a list of grades in attribute `grades` (starts empty).

    add_grade(g): g must be 0..100 inclusive else ValueError.
    average() -> float; 0.0 if there are no grades.
    highest() -> the max grade, or None if no grades.
    Each student must have their OWN grades list (beware shared mutable state).
    """

    def __init__(self, name):
        ...

    def add_grade(self, grade):
        ...

    def average(self):
        ...

    def highest(self):
        ...


class Dog:
    """Class attributes vs instance attributes.

    - class attribute `species = "Canis familiaris"`
    - class attribute `count`: how many Dog objects have been created so far
      (starts at 0; increment in __init__ via `Dog.count`)
    - Dog(name, tricks=None): instance attrs `name` and `tricks` (a new list;
      copy the argument if given). Do NOT use `tricks=[]` as the default!
    - add_trick(trick): append only if not already known.
    """

    species = "Canis familiaris"
    count = 0

    def __init__(self, name, tricks=None):
        ...

    def add_trick(self, trick):
        ...


class Stack:
    """LIFO stack backed by a list stored in a private-by-convention `_items`.

    push(x), pop() -> x, peek() -> top without removing,
    is_empty() -> bool, size() -> int.
    pop() and peek() on an empty stack raise IndexError("stack is empty").
    """

    def __init__(self):
        ...

    def push(self, item):
        ...

    def pop(self):
        ...

    def peek(self):
        ...

    def is_empty(self):
        ...

    def size(self):
        ...


class ShoppingCart:
    """ShoppingCart() starts empty.

    add(name, price, qty=1): add qty of an item. If the name is already in the
      cart, increase its quantity (the original price stays). price >= 0, qty >= 1
      else ValueError.
    remove(name): remove the item entirely; KeyError if missing.
    total() -> sum of price * qty.
    item_count() -> total quantity of all items.
    Hint: dict of name -> [price, qty] (or a small dict per item).
    """

    def __init__(self):
        ...

    def add(self, name, price, qty=1):
        ...

    def remove(self, name):
        ...

    def total(self):
        ...

    def item_count(self):
        ...


class Team:
    """Team(name). Attribute `members` is a list, unique per team.

    add(member): append if not present; returns True if added, False if already there.
    __len__ is NOT needed yet; use size() -> int.
    Class attribute `all_teams` is a list of every Team ever created (shared on
    purpose; append `self` in __init__).
    """

    all_teams = []

    def __init__(self, name):
        ...

    def add(self, member):
        ...

    def size(self):
        ...


def make_points(pairs):
    """Given [(1, 2), (3, 4)] return a list of Point objects.

    Hint: a list comprehension and `Point(*pair)`.
    """
    ...


def farthest_from_origin(points):
    """Return the Point farthest from (0, 0), or None for an empty list.

    Hint: Point().distance_to(p), and max(..., key=...).
    """
    ...
