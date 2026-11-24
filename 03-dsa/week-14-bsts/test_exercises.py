import pytest
from collections import deque
from exercises import *


def build(vals):
    if not vals:
        return None
    nodes = [None if v is None else TreeNode(v) for v in vals]
    kids = deque(nodes[1:])
    for n in nodes:
        if n is None:
            continue
        if kids:
            n.left = kids.popleft()
        if kids:
            n.right = kids.popleft()
    return nodes[0]


def to_list(root):
    if root is None:
        return []
    out, q = [], deque([root])
    while q:
        n = q.popleft()
        if n is None:
            out.append(None)
        else:
            out.append(n.val)
            q.append(n.left)
            q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


def inorder(root):
    return [] if root is None else inorder(root.left) + [root.val] + inorder(root.right)


def height(root):
    return 0 if root is None else 1 + max(height(root.left), height(root.right))


def is_balanced(root):
    if root is None:
        return True
    return (abs(height(root.left) - height(root.right)) <= 1
            and is_balanced(root.left) and is_balanced(root.right))


def check_bst(root, lo=float("-inf"), hi=float("inf")):
    if root is None:
        return True
    return lo < root.val < hi and check_bst(root.left, lo, root.val) and check_bst(root.right, root.val, hi)


def find(root, val):
    if root is None:
        return None
    if root.val == val:
        return root
    return find(root.left, val) or find(root.right, val)


BIG = [8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13]


def test_search_bst():
    root = build([4, 2, 7, 1, 3])
    assert search_bst(root, 2) is root.left
    assert search_bst(root, 4) is root
    assert search_bst(root, 3) is root.left.right
    assert search_bst(root, 5) is None
    assert search_bst(None, 1) is None
    assert search_bst(root, 0) is None and search_bst(root, 100) is None


@pytest.mark.parametrize("vals,target,expected", [
    ([4, 2, 5, 1, 3], 3.714286, 4), ([4, 2, 5, 1, 3], 2.5, 2), ([1], 4.428, 1),
    ([4, 2, 5, 1, 3], -10, 1), ([4, 2, 5, 1, 3], 100, 5), ([4, 2, 5, 1, 3], 4.5, 4),
    ([2, 1, 3], 2.0, 2), (BIG, 12.4, 13), (BIG, 11.5, 10),
])
def test_closest_value(vals, target, expected):
    assert closest_value(build(vals), target) == expected


@pytest.mark.parametrize("vals,val", [
    ([], 5), ([4], 2), ([4], 9), ([4, 2, 7, 1, 3], 5), ([4, 2, 7, 1, 3], 0),
    ([4, 2, 7, 1, 3], 8), (BIG, 5), (BIG, 15), (BIG, 0),
])
def test_insert_into_bst(vals, val):
    root = insert_into_bst(build(vals), val)
    assert check_bst(root)
    assert inorder(root) == sorted(inorder(build(vals)) + [val])


def test_insert_keeps_root_object():
    root = build([4, 2, 7])
    assert insert_into_bst(root, 5) is root


def test_lca_bst():
    root = build([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5])
    f = lambda v: find(root, v)
    assert lca_bst(root, f(2), f(8)) is root
    assert lca_bst(root, f(2), f(4)) is f(2)
    assert lca_bst(root, f(3), f(5)) is f(4)
    assert lca_bst(root, f(0), f(5)) is f(2)
    assert lca_bst(root, f(7), f(9)) is f(8)
    assert lca_bst(root, f(5), f(5)) is f(5)
    assert lca_bst(root, f(9), f(3)) is root   # argument order must not matter


@pytest.mark.parametrize("vals,k,expected", [
    ([5, 3, 6, 2, 4, None, None, 1], 1, 1), ([5, 3, 6, 2, 4, None, None, 1], 3, 3),
    ([5, 3, 6, 2, 4, None, None, 1], 6, 6), ([1], 1, 1),
    ([3, 1, 4, None, 2], 1, 1), ([3, 1, 4, None, 2], 4, 4),
])
def test_kth_smallest(vals, k, expected):
    assert kth_smallest(build(vals), k) == expected


def test_kth_smallest_every_k():
    root = build(BIG)
    assert [kth_smallest(root, k) for k in range(1, 10)] == sorted(inorder(root))


