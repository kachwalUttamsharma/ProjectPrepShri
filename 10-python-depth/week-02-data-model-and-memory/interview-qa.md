# Week 2 interview Q&A: data model and memory

**1. Is Python pass-by-value or pass-by-reference?**
Neither exactly: pass by object reference (assignment). The parameter is a new name bound to the same object. Mutating it is visible to the caller; rebinding it is not.

**2. `is` vs `==`?**
`is` compares identity (same object); `==` calls `__eq__` (same value). Use `is` for `None`/singletons. CPython caches small ints and interns some strings, so `is` on those is an implementation detail.

**3. Shallow vs deep copy?**
Shallow copy creates a new container holding references to the same children; deep copy recursively copies children (with a memo to handle cycles and shared references). `list(x)`, `x[:]`, `x.copy()`, `copy.copy` are shallow.

**4. Why does `[[0]*3]*3` misbehave?**
The outer `*` repeats the same inner list reference three times; changing one row changes all. Use a comprehension.

**5. What makes an object hashable? What is the contract?**
It has `__hash__` and the hash never changes during its life; if `a == b` then `hash(a) == hash(b)`. Defining `__eq__` alone sets `__hash__` to None. Lists, dicts, sets are unhashable; tuples are hashable only if all elements are.

**6. How does a dict work, and what is lookup complexity?**
Open-addressing hash table with a compact index table plus a dense, insertion-ordered entries array. Average O(1) get/set/delete, worst O(n) with pathological collisions. Resizes at ~2/3 load, so inserts are amortised O(1).

**7. Is dict ordering guaranteed?**
Yes since 3.7 (language guarantee): insertion order. Re-assigning an existing key keeps its position. Equality between plain dicts ignores order; `OrderedDict` equality respects it.

**8. Why can't you modify a dict while iterating it?**
Resizing/inserting invalidates the iteration; Python raises `RuntimeError: dictionary changed size during iteration`. Iterate over `list(d)` or build a new dict.

**9. Is `sorted` stable? Why does it matter?**
Yes (Timsort). Equal-key elements keep original order, so you can do multi-key sorts by sorting repeatedly from least to most significant key. Complexity O(n log n), O(n) best case.

**10. What does `__slots__` do and what are the trade-offs?**
Declares fixed attributes stored in slots rather than a per-instance `__dict__`: less memory, slightly faster access, no arbitrary new attributes. Costs: no dynamic attrs, no weakrefs unless `__weakref__` listed, subclasses need own `__slots__`, multiple inheritance with slots is awkward.

**11. What is a descriptor? Where do you already use them?**
An object with `__get__`/`__set__`/`__delete__` defined on a class. `property`, functions-as-methods (binding), `classmethod`, `staticmethod`, `__slots__` members are all descriptors. Data descriptors beat the instance dict in attribute lookup.

**12. Explain CPython memory management.**
Reference counting frees an object the instant its count reaches zero. A generational cyclic GC (`gc` module) finds unreachable reference cycles that refcounting can't. Small objects come from the pymalloc arena allocator. `weakref` avoids keeping objects alive.

**13. Does Python's GC make `__del__` reliable?**
No. `__del__` timing isn't guaranteed (cycles, other interpreters, exit). Use context managers or `weakref.finalize` for cleanup.

**14. `defaultdict` vs `dict.setdefault` vs `Counter`?**
`defaultdict(factory)` creates missing values on `d[k]` (also inserts on read). `setdefault(k, v)` evaluates `v` every call. `Counter` is a dict subclass for counting hashables with `most_common`; missing keys return 0 without inserting.

**15. When use `deque` over `list`?**
When you add/remove at both ends: `appendleft/popleft` are O(1), while `list.pop(0)`/`insert(0, x)` are O(n). `maxlen` gives a ring buffer. Downside: indexing in the middle is O(n).

**16. `namedtuple` vs `dataclass` vs `TypedDict` vs Pydantic model?**
namedtuple: immutable, tuple-like, unpackable, small. dataclass: regular class with generated methods, mutable by default, optional frozen/slots/order. TypedDict: type-checker-only shape of a dict. Pydantic: runtime validation/coercion/serialisation (FastAPI).

**17. Why is `field(default_factory=list)` required in dataclasses?**
A shared mutable default would be one object for every instance; dataclasses raise `ValueError` for list/dict/set defaults to prevent it. The factory runs per instance.

**18. Protocol vs ABC?**
ABC: nominal typing, explicit inheritance (or registration), can provide shared code and runtime enforcement. Protocol: structural typing; any class with matching methods satisfies it, no inheritance (add `@runtime_checkable` for isinstance, which checks only method presence).

**19. What is type narrowing, and what does `Optional[int]` mean?**
After `if x is None: return`, a checker knows `x` is `int`. `isinstance`, truthiness, `match`, and `TypeGuard` narrow unions. `Optional[int]` is `int | None`; it does NOT mean the argument is optional (that's a default).

**20. Enum: `Enum` vs `IntEnum` vs `StrEnum`, and how to compare?**
`Enum` members aren't equal to raw values; `IntEnum`/`StrEnum` are, which eases JSON/DB interop but weakens type safety. Members are singletons so use `is`. Look up by value `Color(1)` (ValueError) or name `Color["RED"]` (KeyError). `auto()` assigns values.
