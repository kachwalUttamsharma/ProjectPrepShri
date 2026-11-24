import inspect
from itertools import islice

import pytest
from exercises import *


def test_squares_of_evens():
    assert squares_of_evens([1, 2, 3, 4]) == [4, 16]
    assert squares_of_evens([]) == []
    assert squares_of_evens([1, 3]) == []
    assert squares_of_evens([-2, 0]) == [4, 0]


def test_word_lengths():
    assert word_lengths(["a", "bbb"]) == {"a": 1, "bbb": 3}
    assert word_lengths([]) == {}


def test_flatten():
    assert flatten([[1, 2], [3], []]) == [1, 2, 3]
    assert flatten([]) == []
    assert flatten([["a"], ["b", "c"]]) == ["a", "b", "c"]


def test_sort_by_length():
    assert sort_by_length(["pear", "fig", "apple", "kiwi"]) == ["fig", "kiwi", "pear", "apple"]
    assert sort_by_length([]) == []
    words = ["bb", "a"]
    sort_by_length(words)
    assert words == ["bb", "a"]  # input untouched


def test_sort_by_score_desc():
    assert sort_by_score_desc([("a", 1), ("b", 3), ("c", 3)]) == [("b", 3), ("c", 3), ("a", 1)]
    assert sort_by_score_desc([]) == []
    assert sort_by_score_desc([("x", 5)]) == [("x", 5)]


def test_index_of_max():
    assert index_of_max([1, 5, 3]) == 1
    assert index_of_max([5, 5, 1]) == 0
    assert index_of_max([-3, -1, -2]) == 1
    assert index_of_max([]) is None


def test_pairwise_sum():
    assert pairwise_sum([1, 2, 3], [10, 20]) == [11, 22]
    assert pairwise_sum([], [1]) == []
    assert pairwise_sum([1, 1], [2, 2]) == [3, 3]


def test_numbered():
    assert numbered(["a", "b"]) == ["1. a", "2. b"]
    assert numbered([]) == []


def test_evens_up_to():
    assert inspect.isgenerator(evens_up_to(5))
    assert list(evens_up_to(7)) == [0, 2, 4, 6]
    assert list(evens_up_to(8)) == [0, 2, 4, 6, 8]
    assert list(evens_up_to(0)) == [0]
    assert list(evens_up_to(-1)) == []


def test_fib_generator():
    assert inspect.isgenerator(fib_generator())
    assert list(islice(fib_generator(), 10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    g = fib_generator()
    assert next(g) == 0
    assert next(g) == 1
    assert next(g) == 1


def test_chunks():
    assert inspect.isgenerator(chunks([1], 1))
    assert list(chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert list(chunks([1, 2, 3, 4], 2)) == [[1, 2], [3, 4]]
    assert list(chunks([], 3)) == []
    assert list(chunks("abcde", 3)) == ["abc", "de"]
    with pytest.raises(ValueError):
        list(chunks([1, 2], 0))


def test_running_total():
    assert inspect.isgenerator(running_total([1]))
    assert list(running_total([1, 2, 3, 4])) == [1, 3, 6, 10]
    assert list(running_total([])) == []
    assert list(running_total([5, -5, 5])) == [5, 0, 5]
    # lazy: works on an endless input
    def naturals():
        n = 1
        while True:
            yield n
            n += 1
    assert list(islice(running_total(naturals()), 4)) == [1, 3, 6, 10]


def test_top_n_words():
    assert top_n_words("b a b c a b", 2) == ["b", "a"]
    assert top_n_words("B b A", 1) == ["b"]
    assert top_n_words("x y z", 2) == ["x", "y"]  # tie -> alphabetical
    assert top_n_words("", 3) == []
    assert top_n_words("a a b", 10) == ["a", "b"]
