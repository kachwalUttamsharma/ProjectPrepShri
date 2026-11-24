"""Week 14 exercises: binary search trees. Replace each `...` with your code.

BST rule: for every node, ALL values in the left subtree are < node.val and ALL
values in the right subtree are > node.val (no duplicates unless stated).
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def search_bst(root, val):
    """Return the node whose value equals val, or None if absent.

    Example: [4, 2, 7, 1, 3], val=2 -> subtree rooted at 2 ; val=5 -> None
    Expected: O(h) time, O(1) space (iterative).
    Hint: compare and go left or right; never visit both sides.
    """
    ...


def closest_value(root, target):
    """Return the value in the BST closest to target (a float). On a tie return the smaller value.

    Example: [4, 2, 5, 1, 3], target=3.714286 -> 4 ; target=2.5 -> 2
    Expected: O(h) time, O(1) space.
    Hint: walk down like a search, remembering the best seen so far.
    """
    ...


def insert_into_bst(root, val):
    """Insert val (not already present) as a new leaf and return the root.
    An empty tree returns a new single node.

    Example: [4, 2, 7, 1, 3], val=5 -> [4, 2, 7, 1, 3, 5]
    Expected: O(h) time.
    Hint: descend until you find a None slot; attach there.
    """
    ...


def lca_bst(root, p, q):
    """Return the lowest common ancestor of nodes p and q (TreeNode objects in the tree).
    A node is a descendant of itself.

    Example: [6, 2, 8, 0, 4, 7, 9], p=2, q=8 -> 6 ; p=2, q=4 -> 2
    Expected: O(h) time, O(1) space.
    Hint: the BST ordering lets you skip the full search: the LCA is the first node
          whose value lies between p.val and q.val (inclusive).
    """
    ...


def kth_smallest(root, k):
    """Return the k-th smallest value (1-indexed). 1 <= k <= number of nodes.

    Example: [5, 3, 6, 2, 4, None, None, 1], k=3 -> 3
    Expected: O(h + k) time, O(h) space; stop early.
    Hint: inorder traversal of a BST is sorted. Iterative with a stack lets you stop at k.
    """
    ...


def is_valid_bst(root):
    """Return True if the tree is a valid BST (strictly: duplicates are invalid).

    Example: [2, 1, 3] -> True ; [5, 1, 4, None, None, 3, 6] -> False
    Expected: O(n) time, O(h) space.
    Hint: checking only parent vs child is WRONG. Pass (low, high) bounds down,
          or verify inorder is strictly increasing.
    """
    ...


def sorted_array_to_bst(nums):
    """Build a height-balanced BST from a strictly increasing list and return its root
    (None for an empty list). Balanced: subtree heights differ by at most 1 at every node.
    Any valid answer is accepted.

    Example: [-10, -3, 0, 5, 9] -> e.g. [0, -3, 9, -10, None, 5]
    Expected: O(n) time, O(log n) recursion depth.
    Hint: the middle element is the root; recurse on each half (use indices, not slices, to stay O(n)).
    """
    ...


def delete_node(root, key):
    """Delete the node with value key (if present) and return the new root.
    The result must still be a valid BST. Absent key -> tree unchanged.

    Example: [5, 3, 6, 2, 4, None, 7], key=3 -> [5, 4, 6, 2, None, None, 7] (or with 2 promoted)
    Expected: O(h) time.
    Hint: 0 children -> return None; 1 child -> return that child; 2 children -> copy the
          inorder successor (min of right subtree) into the node, then delete it from the right.
    """
    ...


class BSTIterator:
    """Iterator over a BST in ascending order.

    BSTIterator(root); next() returns the next smallest value; hasNext() says if one remains.
    Example: BSTIterator([7, 3, 15, None, None, 9, 20]) yields 3, 7, 9, 15, 20.
    Expected: next() and hasNext() amortized O(1) time, O(h) memory (NOT O(n)).
    Hint: keep a stack holding the leftmost path; after popping, push the leftmost path of the right child.
    """

    def __init__(self, root):
        ...

    def _push_left(self, node):
        ...

    def next(self):
        ...

    def hasNext(self):
        ...


def recover_tree(root):
    """Exactly two nodes of a valid BST had their values swapped by mistake. Fix the tree
    IN PLACE by swapping the two values back. Return None.

    Example: [1, 3, None, None, 2] -> [3, 1, None, None, 2]
    Expected: O(n) time, O(h) space (O(1) with Morris traversal is the follow-up).
    Hint: inorder should be increasing; find the 'descents' (prev.val > cur.val). First descent
          gives `first = prev`, last descent gives `second = cur`. Adjacent swap = one descent.
    """
    ...
