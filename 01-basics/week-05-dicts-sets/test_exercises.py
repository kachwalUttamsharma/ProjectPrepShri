from exercises import *


def test_char_count():
    assert char_count("") == {}
    assert char_count("aab") == {"a": 2, "b": 1}
    assert char_count("a a") == {"a": 2, " ": 1}


def test_word_count():
    assert word_count("the cat The dog") == {"the": 2, "cat": 1, "dog": 1}
    assert word_count("") == {}
    assert word_count("  a   a ") == {"a": 2}


def test_most_common_char():
    assert most_common_char("abca") == "a"
    assert most_common_char("abcb") == "b"
    assert most_common_char("abc") == "a"
    assert most_common_char("") is None
    assert most_common_char("x") == "x"


def test_has_duplicates():
    assert has_duplicates([1, 2, 3]) is False
    assert has_duplicates([1, 2, 1]) is True
    assert has_duplicates([]) is False
    assert has_duplicates("hello") is True


def test_two_sum():
    assert two_sum([2, 7, 11, 15], 9) == (0, 1)
    assert two_sum([3, 2, 4], 6) == (1, 2)
    assert two_sum([3, 3], 6) == (0, 1)
    assert two_sum([1, 2, 3], 100) is None
    assert two_sum([], 1) is None
    assert two_sum([5], 10) is None  # can't reuse the same element


def test_invert_dict():
    assert invert_dict({"a": 1, "b": 2}) == {1: "a", 2: "b"}
    assert invert_dict({}) == {}


def test_group_by_length():
    assert group_by_length(["hi", "yo", "sup"]) == {2: ["hi", "yo"], 3: ["sup"]}
    assert group_by_length([]) == {}


def test_common_elements():
    assert common_elements([1, 2, 2, 3], [2, 3, 3, 4]) == [2, 3]
    assert common_elements([1], [2]) == []
    assert common_elements([], [1]) == []


def test_unique_to_first():
    assert unique_to_first([1, 2, 2, 3], [3, 4]) == [1, 2]
    assert unique_to_first([1], [1]) == []
    assert unique_to_first([3, 1, 2], []) == [1, 2, 3]


def test_merge_dicts_sum():
    d1, d2 = {"a": 1, "b": 2}, {"b": 3, "c": 4}
    assert merge_dicts_sum(d1, d2) == {"a": 1, "b": 5, "c": 4}
    assert d1 == {"a": 1, "b": 2} and d2 == {"b": 3, "c": 4}
    assert merge_dicts_sum({}, {}) == {}
    assert merge_dicts_sum({"a": 1}, {}) == {"a": 1}


def test_first_unique_char():
    assert first_unique_char("leetcode") == 0
    assert first_unique_char("loveleetcode") == 2
    assert first_unique_char("aabb") == -1
    assert first_unique_char("") == -1


def test_group_anagrams():
    assert group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [
        ["eat", "tea", "ate"],
        ["tan", "nat"],
        ["bat"],
    ]
    assert group_anagrams([]) == []
    assert group_anagrams([""]) == [[""]]
    assert group_anagrams(["a", "b", "a"]) == [["a", "a"], ["b"]]
