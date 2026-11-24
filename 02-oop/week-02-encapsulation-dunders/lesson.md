# Week 2: Encapsulation, properties and dunder methods

## 1. Encapsulation by convention
Python has no `private` keyword. Conventions:
- `name`: public.
- `_name`: "internal, please don't touch" (a promise, not enforced).
- `__name`: **name mangling**: stored as `_ClassName__name` to avoid clashes in subclasses. It is not security.

## 2. `@property`
Expose an attribute with validation while keeping `obj.attr` syntax:
```python
class Temperature:
    def __init__(self, celsius):
        self.celsius = celsius          # goes through the setter below

    @property
    def celsius(self):                  # getter
        return self._celsius

    @celsius.setter
    def celsius(self, value):           # setter
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self):               # read-only (no setter) -> computed
        return self._celsius * 9 / 5 + 32
```
Assigning to a property with no setter raises `AttributeError`. Start with plain attributes; switch to a property only when you need validation or a computed value (the call sites don't change).

## 3. Dunder (special) methods
Python calls these for you. Never call `obj.__len__()` directly; use `len(obj)`.

| Method | Triggered by |
|---|---|
| `__repr__` | `repr(x)`, REPL, debugging. Aim for `Vector(1, 2)` (unambiguous, ideally eval-able) |
| `__str__` | `str(x)`, `print(x)`; falls back to `__repr__` |
| `__eq__(self, other)` | `a == b` |
| `__lt__` | `a < b` (enables `sorted`, `min`, `max`) |
| `__hash__` | `hash(x)`, set members, dict keys |
| `__len__` | `len(x)`, also truthiness if no `__bool__` |
| `__getitem__` | `x[i]`, `x[1:3]` |
| `__iter__` | `for a in x`, `list(x)` |
| `__contains__` | `a in x` |
| `__add__`, `__mul__` | `a + b`, `a * 3` |

Rules of thumb:
- Return `NotImplemented` (not `False`) from `__eq__`/`__add__` when `other` is the wrong type; Python then tries the other side.
- **If you define `__eq__`, Python sets `__hash__ = None`** (unhashable). Define both, from the same fields, and only for immutable-ish state: `hash((self.x, self.y))`. Equal objects MUST have equal hashes.
- `functools.total_ordering`: define `__eq__` and `__lt__`, get `<=`, `>`, `>=` free.
- `__iter__` should return a **fresh iterator** each call (a generator function with `yield` does that), so you can loop twice.

## 4. `@staticmethod` and `@classmethod`
```python
class Person:
    def __init__(self, name, age): ...

    @staticmethod
    def is_adult(age):            # no self/cls: just a function living in the class
        return age >= 18

    @classmethod
    def from_string(cls, s):      # cls is the class (works with subclasses)
        name, age = s.split(",")
        return cls(name, int(age))   # alternative constructor
```
Use `@classmethod` for alternative constructors (`dict.fromkeys`, `datetime.fromisoformat`). Use `@staticmethod` rarely; a module-level function is often cleaner.

## Common mistakes
- Setter that assigns `self.celsius = v` (infinite recursion). Store in `self._celsius`.
- Defining `__eq__` without `__hash__` and then putting objects in a set.
- `__eq__` that crashes on other types (`other.x` on an int). Check `isinstance` first.
- `__repr__` that returns something that isn't a `str` (e.g. forgetting `f`).
- Mutating an object that is used as a dict key or set member.
- `__str__` printing in the method instead of **returning** a string.

## Your task
Fill in `exercises.py`, then run
`.venv/bin/pytest 02-oop/week-02-encapsulation-dunders -v`
and show me your code. Interview lens: explain `__eq__`/`__hash__` contract, property vs plain attribute, `@classmethod` vs `@staticmethod`.
