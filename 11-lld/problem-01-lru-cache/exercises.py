"""LLD 01: LRU cache. Read lesson.md for the full spec.

Implement everything marked `...`. Do NOT use OrderedDict or functools.lru_cache:
the point is to build the hash map + doubly linked list yourself.
"""
import time


class Node:
    """A list node. Attributes: key, value, expires_at (None = never), prev, next.

    Node(key=None, value=None). Sentinel nodes use the defaults.
    """

    def __init__(self, key=None, value=None):
        ...


class DoublyLinkedList:
    """Doubly linked list with sentinel `head` and `tail` Node attributes.

    Front = most recently used. Every operation below is O(1) except nodes().
    - __len__: number of real nodes (sentinels excluded).
    - add_front(node): insert right after head.
    - remove(node): unlink node (it must be in the list); set its prev/next to None.
    - move_to_front(node): remove then add_front.
    - pop_back() -> Node | None: unlink and return the node before tail; None if empty.
    - nodes() -> list[Node]: real nodes from front to back (O(n), for tests/debug).
    """

    def __init__(self):
        ...

    def __len__(self):
        ...

    def add_front(self, node):
        ...

    def remove(self, node):
        ...

    def move_to_front(self, node):
        ...

    def pop_back(self):
        ...

    def nodes(self):
        ...


class LRUCache:
    """LRUCache(capacity, ttl=None, clock=None, on_evict=None).

    - capacity: int > 0 (bool and non-int also rejected) else ValueError.
    - ttl: seconds an entry lives after its last put(); None = no expiry; ttl <= 0 -> ValueError.
      An entry is expired when clock() >= expires_at. get() does NOT extend the ttl.
    - clock: zero-arg callable returning seconds (default time.monotonic).
    - on_evict(key, value): called ONLY when an entry is dropped to make room
      (capacity eviction). Not called for delete(), clear() or expiry.

    Attribute: capacity.

    Methods:
    - get(key, default=None): value and mark most-recently-used. Missing or expired
      -> default (an expired entry is removed).
    - peek(key, default=None): like get but does NOT change recency.
    - put(key, value): insert or update (update refreshes recency and ttl). Before
      inserting a NEW key into a full cache, purge expired entries first; if still
      full evict the least recently used one (call on_evict).
    - delete(key) -> bool: True if a live entry was removed; False if missing/expired.
    - clear(): remove everything (no callbacks).
    - keys() -> list: live keys ordered most- to least-recently used.
    - __len__: number of live entries. __contains__(key): live and present; does NOT
      change recency.
    get/put/delete/peek/__contains__ must be O(1) (len/keys may purge expired in O(n)).
    """

    def __init__(self, capacity, ttl=None, clock=None, on_evict=None):
        ...

    def get(self, key, default=None):
        ...

    def peek(self, key, default=None):
        ...

    def put(self, key, value):
        ...

    def delete(self, key):
        ...

    def clear(self):
        ...

    def keys(self):
        ...

    def __len__(self):
        ...

    def __contains__(self, key):
        ...
