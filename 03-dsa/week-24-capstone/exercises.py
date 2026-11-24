"""Week 24 capstone: timed mock-interview sets. Replace each `...` with your code.

Run each set under a timer. Talk out loud as if the interviewer were present:
clarify, examples, approach + complexity, code, test, optimise.
"""


import heapq
from collections import defaultdict, deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


# =====================================================================
# MOCK SET A -- "Phone screen warm-up"   45 minutes total
# Budget: 10 min + 15 min + 20 min. Medium-level, arrays/strings/lists.
# =====================================================================

def group_anagrams(strs):
    """[Set A, Q1, 10 min] Group strings that are anagrams of each other.
    Return a list of groups (any order of groups and of words inside).

    ["eat","tea","tan","ate","nat","bat"] -> [["eat","tea","ate"],["tan","nat"],["bat"]]
    [""] -> [[""]]
    Expected: O(n * k) or O(n * k log k) time, k = max word length.
    Hint: hash map keyed by a canonical form (sorted letters or 26-count tuple).
    """
    ...


def length_of_longest_substring(s):
    """[Set A, Q2, 15 min] Length of the longest substring without repeating characters.

    "abcabcbb" -> 3
    "" -> 0
    Expected: O(n) time, O(alphabet) space.
    Hint: sliding window + dict of last-seen index; move left past the duplicate.
    """
    ...


def merge_k_lists(lists):
    """[Set A, Q3, 20 min] Merge k sorted linked lists (heads, some may be None)
    into one sorted list; return its head (None if nothing to merge).

    [1->4->5, 1->3->4, 2->6] -> 1->1->2->3->4->4->5->6
    Expected: O(N log k) time, O(k) extra space.
    Hint: min-heap of (value, list index, node); the index breaks ties so
    ListNodes are never compared.
    """
    ...


# =====================================================================
# MOCK SET B -- "Onsite round: trees and graphs"   50 minutes total
# Budget: 15 min + 15 min + 20 min.
# =====================================================================

def lowest_common_ancestor(root, p, q):
    """[Set B, Q4, 15 min] Binary tree (NOT a BST). p and q are nodes in the tree.
    Return their lowest common ancestor node (a node may be its own ancestor).

    Expected: O(n) time, O(h) space.
    Hint: post-order; if left and right both return non-None, current node is the LCA.
    """
    ...


def num_islands(grid):
    """[Set B, Q5, 15 min] Grid of "1" (land) / "0" (water) strings. Count
    4-directionally connected islands. Do not rely on mutating the input
    being visible to the caller (copy or use a visited set if unsure).

    [["1","1","0"],["0","1","0"],["0","0","1"]] -> 2
    Expected: O(m*n) time.
    Hint: iterative BFS/DFS avoids recursion-depth problems on big grids.
    """
    ...


def can_finish(num_courses, prerequisites):
    """[Set B, Q6, 20 min] Courses 0..num_courses-1; prerequisites[i] = [a, b]
    means take b before a. Return True iff all courses can be finished
    (no cycle).

    (2, [[1,0]]) -> True
    (2, [[1,0],[0,1]]) -> False
    Expected: O(V + E) time.
    Hint: Kahn's algorithm; finished iff you pop all V nodes.
    """
    ...


# =====================================================================
# MOCK SET C -- "Stretch round: harder mixed patterns"   75 minutes total
# Budget: 15 min + 20 min + 15 min + 25 min. Aim for 3 of 4 clean.
# =====================================================================

def top_k_frequent(nums, k):
    """[Set C, Q7, 15 min] Return the k most frequent elements (any order).
    Tests only use inputs where the answer is unique.

    ([1,1,1,2,2,3], 2) -> [1,2]
    Expected: O(n log k) with a heap, or O(n) with bucket sort.
    Hint: Counter + heapq.nlargest, or buckets indexed by frequency.
    """
    ...


def word_break(s, word_dict):
    """[Set C, Q8, 20 min] Can s be segmented into a space-separated sequence
    of words from word_dict (words reusable)?

    ("leetcode", ["leet","code"]) -> True
    ("catsandog", ["cats","dog","sand","and","cat"]) -> False
    Expected: O(n * L) time, L = max word length.
    Hint: dp[i] = prefix s[:i] segmentable; dp[0] = True.
    """
    ...


def generate_parentheses(n):
    """[Set C, Q9, 15 min] All well-formed strings of n pairs of parentheses (any order).

    3 -> ["((()))","(()())","(())()","()(())","()()()"]
    0 -> [""]
    Expected: O(4^n / sqrt(n)) output-bound.
    Hint: backtrack, add "(" if open < n, add ")" if close < open.
    """
    ...


def network_delay_time(times, n, k):
    """[Set C, Q10, 25 min] Directed weighted graph on nodes 1..n; times[i] =
    [u, v, w]. A signal starts at node k. Return the time for ALL nodes to
    receive it, or -1 if some node is unreachable.

    ([[2,1,1],[2,3,1],[3,4,1]], 4, 2) -> 2
    ([[1,2,1]], 2, 2) -> -1
    Expected: O(E log V) time.
    Hint: Dijkstra with a heap; answer = max shortest distance.
    """
    ...
