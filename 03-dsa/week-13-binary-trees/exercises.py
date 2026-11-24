"""Week 13 exercises: binary trees and traversals. Replace each `...` with your code.

Trees use the TreeNode class below. Tests build trees from LeetCode-style
level-order lists, e.g. [1, 2, 3, None, 4].
"""
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def max_depth(root):
    """Return the number of nodes on the longest root-to-leaf path (0 for empty).

    Example: [3, 9, 20, None, None, 15, 7] -> 3
    Expected: O(n) time, O(h) space (h = height).
    Hint: depth(node) = 1 + max(depth(left), depth(right)).
    """
    ...


def invert_tree(root):
    """Mirror the tree (swap left and right at every node) and return the root.

    Example: [4, 2, 7, 1, 3, 6, 9] -> [4, 7, 2, 9, 6, 3, 1]
    Expected: O(n) time, O(h) space.
    Hint: swap children, then recurse (or use a queue).
    """
    ...


def is_symmetric(root):
    """Return True if the tree is a mirror image of itself around its center.

    Example: [1, 2, 2, 3, 4, 4, 3] -> True ; [1, 2, 2, None, 3, None, 3] -> False
    Expected: O(n) time, O(h) space.
    Hint: write a helper mirror(a, b) comparing a.left with b.right and a.right with b.left.
    """
    ...


def inorder_traversal(root):
    """Return the inorder (left, node, right) values as a list, ITERATIVELY.

    Example: [1, None, 2, 3] -> [1, 3, 2]
    Expected: O(n) time, O(h) space. Must not use recursion (deep trees!).
    Hint: stack; go left as far as possible, pop, visit, move to right child.
    """
    ...


def level_order(root):
    """Return values grouped by level, top to bottom, left to right.

    Example: [3, 9, 20, None, None, 15, 7] -> [[3], [9, 20], [15, 7]] ; empty -> []
    Expected: O(n) time, O(w) space (w = max width).
    Hint: BFS with a deque; process len(queue) nodes per iteration.
    """
    ...


def right_side_view(root):
    """Return the values visible when looking at the tree from the right side.

    Example: [1, 2, 3, None, 5, None, 4] -> [1, 3, 4]
    Expected: O(n) time, O(w) space.
    Hint: last node of each BFS level. Note a left-subtree node can be visible.
    """
    ...


def diameter_of_tree(root):
    """Return the length (in EDGES) of the longest path between any two nodes.

    The path may or may not pass through the root.
    Example: [1, 2, 3, 4, 5] -> 3 (path 4-2-1-3 or 5-2-1-3)
    Expected: O(n) time, O(h) space.
    Hint: height(node) returns depth; update a best answer with left_h + right_h.
    """
    ...


def lowest_common_ancestor(root, p, q):
    """Return the lowest node that has both p and q as descendants (a node counts
    as its own descendant). p and q are TreeNode objects that exist in the tree.

    Example: [3, 5, 1, 6, 2, 0, 8], p=5, q=1 -> node 3 ; p=5, q=4(under 5) -> node 5
    Expected: O(n) time, O(h) space.
    Hint: if root is p or q return root; recurse both sides; if both return non-None, root is the LCA.
    """
    ...


def build_tree(preorder, inorder):
    """Construct and return the binary tree from its preorder and inorder traversals
    (all values are unique). Return None for empty input.

    Example: preorder=[3, 9, 20, 15, 7], inorder=[9, 3, 15, 20, 7] -> [3, 9, 20, None, None, 15, 7]
    Expected: O(n) time, O(n) space.
    Hint: preorder[0] is the root; its index in inorder (via a dict) splits left/right sizes.
    """
    ...


def max_path_sum(root):
    """Return the maximum sum over all non-empty paths (any node to any node, going
    only along parent-child links, each node at most once). Values may be negative.

    Example: [-10, 9, 20, None, None, 15, 7] -> 42 (15 + 20 + 7) ; [-3] -> -3
    Expected: O(n) time, O(h) space.
    Hint: gain(node) = node.val + max(0, gain(left), gain(right)) is what a parent can use;
          candidate answer at node = val + max(0, gain(left)) + max(0, gain(right)).
    """
    ...
