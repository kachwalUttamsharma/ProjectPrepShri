import copy
from exercises import *


def test_reverse_string():
    a = list("hello")
    assert reverse_string(a) is None
    assert a == list("olleh")
    b = list("abcd")
    reverse_string(b)
    assert b == list("dcba")
    c = ["x"]
    reverse_string(c)
    assert c == ["x"]
    e = []
    reverse_string(e)
    assert e == []
    big = list(range(100000))
    reverse_string(big)
    assert big == list(range(99999, -1, -1))
    d = ["a", "b"]
    reverse_string(d)
    assert d == ["b", "a"]


def test_move_zeroes():
    a = [0, 1, 0, 3, 12]
    assert move_zeroes(a) is None
    assert a == [1, 3, 12, 0, 0]
    for src, exp in [([], []), ([0], [0]), ([1], [1]), ([0, 0, 0], [0, 0, 0]),
                     ([1, 2, 3], [1, 2, 3]), ([0, 0, 1], [1, 0, 0]), ([-1, 0, -2], [-1, -2, 0])]:
        x = list(src)
        move_zeroes(x)
        assert x == exp
    big = [0, 1] * 50000
    move_zeroes(big)
    assert big == [1] * 50000 + [0] * 50000


def test_is_palindrome():
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome("") is True
    assert is_palindrome(" ") is True
    assert is_palindrome(".,") is True
    assert is_palindrome("a") is True
    assert is_palindrome("ab") is False
    assert is_palindrome("0P") is False
    assert is_palindrome("Aa") is True
    assert is_palindrome("a" * 100000) is True
    assert is_palindrome("a" * 50000 + "b" + "a" * 49999) is False


def test_longest_common_prefix():
    assert longest_common_prefix(["flower", "flow", "flight"]) == "fl"
    assert longest_common_prefix(["dog", "car"]) == ""
    assert longest_common_prefix(["a"]) == "a"
    assert longest_common_prefix([]) == ""
    assert longest_common_prefix(["", "abc"]) == ""
    assert longest_common_prefix(["abc", "abc", "abc"]) == "abc"
    assert longest_common_prefix(["ab", "abc"]) == "ab"
    assert longest_common_prefix(["a" * 1000 + "x", "a" * 1000 + "y"]) == "a" * 1000


def test_remove_duplicates_sorted():
    a = [0, 0, 1, 1, 1, 2]
    k = remove_duplicates_sorted(a)
    assert k == 3 and a[:k] == [0, 1, 2]
    b = []
    assert remove_duplicates_sorted(b) == 0
    c = [5]
    assert remove_duplicates_sorted(c) == 1 and c[:1] == [5]
    d = [1, 1, 1, 1]
    k = remove_duplicates_sorted(d)
    assert k == 1 and d[:1] == [1]
    e = [-3, -3, -1, 0, 0, 4]
    k = remove_duplicates_sorted(e)
    assert k == 4 and e[:k] == [-3, -1, 0, 4]
    f = [1, 2, 3]
    assert remove_duplicates_sorted(f) == 3 and f == [1, 2, 3]
    big = sorted(list(range(50000)) * 2)
    k = remove_duplicates_sorted(big)
    assert k == 50000 and big[:k] == list(range(50000))


def test_rotate_array():
    a = [1, 2, 3, 4, 5, 6, 7]
    assert rotate_array(a, 3) is None
    assert a == [5, 6, 7, 1, 2, 3, 4]
    for src, k, exp in [([1, 2], 3, [2, 1]), ([1], 5, [1]), ([], 2, []), ([1, 2, 3], 0, [1, 2, 3]),
                        ([1, 2, 3], 3, [1, 2, 3]), ([-1, -100, 3, 99], 2, [3, 99, -1, -100]),
                        ([1, 2, 3], 4, [3, 1, 2])]:
        x = list(src)
        rotate_array(x, k)
        assert x == exp
    big = list(range(100000))
    rotate_array(big, 1)
    assert big[0] == 99999 and big[1] == 0


def test_product_except_self():
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([0, 2, 3]) == [6, 0, 0]
    assert product_except_self([0, 0, 3]) == [0, 0, 0]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    assert product_except_self([5]) == [1]
    assert product_except_self([2, 3]) == [3, 2]
    assert product_except_self([]) == []
    assert product_except_self([-2, 3]) == [3, -2]
    out = product_except_self([1] * 100000)
    assert out == [1] * 100000
    src = [1, 2, 3]
    product_except_self(src)
    assert src == [1, 2, 3]