@pytest.mark.parametrize("vals,expected", [
    ([], True), ([1], True), ([2, 1, 3], True), ([5, 1, 4, None, None, 3, 6], False),
    ([2, 2, 2], False), ([1, 1], False), ([2, 1, 2], False),
    ([5, 4, 6, None, None, 3, 7], False),    # 3 is in right subtree of 5
    ([10, 5, 15, None, None, 6, 20], False),
    ([3, 1, 5, 0, 2, 4, 6], True), (BIG, True),
    ([-2147483648], True), ([2147483647, -2147483648], True),
    ([0, -1], True), ([-1, None, 0], True),
])
def test_is_valid_bst(vals, expected):
    assert is_valid_bst(build(vals)) is expected


@pytest.mark.parametrize("n", [0, 1, 2, 3, 4, 5, 7, 10, 31, 100])
def test_sorted_array_to_bst(n):
    nums = list(range(-n, n * 2, 3))[:n]
    root = sorted_array_to_bst(nums)
    assert inorder(root) == nums
    assert check_bst(root)
    assert is_balanced(root)


def test_sorted_array_to_bst_large_is_fast():
    nums = list(range(100000))
    root = sorted_array_to_bst(nums)
    assert height(root) <= 17


@pytest.mark.parametrize("key", [8, 3, 10, 1, 6, 14, 4, 7, 13, 99, 0])
def test_delete_node_every_key(key):
    root = delete_node(build(BIG), key)
    expected = [x for x in inorder(build(BIG)) if x != key]
    assert inorder(root) == expected
    assert check_bst(root)


def test_delete_edge_cases():
    assert delete_node(None, 1) is None
    assert delete_node(build([1]), 1) is None
    r = delete_node(build([1, None, 2]), 1)
    assert to_list(r) == [2]
    r = delete_node(build([2, 1]), 2)
    assert to_list(r) == [1]


def test_delete_until_empty():
    root = build(BIG)
    for k in [8, 1, 14, 3, 10, 6, 13, 7, 4]:
        root = delete_node(root, k)
        assert check_bst(root)
    assert root is None


def test_bst_iterator():
    it = BSTIterator(build([7, 3, 15, None, None, 9, 20]))
    assert it.next() == 3
    assert it.next() == 7
    assert it.hasNext() is True
    assert it.next() == 9
    assert it.hasNext() is True
    assert it.next() == 15
    assert it.hasNext() is True
    assert it.next() == 20
    assert it.hasNext() is False


def test_bst_iterator_full_and_single_and_empty():
    it = BSTIterator(build(BIG))
    out = []
    while it.hasNext():
        out.append(it.next())
    assert out == sorted(inorder(build(BIG)))
    it = BSTIterator(build([1]))
    assert it.hasNext() and it.next() == 1 and not it.hasNext()
    assert BSTIterator(None).hasNext() is False


def test_bst_iterator_uses_small_memory():
    # degenerate right chain: stack should never hold more than a few nodes
    root = cur = TreeNode(0)
    for i in range(1, 5000):
        cur.right = TreeNode(i)
        cur = cur.right
    it = BSTIterator(root)
    for i in range(5000):
        assert it.next() == i
        assert len(getattr(it, "stack", [])) <= 2
    assert not it.hasNext()


@pytest.mark.parametrize("vals,expected", [
    ([1, 3, None, None, 2], [3, 1, None, None, 2]),
    ([3, 1, 4, None, None, 2], [2, 1, 4, None, None, 3]),
    ([2, 3, 1], [2, 1, 3]),
    ([1, 2], [2, 1]),
])
def test_recover_tree_fixed_cases(vals, expected):
    root = build(vals)
    assert recover_tree(root) is None
    assert to_list(root) == expected


@pytest.mark.parametrize("a,b", [(2, 3), (2, 9), (3, 7), (5, 9), (2, 4), (4, 7), (3, 8)])
def test_recover_tree_any_swap(a, b):
    good = [5, 3, 8, 2, 4, 7, 9]
    root = build(good)
    na, nb = find(root, a), find(root, b)
    na.val, nb.val = nb.val, na.val
    assert not check_bst(root)
    recover_tree(root)
    assert to_list(root) == good
