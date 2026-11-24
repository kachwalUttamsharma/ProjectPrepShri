import itertools

import pytest

from exercises import *


def test_make_counter():
    c = make_counter()
    assert [c(), c(), c()] == [1, 2, 3]
    d = make_counter(10)
    assert d() == 11
    assert c() == 4


def test_make_multipliers():
    fs = make_multipliers(4)
    assert len(fs) == 4
    assert [f(10) for f in fs] == [0, 10, 20, 30]


def test_append_item():
    assert append_item(1) == [1]
    assert append_item(2) == [2]
    mine = [9]
    assert append_item(1, mine) is mine
    assert mine == [9, 1]


def test_count_calls():
    @count_calls
    def add(a, b):
        """adds"""
        return a + b

    assert add.calls == 0
    assert add(1, 2) == 3
    assert add(a=2, b=2) == 4
    assert add.calls == 2
    assert add.__name__ == "add"
    assert add.__doc__ == "adds"


def test_retry_succeeds_after_failures():
    state = {"n": 0}

    @retry(3, exceptions=(ValueError,))
    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise ValueError("no")
        return "ok"

    assert flaky() == "ok"
    assert state["n"] == 3
    assert flaky.__name__ == "flaky"


def test_retry_gives_up_and_reraises_last():
    state = {"n": 0}

    @retry(2)
    def bad():
        state["n"] += 1
        raise RuntimeError(f"fail {state['n']}")

    with pytest.raises(RuntimeError, match="fail 2"):
        bad()
    assert state["n"] == 2


def test_retry_other_exception_propagates_immediately():
    state = {"n": 0}

    @retry(5, exceptions=(ValueError,))
    def f():
        state["n"] += 1
        raise KeyError("x")

    with pytest.raises(KeyError):
        f()
    assert state["n"] == 1


def test_retry_passes_args():
    @retry(2)
    def mul(a, b=1):
        return a * b

    assert mul(3, b=4) == 12


def test_singleton():
    @singleton
    class Config:
        def __init__(self, name="default"):
            self.name = name

    a = Config("first")
    b = Config("second")
    assert a is b
    assert a.name == "first"


def test_singleton_independent_classes():
    @singleton
    class A:
        pass

    @singleton
    class B:
        pass

    assert A() is A()
    assert A() is not B()


def test_temp_attr_restores():
    class Obj:
        x = 1

    o = Obj()
    with temp_attr(o, "x", 99):
        assert o.x == 99
    assert o.x == 1


def test_temp_attr_deletes_new_attribute_and_restores_on_error():
    class Obj:
        pass

    o = Obj()
    with pytest.raises(ZeroDivisionError):
        with temp_attr(o, "y", 5):
            assert o.y == 5
            1 / 0
    assert not hasattr(o, "y")


def test_countdown():
    assert list(Countdown(3)) == [3, 2, 1]
    assert list(Countdown(0)) == []


def test_countdown_is_one_shot_iterator():
    c = Countdown(2)
    assert iter(c) is c
    assert next(c) == 2
    assert list(c) == [1]
    assert list(c) == []
    with pytest.raises(StopIteration):
        next(c)


def test_chunked():
    assert list(chunked(range(5), 2)) == [[0, 1], [2, 3], [4]]
    assert list(chunked([], 3)) == []
    assert list(chunked("abcd", 2)) == [["a", "b"], ["c", "d"]]


def test_chunked_lazy_on_infinite():
    gen = chunked(itertools.count(), 3)
    assert next(gen) == [0, 1, 2]
    assert next(gen) == [3, 4, 5]


def test_chunked_invalid_n():
    with pytest.raises(ValueError):
        list(chunked([1, 2], 0))


def test_fib_cached():
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(10) == 55
    assert fib(90) == 2880067194370816120
    assert fib.cache_info().hits > 0


def test_compose():
    inc = lambda x: x + 1
    dbl = lambda x: x * 2
    assert compose(inc, dbl)(5) == 11   # inc(dbl(5))
    assert compose(dbl, inc)(5) == 12   # dbl(inc(5))
    assert compose()(7) == 7
    assert compose(str, inc, dbl)(1) == "3"


def test_run_length_encode():
    assert run_length_encode("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]
    assert run_length_encode("") == []
    assert run_length_encode("abab") == [("a", 1), ("b", 1), ("a", 1), ("b", 1)]
