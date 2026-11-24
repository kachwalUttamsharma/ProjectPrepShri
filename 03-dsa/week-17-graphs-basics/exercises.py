"""Week 17 exercises: Graph basics (BFS/DFS, grids, adjacency lists).

Replace each `...` with your code. Problems are ordered easy -> hard.
Grids are lists of lists; edges are lists of [u, v] pairs (undirected unless stated).
"""
from collections import defaultdict, deque

class Node:
    """Graph node used by clone_graph (already implemented, do not edit)."""

    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

def valid_path(n, edges, source, destination):
    """LeetCode 1971. Is there a path from source to destination?

    Nodes are 0..n-1, edges are undirected.

    Examples:
        n=3, edges=[[0,1],[1,2],[2,0]], source=0, destination=2 -> True
        n=6, edges=[[0,1],[0,2],[3,5],[5,4],[4,3]], source=0, destination=5 -> False
        n=1, edges=[], source=0, destination=0 -> True

    Expected: O(V + E) time and space.
    Hint: build an adjacency list (defaultdict(list)), BFS/DFS from source with
    a visited set. source == destination is trivially True.
    """
    ...

def flood_fill(image, sr, sc, color):
    """LeetCode 733. Paint-bucket fill.

    Starting at (sr, sc), recolor the 4-directionally connected region that has
    the same original color as image[sr][sc] to `color`. Return the image
    (modifying in place is fine).

    Example:
        image=[[1,1,1],[1,1,0],[1,0,1]], sr=1, sc=1, color=2
        -> [[2,2,2],[2,2,0],[2,0,1]]

    Expected: O(R * C) time.
    Hint: if the original color already equals `color`, return immediately
    (otherwise you loop forever / recurse infinitely). Painting doubles as the
    visited marker.
    """
    ...

def num_islands(grid):
    """LeetCode 200. Count islands in a grid of "1" (land) and "0" (water) strings.

    An island is a maximal group of land cells connected 4-directionally.

    Example:
        [["1","1","0","0"],
         ["1","1","0","0"],
         ["0","0","1","0"],
         ["0","0","0","1"]] -> 3

    Expected: O(R * C) time. Empty grid -> 0.
    Hint: scan cells; each unvisited land cell starts a new island, then
    flood it (DFS/BFS) so it is counted once. Prefer an iterative stack/queue
    to avoid recursion-limit trouble on a 300x300 all-land grid.
    """
    ...

def max_area_of_island(grid):
    """LeetCode 695. Largest island area in a grid of 1 (land) / 0 (water) ints.

    Example:
        [[0,1,1],[0,1,0],[1,0,0]] -> 3
        [[0,0,0]] -> 0

    Expected: O(R * C) time.
    Hint: same traversal as num_islands, but return/count the size of each flood.
    """
    ...

def valid_tree(n, edges):
    """LeetCode 261. Do the undirected edges on nodes 0..n-1 form a valid tree?

    A tree is connected and has no cycles.

    Examples:
        n=5, edges=[[0,1],[0,2],[0,3],[1,4]] -> True
        n=5, edges=[[0,1],[1,2],[2,3],[1,3],[1,4]] -> False  (cycle)
        n=4, edges=[[0,1],[2,3]] -> False  (disconnected)
        n=1, edges=[] -> True

    Expected: O(V + E).
    Hint: a graph on n nodes is a tree iff it has exactly n - 1 edges AND is
    connected. Check the edge count first (cheap), then traverse from node 0
    and confirm you reach n nodes.
    """
    ...

def clone_graph(node):
    """LeetCode 133. Deep-copy a connected undirected graph.

    `node` is a Node (with .val and .neighbors) or None. Return the clone of
    the same node. The copy must share NO Node objects with the original.

    Example:
        1 -- 2
        |    |      adjacency [[2,4],[1,3],[2,4],[1,3]] -> an identical, independent graph
        4 -- 3

    Expected: O(V + E) time and space.
    Hint: dict old_node -> new_node doubles as the visited set. Create the
    clone BEFORE exploring neighbors so cycles terminate.
    """
    ...

def oranges_rotting(grid):
    """LeetCode 994. Rotting oranges (multi-source BFS).

    0 = empty, 1 = fresh orange, 2 = rotten orange. Each minute every fresh
    orange 4-adjacent to a rotten one becomes rotten. Return the minutes until
    no fresh orange remains, or -1 if impossible. No fresh oranges -> 0.

    Examples:
        [[2,1,1],[1,1,0],[0,1,1]] -> 4
        [[2,1,1],[0,1,1],[1,0,1]] -> -1
        [[0,2]] -> 0

    Expected: O(R * C).
    Hint: put ALL rotten oranges in the queue at once, process BFS level by
    level (one level = one minute), and count remaining fresh oranges.
    """
    ...

def shortest_path_binary_matrix(grid):
    """LeetCode 1091. Shortest clear path in a binary matrix (8 directions).

    grid[i][j] is 0 (open) or 1 (blocked). Return the number of cells on the
    shortest path from (0,0) to (n-1,n-1) moving in 8 directions through open
    cells, or -1 if none exists.

    Examples:
        [[0,1],[1,0]] -> 2
        [[0,0,0],[1,1,0],[1,1,0]] -> 4
        [[1,0,0],[1,1,0],[1,1,0]] -> -1
        [[0]] -> 1

    Expected: O(n^2).
    Hint: BFS gives shortest paths in unweighted graphs. Mark cells visited
    when you ENQUEUE them. Check the start cell is open.
    """
    ...

def pacific_atlantic(heights):
    """LeetCode 417. Pacific Atlantic water flow.

    heights[r][c] is a cell's height. Water flows from a cell to a 4-adjacent
    cell with height <= its own. The Pacific touches the top and left edges,
    the Atlantic touches the bottom and right edges. Return all [r, c] from
    which water can reach BOTH oceans (any order).

    Example:
        [[1,2,2,3,5],
         [3,2,3,4,4],
         [2,4,5,3,1],
         [6,7,1,4,5],
         [5,1,1,2,4]]
        -> [[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]

    Expected: O(R * C).
    Hint: do NOT simulate flow from every cell. Run a reverse search from each
    ocean's border cells, moving to neighbors with height >= current, and
    intersect the two reachable sets.
    """
    ...

def ladder_length(begin_word, end_word, word_list):
    """LeetCode 127. Word ladder.

    Transform begin_word into end_word changing one letter at a time; every
    intermediate word must be in word_list (begin_word need not be). Return the
    number of WORDS in the shortest sequence (including both ends), or 0 if
    impossible.

    Examples:
        "hit", "cog", ["hot","dot","dog","lot","log","cog"] -> 5
        "hit", "cog", ["hot","dot","dog","lot","log"] -> 0   (cog not in list)
        "a", "c", ["a","b","c"] -> 2

    Expected: O(N * L^2) with wildcard buckets, N words of length L.
    Hint: model words as graph nodes. To find neighbors fast, bucket words by
    patterns like "h*t". BFS from begin_word. Bidirectional BFS is a nice follow-up.
    """
    ...