def test_merge_sorted_array():
    a = [1, 2, 3, 0, 0, 0]
    assert merge_sorted_array(a, 3, [2, 5, 6], 3) is None
    assert a == [1, 2, 2, 3, 5, 6]
    b = [1]
    merge_sorted_array(b, 1, [], 0)
    assert b == [1]
    c = [0]
    merge_sorted_array(c, 0, [1], 1)
    assert c == [1]
    d = [4, 5, 6, 0, 0, 0]
    merge_sorted_array(d, 3, [1, 2, 3], 3)
    assert d == [1, 2, 3, 4, 5, 6]
    e = [-1, 0, 0, 0, 0, 0, 0]
    merge_sorted_array(e, 1, [-3, -2, 0, 0, 2, 3][:6], 6)
    assert e == [-3, -2, -1, 0, 0, 2, 3]
    f = [2, 0]
    merge_sorted_array(f, 1, [1], 1)
    assert f == [1, 2]
    big1 = list(range(0, 100000, 2)) + [0] * 50000
    big2 = list(range(1, 100000, 2))
    merge_sorted_array(big1, 50000, big2, 50000)
    assert big1 == list(range(100000))


def test_compress_string():
    a = ["a", "a", "b", "b", "c", "c", "c"]
    k = compress_string(a)
    assert k == 6 and a[:k] == ["a", "2", "b", "2", "c", "3"]
    b = ["a"]
    k = compress_string(b)
    assert k == 1 and b[:1] == ["a"]
    c = ["a"] * 12
    k = compress_string(c)
    assert k == 3 and c[:k] == ["a", "1", "2"]
    d = list("abc")
    k = compress_string(d)
    assert k == 3 and d[:k] == list("abc")
    e = ["a"] + ["b"] * 12
    k = compress_string(e)
    assert k == 4 and e[:k] == ["a", "b", "1", "2"]
    f = []
    assert compress_string(f) == 0
    g = ["a", "a", "b", "a", "a"]
    k = compress_string(g)
    assert g[:k] == ["a", "2", "b", "a", "2"]
    big = ["x"] * 100000
    k = compress_string(big)
    assert big[:k] == list("x100000")


def test_spiral_order():
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5]
    assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]
    assert spiral_order([[1, 2, 3]]) == [1, 2, 3]
    assert spiral_order([[1], [2], [3]]) == [1, 2, 3]
    assert spiral_order([[5]]) == [5]
    assert spiral_order([]) == []
    assert spiral_order([[1, 2], [3, 4]]) == [1, 2, 4, 3]
    assert spiral_order([[1, 2], [3, 4], [5, 6]]) == [1, 2, 4, 6, 5, 3]
    n = 300
    grid = [[r * n + c for c in range(n)] for r in range(n)]
    out = spiral_order(grid)
    assert len(out) == n * n and sorted(out) == list(range(n * n))
    assert out[:3] == [0, 1, 2]


def test_rotate_image():
    a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert rotate_image(a) is None
    assert a == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    b = [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]
    rotate_image(b)
    assert b == [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]
    c = [[1]]
    rotate_image(c)
    assert c == [[1]]
    d = [[1, 2], [3, 4]]
    rotate_image(d)
    assert d == [[3, 1], [4, 2]]
    n = 200
    m = [[r * n + c for c in range(n)] for r in range(n)]
    orig = copy.deepcopy(m)
    for _ in range(4):
        rotate_image(m)
    assert m == orig
    rows = [id(r) for r in m]
    rotate_image(m)
    assert [id(r) for r in m] == rows  # still the same row objects (in place)


def test_longest_palindromic_substring():
    assert longest_palindromic_substring("babad") in ("bab", "aba")
    assert longest_palindromic_substring("cbbd") == "bb"
    assert longest_palindromic_substring("a") == "a"
    assert longest_palindromic_substring("") == ""
    assert longest_palindromic_substring("ac") in ("a", "c")
    assert longest_palindromic_substring("aaaa") == "aaaa"
    assert longest_palindromic_substring("forgeeksskeegfor") == "geeksskeeg"
    assert longest_palindromic_substring("abcdedcbaxyz") == "abcdedcba"
    s = "a" * 1500
    assert longest_palindromic_substring(s) == s
    t = "ab" * 700
    r = longest_palindromic_substring(t)
    assert len(r) == 1399 and r == r[::-1] and r in t
