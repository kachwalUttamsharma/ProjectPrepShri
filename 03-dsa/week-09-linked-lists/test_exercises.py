import random

from exercises import *


def build(vals):
    dummy = tail = ListNode()
    for v in vals:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head, limit=10 ** 7):
    out = []
    while head and len(out) < limit:
        out.append(head.val)
        head = head.next
    return out


def build_cycle(vals, pos):
    """Build a list and link the tail back to index pos (-1 = no cycle).
    Returns (head, node_at_pos)."""
    nodes = [ListNode(v) for v in vals]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    if nodes and pos >= 0:
        nodes[-1].next = nodes[pos]
    return (nodes[0] if nodes else None), (nodes[pos] if nodes and pos >= 0 else None)


# ---------- reverse_list ----------
def test_reverse_list():
    assert to_list(reverse_list(build([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert to_list(reverse_list(build([1, 2]))) == [2, 1]
    assert to_list(reverse_list(build([7]))) == [7]
    assert to_list(reverse_list(build([1, 1, 2, 2]))) == [2, 2, 1, 1]
    assert reverse_list(None) is None


def test_reverse_list_reuses_nodes_and_terminates():
    head = build([1, 2, 3])
    new = reverse_list(head)
    assert new.val == 3
    assert head.next is None   # old head is now the tail
    assert to_list(new, limit=10) == [3, 2, 1]


def test_reverse_list_large():
    n = 100000
    assert to_list(reverse_list(build(range(n)))) == list(range(n - 1, -1, -1))


# ---------- middle_node ----------
def test_middle_node():
    h = build([1, 2, 3, 4, 5])
    assert middle_node(h).val == 3
    h = build([1, 2, 3, 4])
    assert middle_node(h).val == 3
    assert middle_node(build([1])).val == 1
    h = build([1, 2])
    assert middle_node(h) is h.next
    assert to_list(middle_node(build([1, 2, 3, 4, 5, 6]))) == [4, 5, 6]


def test_middle_node_large():
    assert middle_node(build(range(100001))).val == 50000
    assert middle_node(build(range(100000))).val == 50000


# ---------- merge_two_lists ----------
def test_merge_two_lists():
    assert to_list(merge_two_lists(build([1, 2, 4]), build([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    assert to_list(merge_two_lists(build([]), build([0]))) == [0]
    assert to_list(merge_two_lists(build([5]), build([]))) == [5]
    assert merge_two_lists(None, None) is None
    assert to_list(merge_two_lists(build([1, 2, 3]), build([4, 5, 6]))) == [1, 2, 3, 4, 5, 6]
    assert to_list(merge_two_lists(build([4, 5, 6]), build([1, 2, 3]))) == [1, 2, 3, 4, 5, 6]
    assert to_list(merge_two_lists(build([-3, -1]), build([-2, 0]))) == [-3, -2, -1, 0]
    assert to_list(merge_two_lists(build([2, 2]), build([2, 2]))) == [2, 2, 2, 2]


def test_merge_two_lists_splices_nodes_and_stable():
    a, b = build([1]), build([1])
    m = merge_two_lists(a, b)
    assert m is a and m.next is b   # tie -> take l1 first, reuse nodes


def test_merge_two_lists_large():
    a = sorted(random.Random(1).sample(range(10 ** 6), 50000))
    b = sorted(random.Random(2).sample(range(10 ** 6), 50000))
    assert to_list(merge_two_lists(build(a), build(b))) == sorted(a + b)


# ---------- has_cycle ----------
def test_has_cycle():
    assert has_cycle(build_cycle([3, 2, 0, -4], 1)[0]) is True
    assert has_cycle(build_cycle([1, 2], 0)[0]) is True
    assert has_cycle(build_cycle([1], 0)[0]) is True
    assert has_cycle(build_cycle([1, 2, 3], 2)[0]) is True
    assert has_cycle(build_cycle([1, 2], -1)[0]) is False
    assert has_cycle(build_cycle([1], -1)[0]) is False
    assert has_cycle(None) is False
    assert has_cycle(build([5, 5, 5, 5])) is False   # equal values, no cycle


def test_has_cycle_large():
    assert has_cycle(build_cycle(list(range(100000)), 0)[0]) is True
    assert has_cycle(build_cycle(list(range(100000)), -1)[0]) is False
    assert has_cycle(build_cycle(list(range(100000)), 99999)[0]) is True


# ---------- is_palindrome_list ----------
def test_is_palindrome_list():
    assert is_palindrome_list(build([1, 2, 2, 1])) is True
    assert is_palindrome_list(build([1, 2, 3, 2, 1])) is True
    assert is_palindrome_list(build([1, 2])) is False
    assert is_palindrome_list(build([1, 2, 3])) is False
    assert is_palindrome_list(build([1])) is True
    assert is_palindrome_list(build([1, 1])) is True
    assert is_palindrome_list(None) is True
    assert is_palindrome_list(build([1, 2, 3, 3, 1])) is False
    assert is_palindrome_list(build([9, 8, 7, 8, 9])) is True


def test_is_palindrome_list_large():
    half = list(range(50000))
    assert is_palindrome_list(build(half + half[::-1])) is True
    assert is_palindrome_list(build(half + [-1] + half[::-1])) is True
    assert is_palindrome_list(build(half + [1] + half[::-1][:-1] + [5])) is False


# ---------- remove_nth_from_end ----------
def test_remove_nth_from_end():
    assert to_list(remove_nth_from_end(build([1, 2, 3, 4, 5]), 2)) == [1, 2, 3, 5]
    assert remove_nth_from_end(build([1]), 1) is None
    assert to_list(remove_nth_from_end(build([1, 2]), 1)) == [1]
    assert to_list(remove_nth_from_end(build([1, 2]), 2)) == [2]
    assert to_list(remove_nth_from_end(build([1, 2, 3]), 3)) == [2, 3]   # remove head
    assert to_list(remove_nth_from_end(build([1, 2, 3]), 1)) == [1, 2]   # remove tail
    assert to_list(remove_nth_from_end(build([1, 1, 1]), 2)) == [1, 1]


def test_remove_nth_from_end_large():
    n = 100000
    assert to_list(remove_nth_from_end(build(range(n)), 50000)) == [x for x in range(n) if x != 50000]


# ---------- detect_cycle_start ----------
def test_detect_cycle_start():
    for vals, pos in [([3, 2, 0, -4], 1), ([1, 2], 0), ([1], 0), ([1, 2, 3, 4, 5], 4),
                      ([1, 2, 3, 4, 5], 2), ([1, 2, 3, 4, 5, 6, 7], 0)]:
        head, node = build_cycle(vals, pos)
        assert detect_cycle_start(head) is node


def test_detect_cycle_start_none():
    assert detect_cycle_start(build([1, 2])) is None
    assert detect_cycle_start(build([1])) is None
    assert detect_cycle_start(None) is None
    assert detect_cycle_start(build([4, 4, 4])) is None
    head, node = build_cycle([4, 4, 4], 1)
    assert detect_cycle_start(head) is node


def test_detect_cycle_start_distinct_equal_values():
    head, node = build_cycle([7, 7, 7, 7, 7], 3)
    assert detect_cycle_start(head) is node


def test_detect_cycle_start_large():
    head, node = build_cycle(list(range(100000)), 54321)
    assert detect_cycle_start(head) is node


# ---------- add_two_numbers ----------
def test_add_two_numbers():
    assert to_list(add_two_numbers(build([2, 4, 3]), build([5, 6, 4]))) == [7, 0, 8]
    assert to_list(add_two_numbers(build([0]), build([0]))) == [0]
    assert to_list(add_two_numbers(build([9, 9, 9, 9]), build([1]))) == [0, 0, 0, 0, 1]
    assert to_list(add_two_numbers(build([1]), build([9, 9]))) == [0, 0, 1]
    assert to_list(add_two_numbers(build([5]), build([5]))) == [0, 1]
    assert to_list(add_two_numbers(build([1, 2, 3]), build([0]))) == [1, 2, 3]


def test_add_two_numbers_random_and_large():
    rnd = random.Random(3)
    for _ in range(100):
        a = rnd.randint(0, 10 ** 12)
        b = rnd.randint(0, 10 ** 12)
        da = [int(c) for c in str(a)[::-1]]
        db = [int(c) for c in str(b)[::-1]]
        exp = [int(c) for c in str(a + b)[::-1]]
        assert to_list(add_two_numbers(build(da), build(db))) == exp
    big = [9] * 50000
    assert to_list(add_two_numbers(build(big), build([1]))) == [0] * 50000 + [1]


# ---------- reorder_list ----------
def test_reorder_list():
    h = build([1, 2, 3, 4])
    assert reorder_list(h) is None
    assert to_list(h, limit=100) == [1, 4, 2, 3]
    h = build([1, 2, 3, 4, 5])
    reorder_list(h)
    assert to_list(h, limit=100) == [1, 5, 2, 4, 3]


def test_reorder_list_small():
    h = build([1])
    reorder_list(h)
    assert to_list(h, limit=10) == [1]
    h = build([1, 2])
    reorder_list(h)
    assert to_list(h, limit=10) == [1, 2]
    h = build([1, 2, 3])
    reorder_list(h)
    assert to_list(h, limit=10) == [1, 3, 2]
    assert reorder_list(None) is None


def test_reorder_list_large():
    n = 100000
    h = build(range(n))
    reorder_list(h)
    exp = []
    lo, hi = 0, n - 1
    while lo <= hi:
        exp.append(lo)
        if lo != hi:
            exp.append(hi)
        lo += 1
        hi -= 1
    assert to_list(h, limit=n + 10) == exp


# ---------- reverse_k_group ----------
def test_reverse_k_group():
    assert to_list(reverse_k_group(build([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
    assert to_list(reverse_k_group(build([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
    assert to_list(reverse_k_group(build([1, 2, 3]), 1)) == [1, 2, 3]
    assert to_list(reverse_k_group(build([1, 2]), 5)) == [1, 2]
    assert reverse_k_group(None, 3) is None
    assert to_list(reverse_k_group(build([1, 2, 3, 4]), 4)) == [4, 3, 2, 1]
    assert to_list(reverse_k_group(build([1, 2, 3, 4, 5, 6]), 3)) == [3, 2, 1, 6, 5, 4]
    assert to_list(reverse_k_group(build([1]), 1)) == [1]


def test_reverse_k_group_random_and_large():
    rnd = random.Random(4)
    for _ in range(50):
        vals = list(range(rnd.randint(0, 20)))
        k = rnd.randint(1, 6)
        exp = []
        for i in range(0, len(vals), k):
            chunk = vals[i:i + k]
            exp += chunk[::-1] if len(chunk) == k else chunk
        assert to_list(reverse_k_group(build(vals), k), limit=100) == exp
    n = 100000
    out = to_list(reverse_k_group(build(range(n)), 3))
    assert out[:6] == [2, 1, 0, 5, 4, 3]
    assert len(out) == n


# ---------- merge_k_sorted_lists ----------
def test_merge_k_sorted_lists():
    lists = [build([1, 4, 5]), build([1, 3, 4]), build([2, 6])]
    assert to_list(merge_k_sorted_lists(lists)) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_sorted_lists([]) is None
    assert merge_k_sorted_lists([None]) is None
    assert merge_k_sorted_lists([None, None]) is None
    assert to_list(merge_k_sorted_lists([None, build([1])])) == [1]
    assert to_list(merge_k_sorted_lists([build([2, 2]), build([2, 2]), build([2])])) == [2] * 5
    assert to_list(merge_k_sorted_lists([build([-2, 5]), build([-3]), build([0, 0])])) == [-3, -2, 0, 0, 5]


def test_merge_k_sorted_lists_many_and_large():
    rnd = random.Random(5)
    chunks = [sorted(rnd.randint(-1000, 1000) for _ in range(rnd.randint(0, 50))) for _ in range(100)]
    exp = sorted(x for c in chunks for x in c)
    assert to_list(merge_k_sorted_lists([build(c) for c in chunks])) == exp
    big = [build(range(i, 100000, 10)) for i in range(10)]
    assert to_list(merge_k_sorted_lists(big)) == list(range(100000))
