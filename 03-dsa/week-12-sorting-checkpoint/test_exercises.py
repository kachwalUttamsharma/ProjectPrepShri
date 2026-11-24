import random
from collections import Counter

from exercises import *


def build(vals):
    dummy = cur = ListNode()
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ------------------------------ Part A ------------------------------

def test_merge_sort():
    assert merge_sort([5, 2, 3, 1]) == [1, 2, 3, 5]
    assert merge_sort([]) == []
    assert merge_sort([1]) == [1]
    assert merge_sort([2, 1]) == [1, 2]
    assert merge_sort([3, 3, 3]) == [3, 3, 3]
    assert merge_sort([-1, -5, 0, 7, -5]) == [-5, -5, -1, 0, 7]
    orig = [4, 3, 2, 1]
    out = merge_sort(orig)
    assert orig == [4, 3, 2, 1] and out == [1, 2, 3, 4]
    random.seed(3)
    for _ in range(50):
        a = [random.randint(-30, 30) for _ in range(random.randint(0, 40))]
        assert merge_sort(a) == sorted(a)
    big = [random.randint(-10 ** 6, 10 ** 6) for _ in range(50_000)]
    assert merge_sort(big) == sorted(big)


def test_merge_sort_stable():
    class Item:
        def __init__(self, k, tag):
            self.k, self.tag = k, tag

        def __lt__(self, o):
            return self.k < o.k

        def __le__(self, o):
            return self.k <= o.k

        def __gt__(self, o):
            return self.k > o.k

        def __ge__(self, o):
            return self.k >= o.k

    items = [Item(1, "a"), Item(0, "b"), Item(1, "c"), Item(0, "d")]
    out = merge_sort(items)
    assert [i.tag for i in out] == ["b", "d", "a", "c"]


def test_quick_sort():
    assert quick_sort([3, 1, 2, 3, 3]) == [1, 2, 3, 3, 3]
    assert quick_sort([]) == []
    assert quick_sort([9]) == [9]
    assert quick_sort([2, 1]) == [1, 2]
    assert quick_sort([-3, 5, -3, 0]) == [-3, -3, 0, 5]
    orig = [3, 2, 1]
    assert quick_sort(orig) == [1, 2, 3] and orig == [3, 2, 1]
    random.seed(4)
    for _ in range(50):
        a = [random.randint(-9, 9) for _ in range(random.randint(0, 40))]
        assert quick_sort(a) == sorted(a)
    assert quick_sort([7] * 20_000) == [7] * 20_000
    asc = list(range(20_000))
    assert quick_sort(asc) == asc
    assert quick_sort(asc[::-1]) == asc
    big = [random.randint(0, 10 ** 6) for _ in range(50_000)]
    assert quick_sort(big) == sorted(big)


def test_sort_colors():
    for arr in ([2, 0, 2, 1, 1, 0], [2, 0, 1], [1, 0], [2, 2, 1, 1, 0, 0], [1, 2, 0, 1]):
        exp = sorted(arr)
        assert sort_colors(arr) is None
        assert arr == exp
    a = [1]
    sort_colors(a)
    assert a == [1]
    a = []
    sort_colors(a)
    assert a == []
    a = [2, 2, 2, 0, 0]
    sort_colors(a)
    assert a == [0, 0, 2, 2, 2]
    random.seed(5)
    big = [random.randint(0, 2) for _ in range(100_000)]
    exp = sorted(big)
    sort_colors(big)
    assert big == exp


def test_merge_intervals():
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([]) == []
    assert merge_intervals([[1, 2]]) == [[1, 2]]
    assert merge_intervals([[5, 6], [1, 2], [3, 4]]) == [[1, 2], [3, 4], [5, 6]]
    assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]
    assert merge_intervals([[2, 3], [1, 10]]) == [[1, 10]]
    assert merge_intervals([[-5, -1], [-3, 2]]) == [[-5, 2]]
    assert merge_intervals([[1, 1], [1, 1]]) == [[1, 1]]
    big = [[i, i + 1] for i in range(50_000)]
    assert merge_intervals(big) == [[0, 50_000]]


