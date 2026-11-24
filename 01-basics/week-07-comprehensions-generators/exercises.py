"""Week 7 exercises. Replace each `...` with your code."""


def squares_of_evens(nums):
    """Return a list of the squares of the even numbers, in order.
    [1, 2, 3, 4] -> [4, 16]. Hint: list comprehension with an `if`."""
    ...


def word_lengths(words):
    """Return a dict mapping each word to its length. ['a', 'bbb'] -> {'a': 1, 'bbb': 3}.
    Hint: dict comprehension."""
    ...


def flatten(list_of_lists):
    """Flatten one level. [[1, 2], [3], []] -> [1, 2, 3]. Hint: two `for`s in one comprehension."""
    ...


def sort_by_length(words):
    """Return words sorted by length; ties are alphabetical.
    ['pear', 'fig', 'apple', 'kiwi'] -> ['fig', 'kiwi', 'pear', 'apple']. Hint: key=lambda with a tuple."""
    ...


def sort_by_score_desc(pairs):
    """pairs is a list of (name, score). Return it sorted by score, highest first;
    ties keep original order. [('a', 1), ('b', 3), ('c', 3)] -> [('b', 3), ('c', 3), ('a', 1)].
    Hint: sorted is stable; use reverse=True (it keeps tie order too)."""
    ...


def index_of_max(nums):
    """Return the index of the largest value (first one on ties); None for an empty list.
    Hint: max(range(len(nums)), key=...) or enumerate."""
    ...


def pairwise_sum(a, b):
    """Add two lists element by element (stop at the shorter). [1, 2, 3], [10, 20] -> [11, 22].
    Hint: zip."""
    ...


def numbered(items):
    """Return strings like '1. apple' numbered from 1. ['a', 'b'] -> ['1. a', '2. b'].
    Hint: enumerate(items, start=1)."""
    ...


def evens_up_to(n):
    """GENERATOR: yield the even numbers from 0 up to and including n, one at a time.
    list(evens_up_to(7)) -> [0, 2, 4, 6]. Use `yield`, do not build a list."""
    ...


def fib_generator():
    """INFINITE GENERATOR yielding 0, 1, 1, 2, 3, 5, 8, ... forever.
    Tests take the first few with itertools.islice."""
    ...


def chunks(items, size):
    """GENERATOR: yield consecutive slices of `items` of length `size` (last may be shorter).
    list(chunks([1,2,3,4,5], 2)) -> [[1,2],[3,4],[5]]. Raise ValueError if size < 1
    (note: a generator raises only once you start iterating it)."""
    ...


def running_total(nums):
    """GENERATOR: yield the running (cumulative) sum. [1, 2, 3, 4] -> 1, 3, 6, 10."""
    ...


def top_n_words(text, n):
    """Return the n most frequent words (lowercase, split on whitespace) as a list of words.
    Order: highest count first; ties alphabetical.
    'b a b c a b' with n=2 -> ['b', 'a']. Hint: count in a dict, then sorted with
    key=lambda w: (-counts[w], w)."""
    ...
