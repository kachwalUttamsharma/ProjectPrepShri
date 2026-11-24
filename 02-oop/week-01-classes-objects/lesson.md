# Week 1: Classes and objects

## 1. Why classes?
A class bundles **data** (attributes) and **behaviour** (methods) into one new type. Interviews (and real code) use classes to model things: accounts, stacks, parking spots.

```python
class Point:
    def __init__(self, x, y):   # runs when you call Point(1, 2)
        self.x = x              # instance attributes
        self.y = y

    def move(self, dx, dy):     # a method: first parameter is the object itself
        self.x += dx
        self.y += dy

p = Point(1, 2)    # p is an *instance* (object) of class Point
p.move(3, 0)
p.x                # 4
```

## 2. `self`
`p.move(3, 0)` is sugar for `Point.move(p, 3, 0)`. `self` is just the name (by convention) of the first parameter: the instance the method was called on. You must write it in every method signature and use `self.` to reach attributes.

## 3. `__init__`
The initializer. It sets up the starting state. It must return `None`. Validate inputs here (`raise ValueError`) so an object is never created in a broken state.

## 4. Instance vs class attributes
```python
class Dog:
    species = "dog"          # class attribute: shared by ALL instances
    count = 0

    def __init__(self, name):
        self.name = name     # instance attribute: one per object
        Dog.count += 1       # modify the class attribute via the class name
```
- Lookup order: instance first, then class. `d.species` finds the class one.
- `d.species = "wolf"` creates a new *instance* attribute that shadows the class one; it does not change other dogs.
- Inside methods, write `Dog.count += 1`, not `self.count += 1` (that would create an instance attribute).

## 5. Methods that return vs mutate
Decide per method: does it change `self` (mutate, return `None`) or compute something (return a value)? Be consistent; `list.sort()` mutates and returns `None`, `sorted()` returns a new list.

## 6. Objects are references
```python
a = Point(0, 0)
b = a            # same object, two names
b.x = 9
a.x              # 9
```
`==` on plain objects compares identity until you define `__eq__` (week 2). `is` tests identity.

## 7. Printing objects
`print(p)` gives `<__main__.Point object at 0x...>`. Define `__repr__` (week 2) to fix that. Use `vars(p)` or `p.__dict__` to peek at attributes.

## Common mistakes
- Forgetting `self` in the signature: `def move(dx, dy)` -> `TypeError: takes 2 positional arguments but 3 were given`.
- Forgetting `self.` inside: `x = x` sets a local, not an attribute.
- **Mutable default argument**: `def __init__(self, items=[])` shares ONE list across every instance. Use `items=None` then `self.items = [] if items is None else list(items)`.
- **Mutable class attribute**: `members = []` at class level is shared by all instances. Create lists in `__init__`.
- Writing `return` in `__init__`, or calling a method without parentheses (`acct.balance()` vs `acct.balance`).
- Using `self.count += 1` when you meant the shared class counter.

## Your task
Fill in `exercises.py`, then from the repo root (`/Users/uttam.sharma/Desktop/python`):
`.venv/bin/pytest 02-oop/week-01-classes-objects -v`
Then show me your code for review. Interview lens: be able to write `Stack`, `BankAccount` and a counter class from memory, and explain `self` and class-vs-instance attributes out loud.