def test_largest_number():
    assert largest_number([10, 2]) == "210"
    assert largest_number([3, 30, 34, 5, 9]) == "9534330"
    assert largest_number([0, 0]) == "0"
    assert largest_number([0]) == "0"
    assert largest_number([1]) == "1"
    assert largest_number([121, 12]) == "12121"
    assert largest_number([824, 8247]) == "8248247"
    assert largest_number([432, 43243]) == "43243432"
    assert largest_number([5, 5, 5]) == "555"
    assert largest_number([0, 0, 1]) == "100"
    assert largest_number([999999998, 999999997, 999999999]) == "999999999999999998999999997"


def test_frequency_sort():
    assert frequency_sort("tree") == "eert"
    assert frequency_sort("cccaaa") == "aaaccc"
    assert frequency_sort("") == ""
    assert frequency_sort("a") == "a"
    assert frequency_sort("Aabb") == "bbAa"
    assert frequency_sort("abc") == "abc"
    s = "zzyyx" * 1000
    assert frequency_sort(s) == "y" * 2000 + "z" * 2000 + "x" * 1000
    out = frequency_sort("hello world")
    assert Counter(out) == Counter("hello world")
    assert out.startswith("lll") and out[3:5] == "oo"


def test_k_closest():
    assert k_closest([[1, 3], [-2, 2]], 1) == [[-2, 2]]
    assert k_closest([[3, 3], [5, -1], [-2, 4]], 2) == [[3, 3], [-2, 4]]
    assert k_closest([[0, 0]], 1) == [[0, 0]]
    assert k_closest([[1, 1], [1, 1], [2, 2]], 2) == [[1, 1], [1, 1]]
    assert k_closest([[2, 0], [-2, 0], [0, 2], [0, -2]], 4) == [[-2, 0], [0, -2], [0, 2], [2, 0]]
    assert k_closest([[1, 0], [0, 1], [-1, 0]], 2) == [[-1, 0], [0, 1]]
    random.seed(6)
    pts = [[random.randint(-100, 100), random.randint(-100, 100)] for _ in range(20_000)]
    exp = sorted(pts, key=lambda p: (p[0] ** 2 + p[1] ** 2, p[0], p[1]))[:50]
    assert k_closest(pts, 50) == exp


def _brute_inv(a):
    return sum(1 for i in range(len(a)) for j in range(i + 1, len(a)) if a[i] > a[j])


def test_count_inversions():
    assert count_inversions([2, 4, 1, 3, 5]) == 3
    assert count_inversions([5, 4, 3, 2, 1]) == 10
    assert count_inversions([1, 2, 3]) == 0
    assert count_inversions([]) == 0
    assert count_inversions([1]) == 0
    assert count_inversions([2, 2, 2]) == 0
    assert count_inversions([3, 1, 2, 1]) == 4
    random.seed(8)
    for _ in range(100):
        a = [random.randint(-10, 10) for _ in range(random.randint(0, 30))]
        assert count_inversions(a) == _brute_inv(a)
    n = 100_000
    assert count_inversions(list(range(n, 0, -1))) == n * (n - 1) // 2


def test_kth_largest():
    assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert kth_largest([1], 1) == 1
    assert kth_largest([2, 1], 2) == 1
    assert kth_largest([7, 7, 7], 3) == 7
    assert kth_largest([-1, -2, -3], 1) == -1
    orig = [3, 1, 2]
    kth_largest(orig, 1)
    random.seed(9)
    for _ in range(100):
        a = [random.randint(-20, 20) for _ in range(random.randint(1, 30))]
        k = random.randint(1, len(a))
        assert kth_largest(a, k) == sorted(a, reverse=True)[k - 1]
    big = [random.randint(0, 10 ** 9) for _ in range(100_000)]
    assert kth_largest(big, 1234) == sorted(big, reverse=True)[1233]
    assert kth_largest([5] * 50_000, 25_000) == 5


