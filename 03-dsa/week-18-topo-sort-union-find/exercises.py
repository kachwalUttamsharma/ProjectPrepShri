"""Week 18 exercises: Topological sort and Union-Find (disjoint set union).

Replace each `...` with your code. Problems are ordered easy -> hard.
"""
from collections import defaultdict, deque

class UnionFind:
    """Disjoint Set Union with path compression and union by size.

    UnionFind(n)         n elements 0..n-1, each in its own set.
    find(x) -> int       representative (root) of x's set.
    union(a, b) -> bool  merge the sets; True if they were different, False if
                         a and b were already connected.
    connected(a, b) -> bool
    count() -> int       current number of disjoint sets.
    size(x) -> int       size of the set containing x.

    Example:
        uf = UnionFind(5)
        uf.union(0, 1) -> True; uf.union(1, 0) -> False
        uf.connected(0, 1) -> True; uf.count() -> 4; uf.size(0) -> 2

    Expected: near O(1) amortized (inverse Ackermann) per operation.
    Hint: parent[] and size[] arrays. Make find ITERATIVE (path halving:
    parent[x] = parent[parent[x]]) so long chains cannot hit the recursion limit.
    Attach the smaller root under the larger one.
    """

    def __init__(self, n):
        """Create n singleton sets."""
        ...

    def find(self, x):
        """Return the root of x."""
        ...

    def union(self, a, b):
        """Merge the sets of a and b. Return True if a merge happened."""
        ...

    def connected(self, a, b):
        """Return True if a and b are in the same set."""
        ...

    def count(self):
        """Return the number of disjoint sets."""
        ...

    def size(self, x):
        """Return the size of x's set."""
        ...

def find_circle_num(is_connected):
    """LeetCode 547. Number of provinces.

    is_connected is an n x n matrix; is_connected[i][j] == 1 means cities i and
    j are directly connected (symmetric, diagonal is 1). A province is a group
    of directly or indirectly connected cities. Return the number of provinces.

    Examples:
        [[1,1,0],[1,1,0],[0,0,1]] -> 2
        [[1,0,0],[0,1,0],[0,0,1]] -> 3
        [] -> 0

    Expected: O(n^2 * alpha(n)) time (reading the matrix dominates).
    Hint: UnionFind, count() at the end. Or DFS counting component starts.
    """
    ...

def count_components(n, edges):
    """LeetCode 323. Number of connected components in an undirected graph.

    Nodes are 0..n-1. Duplicate edges and self loops may appear.

    Examples:
        n=5, edges=[[0,1],[1,2],[3,4]] -> 2
        n=5, edges=[[0,1],[1,2],[2,3],[3,4]] -> 1
        n=3, edges=[] -> 3
        n=0, edges=[] -> 0

    Expected: O(n + E * alpha(n)).
    Hint: start with n components and subtract 1 for every union that merges.
    """
    ...

def can_finish(num_courses, prerequisites):
    """LeetCode 207. Can all courses be finished?

    Courses are 0..num_courses-1. prerequisites[i] = [a, b] means you must take
    b BEFORE a. Return True if some order completes every course, i.e. the
    directed graph has no cycle.

    Examples:
        2, [[1,0]] -> True
        2, [[1,0],[0,1]] -> False
        3, [] -> True
        1, [[0,0]] -> False  (self dependency)

    Expected: O(V + E).
    Hint: Kahn's algorithm. Compute in-degrees, queue the zero in-degree
    nodes, pop and decrement neighbors. If you processed fewer than V nodes,
    a cycle exists.
    """
    ...

def find_order(num_courses, prerequisites):
    """LeetCode 210. Return a valid course order, or [] if impossible.

    Same input as can_finish. Any valid order is accepted: for every
    [a, b], b must appear before a, and all courses appear exactly once.

    Examples:
        2, [[1,0]] -> [0, 1]
        4, [[1,0],[2,0],[3,1],[3,2]] -> [0,1,2,3] or [0,2,1,3]
        2, [[0,1],[1,0]] -> []

    Expected: O(V + E).
    Hint: Kahn's algorithm, recording the pop order. Alternative: DFS with
    3 states (unvisited / in progress / done) and reverse post-order; reaching
    an "in progress" node means a cycle.
    """
    ...

