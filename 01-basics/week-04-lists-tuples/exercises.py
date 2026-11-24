"""Week 4 exercises. Replace each `...` with your code."""


def second_largest(nums):
    """Return the second largest DISTINCT value in a list, or None if there isn't one.
    [3, 1, 4, 4] -> 3; [2, 2] -> None; [] -> None.
    Hint: set(nums) removes duplicates; sorted() orders them."""
    ...


def rotate_left(nums, k):
    """Return a NEW list rotated left by k positions. rotate_left([1,2,3,4,5], 2) -> [3,4,5,1,2].
    k may be larger than len(nums) or 0; empty list returns []. Hint: k % len(nums) and slicing."""
    ...


def remove_duplicates(nums):
    """Return a new list with duplicates removed, keeping the FIRST occurrence order.
    [3, 1, 3, 2, 1] -> [3, 1, 2]"""
    ...


def merge_sorted(a, b):
    """Merge two already-sorted lists into one sorted list WITHOUT using sorted()/sort().
    [1, 4, 6], [2, 3, 7] -> [1, 2, 3, 4, 6, 7]. Hint: two index variables, compare heads."""
    ...


def swap_ends(t):
    """Given a tuple of length >= 2, return a new tuple with first and last swapped.
    (1, 2, 3, 4) -> (4, 2, 3, 1). Hint: tuples are immutable, so build a new one."""
    ...


def clean_and_split(text):
    """Strip the text, lowercase it, and return the list of words split on whitespace.
    '  Hello   BIG World ' -> ['hello', 'big', 'world']. Empty/blank -> []."""
    ...


def title_case_words(sentence):
    """Capitalize the first letter of each word, lowercase the rest, single spaces between.
    'hELLO   wORLD' -> 'Hello World'. Hint: split(), str.capitalize(), ' '.join()."""
    ...


def is_anagram(a, b):
    """Return True if a and b use the same letters (ignoring case and spaces).
    'Listen', 'Silent' -> True; 'abc', 'abd' -> False. Hint: compare sorted letters."""
    ...


def transpose(matrix):
    """Return the transpose of a rectangular list of lists (rows become columns).
    [[1,2,3],[4,5,6]] -> [[1,4],[2,5],[3,6]]. Empty matrix -> []. Do not modify the input."""
    ...


def safe_copy_and_append(nested, value):
    """Return a copy of `nested` (a list of lists) where `value` is appended to EACH inner list.
    The original and its inner lists must NOT change.
    Hint: build new inner lists (inner + [value]) instead of calling .append on the originals."""
    ...


def spiral_order(matrix):
    """Return the elements of a rectangular matrix in clockwise spiral order.
    [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5]. Empty -> [].
    Hint: peel the top row, then rotate the rest (transpose + reverse), repeat."""
    ...