def test_sort_students():
    s = [("bo", 90, 20), ("al", 90, 19), ("cy", 95, 30)]
    assert sort_students(s) == [("cy", 95, 30), ("al", 90, 19), ("bo", 90, 20)]
    assert sort_students([]) == []
    assert sort_students([("a", 1, 1)]) == [("a", 1, 1)]
    assert sort_students([("b", 80, 20), ("a", 80, 20)]) == [("a", 80, 20), ("b", 80, 20)]
    assert sort_students([("x", -1, 5), ("y", 0, 5)]) == [("y", 0, 5), ("x", -1, 5)]
    assert s[0] == ("bo", 90, 20)


# ------------------------------ Part B (mock) ------------------------------

def test_longest_unique_substring():
    assert longest_unique_substring("abcabcbb") == 3
    assert longest_unique_substring("bbbbb") == 1
    assert longest_unique_substring("pwwkew") == 3
    assert longest_unique_substring("") == 0
    assert longest_unique_substring("a") == 1
    assert longest_unique_substring("abba") == 2
    assert longest_unique_substring("tmmzuxt") == 5
    assert longest_unique_substring("dvdf") == 3
    assert longest_unique_substring("ab" * 50_000) == 2
    assert longest_unique_substring("".join(chr(33 + i) for i in range(90)) * 1000) == 90


def test_daily_temperatures():
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([30, 60, 90]) == [1, 1, 0]
    assert daily_temperatures([]) == []
    assert daily_temperatures([5]) == [0]
    assert daily_temperatures([5, 5, 5]) == [0, 0, 0]
    assert daily_temperatures([90, 80, 70]) == [0, 0, 0]
    assert daily_temperatures([-5, -10, 0]) == [2, 1, 0]
    n = 100_000
    assert daily_temperatures(list(range(n, 0, -1))) == [0] * n
    assert daily_temperatures(list(range(n))) == [1] * (n - 1) + [0]


def test_subarray_sum_k():
    assert subarray_sum_k([1, 1, 1], 2) == 2
    assert subarray_sum_k([1, 2, 3], 3) == 2
    assert subarray_sum_k([1, -1, 0], 0) == 3
    assert subarray_sum_k([], 0) == 0
    assert subarray_sum_k([0, 0, 0], 0) == 6
    assert subarray_sum_k([5], 5) == 1
    assert subarray_sum_k([5], 4) == 0
    assert subarray_sum_k([-1, -1, 1], 0) == 1
    assert subarray_sum_k([3, 4, 7, 2, -3, 1, 4, 2], 7) == 4
    assert subarray_sum_k([1] * 100_000, 2) == 99_999
    assert subarray_sum_k([0] * 2000, 0) == 2000 * 2001 // 2


def test_merge_two_lists():
    assert to_list(merge_two_lists(build([1, 2, 4]), build([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    assert merge_two_lists(None, None) is None
    assert to_list(merge_two_lists(None, build([0]))) == [0]
    assert to_list(merge_two_lists(build([0]), None)) == [0]
    assert to_list(merge_two_lists(build([1, 2]), build([3, 4]))) == [1, 2, 3, 4]
    assert to_list(merge_two_lists(build([3, 4]), build([1, 2]))) == [1, 2, 3, 4]
    assert to_list(merge_two_lists(build([-3, 0]), build([-3, 0]))) == [-3, -3, 0, 0]
    a, b = build([1, 3]), build([2])
    head = merge_two_lists(a, b)
    assert head is a  # spliced nodes, not copies
    n = 100_000
    out = to_list(merge_two_lists(build(range(0, n, 2)), build(range(1, n, 2))))
    assert out == list(range(n))


def test_min_meeting_rooms():
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert min_meeting_rooms([]) == 0
    assert min_meeting_rooms([[1, 5]]) == 1
    assert min_meeting_rooms([[1, 5], [5, 10]]) == 1
    assert min_meeting_rooms([[1, 5], [1, 5], [1, 5]]) == 3
    assert min_meeting_rooms([[1, 10], [2, 3], [4, 5], [6, 7]]) == 2
    assert min_meeting_rooms([[9, 10], [4, 9], [4, 17]]) == 2
    assert min_meeting_rooms([[i, i + 1] for i in range(50_000)]) == 1
    assert min_meeting_rooms([[0, 10 ** 9]] * 1000) == 1000
