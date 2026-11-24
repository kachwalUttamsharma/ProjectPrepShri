import pytest

from exercises import *


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


# ---- doubly linked list
def keys_of(dll):
    return [n.key for n in dll.nodes()]


def test_dll_empty():
    d = DoublyLinkedList()
    assert len(d) == 0
    assert d.pop_back() is None
    assert d.head.next is d.tail and d.tail.prev is d.head


def test_dll_add_front_order():
    d = DoublyLinkedList()
    for k in "abc":
        d.add_front(Node(k, 1))
    assert keys_of(d) == ["c", "b", "a"]
    assert len(d) == 3


def test_dll_remove_middle_and_pointers():
    d = DoublyLinkedList()
    a, b, c = Node("a", 1), Node("b", 2), Node("c", 3)
    for n in (a, b, c):
        d.add_front(n)
    d.remove(b)
    assert keys_of(d) == ["c", "a"]
    assert b.prev is None and b.next is None
    assert c.next is a and a.prev is c
    assert len(d) == 2


def test_dll_move_to_front():
    d = DoublyLinkedList()
    a, b, c = Node("a", 1), Node("b", 2), Node("c", 3)
    for n in (a, b, c):
        d.add_front(n)
    d.move_to_front(a)
    assert keys_of(d) == ["a", "c", "b"]
    d.move_to_front(a)
    assert keys_of(d) == ["a", "c", "b"]
    assert len(d) == 3


def test_dll_pop_back():
    d = DoublyLinkedList()
    for k in "abc":
        d.add_front(Node(k, 1))
    assert d.pop_back().key == "a"
    assert d.pop_back().key == "b"
    assert d.pop_back().key == "c"
    assert d.pop_back() is None
    assert len(d) == 0


# ---- construction
@pytest.mark.parametrize("cap", [0, -1, 1.5, "3", None, True])
def test_bad_capacity(cap):
    with pytest.raises(ValueError):
        LRUCache(cap)


def test_bad_ttl():
    with pytest.raises(ValueError):
        LRUCache(2, ttl=0)
    with pytest.raises(ValueError):
        LRUCache(2, ttl=-5)


def test_capacity_attribute():
    assert LRUCache(4).capacity == 4


# ---- core behaviour
def test_get_missing_returns_default():
    c = LRUCache(2)
    assert c.get("x") is None
    assert c.get("x", 42) == 42


def test_put_get():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.get("a") == 1 and c.get("b") == 2
    assert len(c) == 2


def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    assert "a" not in c
    assert c.keys() == ["c", "b"]


def test_get_refreshes_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    assert "b" not in c and "a" in c and "c" in c


def test_update_existing_refreshes_and_does_not_evict():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 10)
    assert len(c) == 2
    assert c.keys() == ["a", "b"]
    assert c.get("a") == 10
    c.put("c", 3)
    assert "b" not in c


def test_falsy_values_are_stored():
    c = LRUCache(2)
    c.put("a", 0)
    c.put("b", None)
    assert c.get("a", "d") == 0
    assert c.get("b", "d") is None
    assert "b" in c


def test_capacity_one():
    c = LRUCache(1)
    c.put("a", 1)
    c.put("b", 2)
    assert c.keys() == ["b"]
    assert c.get("a") is None


def test_keys_order_mru_to_lru():
    c = LRUCache(3)
    for k in "abc":
        c.put(k, 1)
    c.get("a")
    assert c.keys() == ["a", "c", "b"]


def test_peek_and_contains_do_not_change_recency():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.peek("a") == 1
    assert "a" in c
    assert c.peek("zzz", "d") == "d"
    assert c.keys() == ["b", "a"]
    c.put("c", 3)
    assert "a" not in c


def test_delete():
    c = LRUCache(3)
    c.put("a", 1)
    c.put("b", 2)
    assert c.delete("a") is True
    assert c.delete("a") is False
    assert c.delete("never") is False
    assert len(c) == 1 and c.keys() == ["b"]
    c.put("x", 1)
    c.put("y", 1)
    assert len(c) == 3


def test_clear():
    c = LRUCache(3)
    c.put("a", 1)
    c.clear()
    assert len(c) == 0 and c.keys() == []
    c.put("b", 1)
    assert c.keys() == ["b"]


def test_unhashable_key_raises_typeerror():
    c = LRUCache(2)
    with pytest.raises(TypeError):
        c.put([1], 1)


# ---- eviction callback
def test_on_evict_called_for_capacity_eviction_only():
    seen = []
    c = LRUCache(2, on_evict=lambda k, v: seen.append((k, v)))
    c.put("a", 1)
    c.put("b", 2)
    c.put("a", 5)        # update: no eviction
    c.delete("b")        # delete: no callback
    c.put("c", 3)
    c.put("d", 4)        # evicts a
    assert seen == [("a", 5)]
    c.clear()
    assert seen == [("a", 5)]


# ---- ttl
def test_ttl_expires_on_get():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("a", 1)
    clock.advance(9.9)
    assert c.get("a") == 1
    clock.advance(0.1)  # now == expires_at -> expired
    assert c.get("a", "gone") == "gone"
    assert len(c) == 0


def test_get_does_not_extend_ttl():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("a", 1)
    clock.advance(6)
    assert c.get("a") == 1
    clock.advance(5)
    assert "a" not in c


def test_put_refreshes_ttl():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("a", 1)
    clock.advance(8)
    c.put("a", 2)
    clock.advance(8)
    assert c.get("a") == 2


def test_expired_entries_purged_before_evicting_live_ones():
    clock = FakeClock()
    c = LRUCache(2, ttl=10, clock=clock)
    c.put("old", 1)
    clock.advance(5)
    c.put("new", 2)
    clock.advance(6)       # "old" expired, "new" alive
    c.get("new")           # new is MRU anyway; make old LRU... put another
    c.put("x", 3)          # should purge old, not evict new
    assert c.keys() == ["x", "new"]


def test_expired_not_counted_in_len_keys_contains_delete():
    clock = FakeClock()
    seen = []
    c = LRUCache(3, ttl=5, clock=clock, on_evict=lambda k, v: seen.append(k))
    c.put("a", 1)
    c.put("b", 2)
    clock.advance(5)
    assert len(c) == 0
    assert c.keys() == []
    assert "a" not in c
    assert c.delete("b") is False
    assert seen == []


def test_no_ttl_never_expires():
    clock = FakeClock()
    c = LRUCache(2, clock=clock)
    c.put("a", 1)
    clock.advance(10 ** 9)
    assert c.get("a") == 1


# ---- stress / O(1) behaviour
def test_large_workload_matches_reference_model():
    cap = 50
    c = LRUCache(cap)
    model = []  # keys MRU first
    import random
    rnd = random.Random(7)
    for _ in range(3000):
        k = rnd.randrange(80)
        if rnd.random() < 0.5:
            c.put(k, k * 2)
            if k in model:
                model.remove(k)
            model.insert(0, k)
            del model[cap:]
        else:
            got = c.get(k)
            if k in model:
                model.remove(k)
                model.insert(0, k)
                assert got == k * 2
            else:
                assert got is None
    assert c.keys() == model


def test_operations_scale_linearly_not_quadratically():
    import time
    c = LRUCache(1000)
    start = time.perf_counter()
    for i in range(100_000):
        c.put(i % 1500, i)
        c.get((i * 7) % 1500)
    assert len(c) == 1000
    assert time.perf_counter() - start < 5  # generous: O(n) per op would take minutes
