"""Week 5 exercises. Replace each `...` with your code."""


def char_count(s):
    """Return a dict of how many times each character appears. 'aab' -> {'a': 2, 'b': 1}."""
    ...


def word_count(text):
    """Return a dict of word counts, case-insensitive, words split on whitespace.
    'the cat The dog' -> {'the': 2, 'cat': 1, 'dog': 1}"""
    ...


def most_common_char(s):
    """Return the character that appears most often. On a tie return the one that
    appears FIRST in s. Return None for an empty string. 'abca' -> 'a'; 'abcb' -> 'b'."""
    ...


def has_duplicates(items):
    """Return True if any item appears more than once. Hint: compare len(items) and len(set(items))."""
    ...


def two_sum(nums, target):
    """Return a tuple (i, j) with i < j of indexes where nums[i] + nums[j] == target,
    or None if no pair exists. two_sum([2, 7, 11, 15], 9) -> (0, 1).
    Hint: dict from value -> index; for each n look up target - n. One pass, no nested loops."""
    ...


def invert_dict(d):
    """Swap keys and values. {'a': 1, 'b': 2} -> {1: 'a', 2: 'b'}. Values are unique."""
    ...


def group_by_length(words):
    """Return a dict mapping length -> list of words of that length (original order).
    ['hi', 'yo', 'sup'] -> {2: ['hi', 'yo'], 3: ['sup']}"""
    ...


def common_elements(a, b):
    """Return a sorted list of unique items present in BOTH lists. Hint: set intersection."""
    ...


def unique_to_first(a, b):
    """Return a sorted list of unique items in a that are NOT in b. Hint: set difference."""
    ...


def merge_dicts_sum(d1, d2):
    """Merge two dicts of numbers. For keys in both, add the values. Return a NEW dict;
    do not modify the inputs. {'a': 1, 'b': 2}, {'b': 3, 'c': 4} -> {'a': 1, 'b': 5, 'c': 4}"""
    ...


def first_unique_char(s):
    """Return the index of the first character that appears exactly once in s, or -1.
    'leetcode' -> 0; 'loveleetcode' -> 2; 'aabb' -> -1. Hint: count first, then scan again."""
    ...


def group_anagrams(words):
    """Group words that are anagrams of each other. Return a list of groups; each group keeps
    input order, and groups are ordered by the first appearance of their first word.
    ['eat','tea','tan','ate','nat','bat'] -> [['eat','tea','ate'],['tan','nat'],['bat']]
    Hint: key = ''.join(sorted(word))."""
    ...
