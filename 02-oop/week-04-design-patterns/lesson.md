# Week 4: Composition, dataclasses, enums, protocols, SOLID and patterns

## 1. Composition over inheritance
**Is-a** -> inheritance (`Dog` is an `Animal`). **Has-a** -> composition (`Car` has an `Engine`).
```python
class Car:
    def __init__(self, engine):
        self.engine = engine          # injected collaborator
    def start(self):
        return self.engine.start()    # delegate
```
Composition is more flexible: swap the engine at runtime, test with a fake engine, no fragile base class. Rule of thumb: if you inherit only to reuse code, compose instead.

## 2. Dataclasses
Auto-generate `__init__`, `__repr__`, `__eq__` from annotated fields.
```python
from dataclasses import dataclass, field, replace

@dataclass
class Item:
    name: str
    price: float
    qty: int = 1
    tags: list[str] = field(default_factory=list)   # NEVER `= []`

    def __post_init__(self):                         # validation hook
        if self.price < 0:
            raise ValueError("price")
```
- `@dataclass(frozen=True)`: immutable and hashable (usable in sets/dict keys).
- `@dataclass(order=True)`: generates `<`, `>` comparing fields **in order**; use `field(compare=False)` to exclude some.
- `replace(obj, x=1)` makes a modified copy (handy for frozen ones).
- Fields with defaults must come after fields without.

## 3. Enums
```python
from enum import Enum, IntEnum

class Status(Enum):
    PENDING = "pending"
    DONE = "done"

Status("done")      # by value -> Status.DONE   (ValueError if unknown)
Status["DONE"]      # by name
Status.DONE.value   # 'done'
list(Status)        # iteration, in definition order
```
Use enums instead of magic strings. `IntEnum` members also compare as ints. Enums can have methods. Compare with `is`/`==`.

## 4. Protocols (structural typing)
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...
```
Any class with a matching `draw()` satisfies it: no inheritance needed (typed duck typing). Type checkers (mypy/pyright) enforce it; `isinstance` works only with `@runtime_checkable` and checks method *presence* only. Use an ABC when you want shared code or to force explicit subclassing; a Protocol when you only describe a shape.

## 5. SOLID (the interview version)
- **S**ingle Responsibility: a class has one reason to change (don't mix parsing, storage and emailing).
- **O**pen/Closed: extend by adding code (new strategy class, registry entry), not editing `if/elif` chains.
- **L**iskov Substitution: a subclass must work wherever the parent is expected (don't strengthen preconditions or break contracts; the classic `Square(Rectangle)` trap!).
- **I**nterface Segregation: small focused interfaces/protocols rather than one fat one.
- **D**ependency Inversion: depend on abstractions; pass collaborators in (`UserService(repo)`) instead of constructing them inside. Makes testing trivial.

## 6. Patterns you should know
- **Strategy**: interchangeable algorithms behind one interface (`PercentDiscount`, `FixedDiscount`). In Python a plain function/callable often suffices.
- **Factory**: one place that decides which class to build (`create_notifier("sms")`). A dict registry keeps it open for extension.
- **Observer**: publishers notify subscribers without knowing them (`emit("saved")`). Event systems, UI callbacks.
- **Singleton**: one shared instance. **Caveats**: it's hidden global state, hard to test (state leaks between tests), problematic with threads, and often unnecessary: a module-level object does the job in Python. Prefer dependency injection; know the pattern for interviews, and be able to argue against it.

## 7. Exceptions as classes
```python
class BankError(Exception): ...                       # base for your domain
class InsufficientFundsError(BankError):
    def __init__(self, balance, requested):
        super().__init__(f"balance {balance}, requested {requested}")
        self.balance, self.requested = balance, requested
```
- Build a small hierarchy so callers can catch `BankError` broadly or the subclass narrowly.
- Carry data as attributes, not only in the message.
- Chain causes: `raise ValidationError("bad age") from err` (sets `__cause__`).
- Catch specific exceptions; never bare `except:`.

## Common mistakes
- `field` default `[]` in a dataclass (it raises ValueError for lists, good) or in a plain `__init__`.
- Inheriting just to reuse a few methods.
- Putting `if kind == ...` chains in many places instead of one factory/strategy.
- Singleton that you can never reset in tests.
- Mutating an `Enum` or comparing `Status.DONE == "done"` (False).
- Catching `Exception` and swallowing it.

## Your task
Fill in `exercises.py`, then run
`.venv/bin/pytest 02-oop/week-04-design-patterns -v`
and show me your code. This is the heaviest week: it's fine to split it across two sessions (exercises 1-5, then 6-10). Interview lens: say what SOLID letters mean with a one-line example each, and describe Strategy/Observer/Factory in 30 seconds.