def minimum_semesters(n, relations):
    """LeetCode 1136. Parallel courses.

    Courses are labeled 1..n. relations[i] = [prev, next]: prev must be taken
    before next. In one semester you can take any number of courses whose
    prerequisites were all completed in EARLIER semesters. Return the minimum
    number of semesters to finish everything, or -1 if there is a cycle.

    Examples:
        n=3, relations=[[1,3],[2,3]] -> 2
        n=3, relations=[[1,2],[2,3],[3,1]] -> -1
        n=4, relations=[] -> 1

    Expected: O(V + E).
    Hint: Kahn's algorithm processed LEVEL BY LEVEL; the number of levels is
    the answer (= length of the longest prerequisite chain).
    """
    ...

def find_redundant_connection(edges):
    """LeetCode 684. Redundant connection.

    edges is a list of n edges [u, v] (nodes labeled 1..n) that form a tree
    plus ONE extra edge. Return the edge that can be removed so the result is
    a tree. If several answers exist, return the one that occurs LAST in the
    input.

    Examples:
        [[1,2],[1,3],[2,3]] -> [2,3]
        [[1,2],[2,3],[3,4],[1,4],[1,5]] -> [1,4]

    Expected: O(n * alpha(n)).
    Hint: process edges in order with UnionFind; the first edge whose
    endpoints are already connected closes the cycle.
    """
    ...

def find_min_height_trees(n, edges):
    """LeetCode 310. Minimum height trees.

    The undirected edges form a tree on nodes 0..n-1. Any node can be the root;
    return all roots that give the minimum possible tree height (any order).
    There are always 1 or 2 such roots.

    Examples:
        n=4, edges=[[1,0],[1,2],[1,3]] -> [1]
        n=6, edges=[[3,0],[3,1],[3,2],[3,4],[5,4]] -> [3, 4]
        n=1, edges=[] -> [0]
        n=2, edges=[[0,1]] -> [0, 1]

    Expected: O(n).
    Hint: topological-sort style "leaf peeling": repeatedly remove all current
    leaves (degree 1) until at most 2 nodes remain; those are the centers of
    the tree.
    """
    ...

def accounts_merge(accounts):
    """LeetCode 721. Accounts merge.

    accounts[i] = [name, email1, email2, ...]. Two accounts belong to the same
    person if they share at least one email (names alone prove nothing: two
    different people may share a name). Return merged accounts as
    [name, sorted unique emails...] in any order.

    Example:
        [["John","a@m","b@m"],["John","c@m"],["John","a@m","d@m"],["Mary","m@m"]]
        -> [["John","a@m","b@m","d@m"],["John","c@m"],["Mary","m@m"]]

    Expected: O(E log E) where E is the total number of emails.
    Hint: union ACCOUNT indices through the first account that owned each
    email (dict email -> account index), then group emails by root.
    """
    ...

def alien_order(words):
    """LeetCode 269. Alien dictionary.

    `words` is sorted lexicographically by the rules of an unknown alphabet.
    Return a string of ALL letters appearing in words, ordered consistently
    with that alphabet (any valid order is accepted). Return "" if the input is
    inconsistent: a cycle in the constraints, or a longer word that precedes
    its own prefix (e.g. ["abc", "ab"]).

    Examples:
        ["wrt","wrf","er","ett","rftt"] -> "wertf" (any valid order)
        ["z","x"] -> "zx"
        ["z","x","z"] -> ""
        ["abc","ab"] -> ""
        ["a"] -> "a"

    Expected: O(total characters + alphabet constraints).
    Hint: compare each ADJACENT pair of words; the first differing characters
    give one edge c1 -> c2. Add every letter as a node first (letters that
    appear in no edge still belong in the output). Then Kahn's algorithm; if
    the result is shorter than the number of letters there is a cycle.
    """
    ...
