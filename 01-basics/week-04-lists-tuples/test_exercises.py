from exercises import *


def test_second_largest():
    assert second_largest([3, 1, 4, 4]) == 3
    assert second_largest([2, 2]) is None
    assert second_largest([]) is None
    assert second_largest([5]) is None
    assert second_largest([-1, -5, -3]) == -3
    assert second_largest([1, 2]) == 1


def test_rotate_left():
    assert rotate_left([1, 2, 3, 4, 5], 2) == [3, 4, 5, 1, 2]
    assert rotate_left([1, 2, 3], 0) == [1, 2, 3]
    assert rotate_left([1, 2, 3], 3) == [1, 2, 3]
    assert rotate_left([1, 2, 3], 4) == [2, 3, 1]
    assert rotate_left([], 5) == []
    src = [1, 2, 3]
    out = rotate_left(src, 1)
    assert src == [1, 2, 3] and out is not src


def test_remove_duplicates():
    assert remove_duplicates([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert remove_duplicates([]) == []
    assert remove_duplicates([1, 1, 1]) == [1]
    assert remove_duplicates(["a", "b", "a"]) == ["a", "b"]


def test_merge_sorted():
    assert merge_sorted([1, 4, 6], [2, 3, 7]) == [1, 2, 3, 4, 6, 7]
    assert merge_sorted([], [1, 2]) == [1, 2]
    assert merge_sorted([1, 2], []) == [1, 2]
    assert merge_sorted([], []) == []
    assert merge_sorted([1, 1], [1]) == [1, 1, 1]


def test_swap_ends():
    assert swap_ends((1, 2, 3, 4)) == (4, 2, 3, 1)
    assert swap_ends((1, 2)) == (2, 1)
    assert isinstance(swap_ends((1, 2)), tuple)


def test_clean_and_split():
    assert clean_and_split("  Hello   BIG World ") == ["hello", "big", "world"]
    assert clean_and_split("") == []
    assert clean_and_split("   ") == []


def test_title_case_words():
    assert title_case_words("hELLO   wORLD") == "Hello World"
    assert title_case_words("a") == "A"
    assert title_case_words("") == ""


def test_is_anagram():
    assert is_anagram("Listen", "Silent") is True
    assert is_anagram("abc", "abd") is False
    assert is_anagram("a gentleman", "elegant man") is True
    assert is_anagram("aab", "ab") is False
    assert is_anagram("", "") is True


def test_transpose():
    assert transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
    assert transpose([[1]]) == [[1]]
    assert transpose([]) == []
    m = [[1, 2], [3, 4]]
    transpose(m)
    assert m == [[1, 2], [3, 4]]


def test_safe_copy_and_append():
    original = [[1], [2, 3]]
    result = safe_copy_and_append(original, 9)
    assert result == [[1, 9], [2, 3, 9]]
    assert original == [[1], [2, 3]]
    assert safe_copy_and_append([], 1) == []


def test_spiral_order():
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert spiral_order([[1, 2, 3, 4]]) == [1, 2, 3, 4]
    assert spiral_order([[1], [2], [3]]) == [1, 2, 3]
    assert spiral_order([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]
    assert spiral_order([]) == []
