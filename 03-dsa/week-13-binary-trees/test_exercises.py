import pytest
from collections import deque
from exercises import *


def build(vals):
    """Level-order list (None = missing) -> TreeNode root."""
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
    """TreeNode root -> level-order list with trailing Nones trimmed."""
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


def find(root, val):
    if root is None:
        return None
    if root.val == val:
        return root
    return find(root.left, val) or find(root.right, val)


def chain(n, side="left"):
    """Degenerate tree of n nodes (values 1..n)."""
    root = cur = TreeNode(1)
    for i in range(2, n + 1):
        nxt = TreeNode(i)
        setattr(cur, side, nxt)
        cur = nxt
    return root


def test_helpers_roundtrip():
    for v in ([1], [1, 2, 3, None, 4], [1, None, 2, 3]):
        assert to_list(build(v)) == v


@pytest.mark.parametrize("vals,expected", [
    ([], 0), ([1], 1), ([3, 9, 20, None, None, 15, 7], 3),
    ([1, None, 2], 2), ([1, 2, None, 3, None, 4], 4),
])
def test_max_depth(vals, expected):
    assert max_depth(build(vals)) == expected


def test_max_depth_chain():
    assert max_depth(chain(500, "right")) == 500


@pytest.mark.parametrize("vals,expected", [
    ([], []), ([1], [1]), ([1, 2], [1, None, 2]), ([1, None, 2], [1, 2]),
    ([4, 2, 7, 1, 3, 6, 9], [4, 7, 2, 9, 6, 3, 1]),
])
def test_invert_tree(vals, expected):
    assert to_list(invert_tree(build(vals))) == expected


def test_invert_returns_same_root_object():
    root = build([1, 2, 3])
    assert invert_tree(root) is root


@pytest.mark.parametrize("vals,expected", [
    ([], True), ([1], True), ([1, 2, 2, 3, 4, 4, 3], True),
    ([1, 2, 2, None, 3, None, 3], False), ([1, 2], False),
    ([1, 2, 2, 3, None, None, 3], True), ([1, 2, 3], False),
    ([1, 2, 2, None, 3, 3], True),
])
def test_is_symmetric(vals, expected):
    assert is_symmetric(build(vals)) is expected


@pytest.mark.parametrize("vals,expected", [
    ([], []), ([1], [1]), ([1, None, 2, 3], [1, 3, 2]),
    ([4, 2, 6, 1, 3, 5, 7], [1, 2, 3, 4, 5, 6, 7]),
    ([1, 2, None, 3], [3, 2, 1]),
])
def test_inorder_traversal(vals, expected):
    assert inorder_traversal(build(vals)) == expected


def test_inorder_deep_tree_no_recursion_error():
    assert inorder_traversal(chain(5000, "left")) == list(range(5000, 0, -1))


@pytest.mark.parametrize("vals,expected", [
    ([], []), ([1], [[1]]), ([3, 9, 20, None, None, 15, 7], [[3], [9, 20], [15, 7]]),
    ([1, 2, 3, 4, None, None, 5], [[1], [2, 3], [4, 5]]),
    ([1, None, 2, None, 3], [[1], [2], [3]]),
])
def test_level_order(vals, expected):
    assert level_order(build(vals)) == expected


@pytest.mark.parametrize("vals,expected", [
    ([], []), ([1], [1]), ([1, 2, 3, None, 5, None, 4], [1, 3, 4]),
    ([1, None, 3], [1, 3]), ([1, 2], [1, 2]),
    ([1, 2, 3, 4], [1, 3, 4]),
])
def test_right_side_view(vals, expected):
    assert right_side_view(build(vals)) == expected


@pytest.mark.parametrize("vals,expected", [
    ([], 0), ([1], 0), ([1, 2], 1), ([1, 2, 3, 4, 5], 3),
    ([1, 2, None, 3, None, 4], 3),
    # longest path avoids the root: 8-4-2-5-9... built below
    ([1, 2, None, 4, 5, 6, None, None, 7, 8], 5),
])
def test_diameter(vals, expected):
    assert diameter_of_tree(build(vals)) == expected


def test_diameter_chain():
    assert diameter_of_tree(chain(300, "left")) == 299


def test_lca_basic():
    root = build([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    assert lowest_common_ancestor(root, find(root, 5), find(root, 1)) is root
    assert lowest_common_ancestor(root, find(root, 5), find(root, 4)) is find(root, 5)
    assert lowest_common_ancestor(root, find(root, 6), find(root, 4)) is find(root, 5)
    assert lowest_common_ancestor(root, find(root, 7), find(root, 8)) is root
    assert lowest_common_ancestor(root, find(root, 7), find(root, 4)) is find(root, 2)


def test_lca_same_node_and_two_nodes():
    root = build([1, 2])
    assert lowest_common_ancestor(root, root, find(root, 2)) is root
    assert lowest_common_ancestor(root, find(root, 2), find(root, 2)) is find(root, 2)


@pytest.mark.parametrize("pre,ino,expected", [
    ([], [], []), ([1], [1], [1]),
    ([3, 9, 20, 15, 7], [9, 3, 15, 20, 7], [3, 9, 20, None, None, 15, 7]),
    ([1, 2], [2, 1], [1, 2]), ([1, 2], [1, 2], [1, None, 2]),
    ([1, 2, 3], [3, 2, 1], [1, 2, None, 3]),
])
def test_build_tree(pre, ino, expected):
    assert to_list(build_tree(pre, ino)) == expected


def test_build_tree_larger_input():
    n = 500
    pre = list(range(n))
    ino = list(range(n))
    root = build_tree(pre, ino)
    assert inorder_traversal(root) == ino


@pytest.mark.parametrize("vals,expected", [
    ([1], 1), ([-3], -3), ([1, 2, 3], 6), ([-10, 9, 20, None, None, 15, 7], 42),
    ([-1, -2, -3], -1), ([2, -1], 2), ([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 48),
    ([-2, 1], 1),
])
def test_max_path_sum(vals, expected):
    assert max_path_sum(build(vals)) == expected
