# Week 3: Inheritance, polymorphism, ABCs and the MRO

## 1. Inheritance and `super()`
A subclass gets everything from its parent and can add or override.
```python
class Employee:
    def __init__(self, name, salary):
        self.name, self.salary = name, salary
    def annual_pay(self):
        return self.salary

class Manager(Employee):                 # Manager "is an" Employee
    def __init__(self, name, salary, reports=None):
        super().__init__(name, salary)   # let the parent set up its part
        self.reports = list(reports or [])
    def annual_pay(self):                # override
        return super().annual_pay() + 1000 * len(self.reports)
```
Use `super()` (no arguments) to call the parent version. Forgetting `super().__init__()` leaves parent attributes unset.

`isinstance(m, Employee)` is True for a Manager. `issubclass(Manager, Employee)` is True. `bool` is a subclass of `int`, so check `bool` **first** when classifying.

## 2. Polymorphism
Same call, different behaviour depending on the object's class:
```python
for e in [Employee(...), Manager(...)]:
    print(e.annual_pay())     # each class answers in its own way
```
Callers depend on the *interface*, not the concrete class. This is what lets you add a new shape without touching `total_area()`.

## 3. Abstract base classes
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self): ...

Shape()          # TypeError: can't instantiate abstract class
```
A subclass must implement every abstract method before it can be instantiated. Concrete methods in the ABC (e.g. `describe()`) can call the abstract ones: this is the **template method** pattern.

## 4. Method Resolution Order (MRO)
With multiple inheritance Python linearizes parents using C3. See it with `Cls.__mro__` or `Cls.mro()`.
```python
class A: ...
class B(A): ...
class C(A): ...
class D(B, C): ...
D.__mro__   # D, B, C, A, object   (children before parents, left-to-right)
```
`super()` means "the next class in the MRO of `type(self)`", not "my parent". If every class calls `super().method()`, each runs exactly once (cooperative inheritance). **Mixins** are small classes adding one behaviour (`JsonMixin.to_json()`) placed to the left of the main base: `class User(JsonMixin, Base)`.

## 5. Duck typing
"If it quacks like a duck..." Python doesn't check the type, only that the method exists. Prefer EAFP/duck typing over many `isinstance` checks:
```python
def quack_all(things):
    return [t.quack() for t in things if hasattr(t, "quack")]
```
Formal alternative (week 4): `typing.Protocol`.

## 6. Subclassing built-ins
You can subclass `list`, `dict`, `Exception`. Gotcha: built-in methods often do NOT call each other (`list.extend` does not call your overridden `append`). Override every entry point you care about.

## 7. Inheritance is the strong coupling
Use it for true "is-a" relationships with shared behaviour. If you only want to reuse code, prefer composition (week 4).

## Common mistakes
- Not calling `super().__init__(...)`.
- Overriding with a different signature, breaking callers (Liskov Substitution Principle).
- Raising `NotImplemented` instead of `NotImplementedError` in a "must override" method.
- Deep hierarchies (3+ levels) for code reuse only.
- Checking `type(x) == Foo` instead of `isinstance(x, Foo)`.
- Assuming `super()` is the direct parent in multiple inheritance.

## Your task
Fill in `exercises.py`, then run
`.venv/bin/pytest 02-oop/week-03-inheritance-polymorphism -v`
and show me your code. Interview lens: explain MRO, abstract classes vs duck typing, when NOT to inherit.
