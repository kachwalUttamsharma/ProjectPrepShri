# Week 2 (Python depth): Data model and memory

Goal: explain what Python does with objects, names, equality, hashing and memory, and use the standard-library data structures idiomatically. Budget ~8 hours: lesson + experiments (3h), exercises (4h), interview-qa (1h).

## 1. Names, objects, references
A variable is a **name bound to an object**; assignment never copies.
```python
a = [1, 2]; b = a; b.append(3)   # a is [1, 2, 3]: same object
a is b          # identity (same object)
a == b          # equality (same value, via __eq__)
id(a)           # identity number (CPython: memory address)
```
Use `is` only for singletons (`None`, `True`, `False`). Small ints and some strings are interned by CPython; never rely on `x is 256`.

Arguments are passed "by assignment" (call by object reference): mutating a parameter affects the caller's object; rebinding it does not.

Mutable: list, dict, set, bytearray, most classes. Immutable: int, float, str, tuple, frozenset, bytes. A tuple holding a list is immutable in shape but its list can change.

## 2. Copying
```python
import copy
b = a[:]  /  list(a)  /  a.copy()   # shallow: new outer, shared inner
c = copy.deepcopy(a)                 # recursive; handles cycles via memo
```
`[[0]*3]*3` makes three references to ONE row: use `[[0]*3 for _ in range(3)]`. Customise with `__copy__`/`__deepcopy__`.

## 3. Hashing and equality
Dict keys and set members must be hashable: `hash(x)` stable for life, and **equal objects must have equal hashes**. Defining `__eq__` without `__hash__` sets `__hash__ = None` (unhashable). Mutable builtins (list, dict, set) are unhashable. Hash tables give O(1) average lookup; worst case O(n) with collisions.

Comparison: return `NotImplemented` (not False) from `__eq__`/`__lt__` for foreign types so Python tries the reflected operation. `functools.total_ordering` fills in the rest from `__eq__` plus one ordering.

## 4. Dict internals and ordering
Since 3.7 dicts preserve insertion order (guaranteed). CPython uses a compact layout: a sparse index table plus a dense entries array. Resizing happens when ~2/3 full, so insertion is amortised O(1). Mutating a dict while iterating raises `RuntimeError`. Updating an existing key keeps its original position; deleting and re-adding moves it to the end. `d | other` merges (3.9+).

## 5. Sorting
`sorted()` / `list.sort()` use Timsort: O(n log n), O(n) on nearly sorted data, and **stable** (equal keys keep input order). Use stability for multi-key sorts: sort by the least significant key first. `key=` is computed once per element. `reverse=True` preserves stability. `sorted` returns a new list; `.sort()` returns `None`.

## 6. `__slots__` and descriptors
`__slots__ = ("x", "y")` replaces the per-instance `__dict__` with fixed slots: less memory, faster attribute access, no dynamic attributes. Gotchas: inheritance needs slots on each class to keep the benefit; no weak references unless `"__weakref__"` is listed.

A **descriptor** is an object with `__get__`, `__set__` and/or `__delete__` stored on a class. It powers `property`, methods (functions are non-data descriptors), `classmethod`, `staticmethod`, and `__slots__`. Data descriptors (define `__set__`) take priority over instance `__dict__`; non-data ones do not. `__set_name__(self, owner, name)` tells the descriptor its attribute name. Rule of thumb: attribute lookup = data descriptor on type, then instance dict, then non-data descriptor/class attribute.

## 7. Memory management
CPython frees most objects by **reference counting**: when the count hits zero, the object is freed immediately (deterministic, which is why `with` and `__del__` mostly behave predictably). Refcounting can't free **cycles** (a <-> b), so a generational cyclic **garbage collector** (`gc`) finds unreachable cycles. `weakref` references don't increase the count (caches, observers). `sys.getrefcount(x)` is always one higher than expected (the call's own argument). Other implementations (PyPy) don't use refcounting, so don't depend on timing. In free-threaded builds (3.13+ optional) refcounting is adapted, but the semantics you rely on stay the same.

## 8. collections
| Tool | Use |
|---|---|
| `Counter` | multiset counts, `.most_common(n)`, arithmetic between counters |
| `defaultdict(factory)` | auto-create missing values (`list`, `int`, `set`) |
| `deque(maxlen=)` | O(1) both ends, ring buffer, BFS queues (list.pop(0) is O(n)) |
| `OrderedDict` | `move_to_end`, `popitem(last=False)` (LRU caches); order-sensitive equality |
| `namedtuple` | lightweight immutable record, tuple-compatible |
| `ChainMap` | layered lookups (config overrides) |
Note `defaultdict` creates keys on read: `d[k]` inserts; `k in d` doesn't.

## 9. dataclasses
```python
@dataclass(frozen=True, order=True, slots=True)
class P:
    x: int
    y: int = 0
    tags: list = field(default_factory=list)   # never a bare mutable default
```
Generates `__init__`, `__repr__`, `__eq__` (and `__hash__` when frozen+eq, `__lt__` etc. with `order=True`). `field(compare=False)`, `__post_init__` for validation, `kw_only=True`, `dataclasses.replace`, `asdict`. Compare with `namedtuple` (tuple semantics), `TypedDict` (typing only, runtime is a dict), and Pydantic (runtime validation, what FastAPI uses).

## 10. typing essentials
Hints are not enforced at runtime; a checker (mypy/pyright) uses them.
```python
def first(xs: list[T]) -> T | None: ...         # Optional[T] == T | None
class Stack[T]: ...                              # 3.12+ syntax; or Generic[T] with TypeVar
class Closeable(Protocol):                       # structural typing ("duck typing" for checkers)
    def close(self) -> None: ...
class User(TypedDict): id: int; name: str        # dict with known keys
```
**Narrowing**: `isinstance`, `is None`, truthiness, `match` narrow a union inside a branch. `Literal`, `Final`, `Callable[[int], str]`, `Any` (opt-out), `TypeGuard`. Python 3.14 evaluates annotations lazily (PEP 649), so forward references mostly just work.

## 11. enum
```python
class Color(Enum): RED = 1
Color(1), Color["RED"], Color.RED.name/.value
IntEnum   # compares equal to ints; StrEnum for strings; Flag for bitmasks; auto()
```
Members are singletons: compare with `is`. Iteration order = definition order. Lookup by an unknown value raises `ValueError`, by name `KeyError`.

## Common mistakes
- Mutable default arguments / `[[]] * n` aliasing.
- Defining `__eq__` and forgetting hash consistency; mutating an object after using it as a dict key.
- Using `is` for value comparison; `is` vs `==` with strings/ints.
- Expecting `copy.copy` to isolate nested data.
- Sorting with `cmp`-style thinking: use `key=` (or `functools.cmp_to_key`).
- Asserting on `__del__` timing or `sys.getrefcount` values in tests.

## Your task
Fill in `exercises.py`, run `../../.venv/bin/pytest -q`, then answer `interview-qa.md` aloud without peeking.
