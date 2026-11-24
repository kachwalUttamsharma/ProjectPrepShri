"""Week 19 exercises: shortest paths. Replace each `...` with your code.

Ordered roughly easy -> hard. Hints are in the docstrings.
"""

import heapq  # noqa: F401  (available for you)
from collections import deque  # noqa: F401

INF = float("inf")


def dijkstra_distances(n, edges, src):
    """Return a list `dist` of length n with the shortest distance from src to every node.

    `edges` is a list of directed edges (u, v, w) with w >= 0. Nodes are 0..n-1.
    Unreachable nodes get INF. Parallel edges and self loops may appear.

    Example: n=4, edges=[(0,1,4),(0,2,1),(2,1,2),(1,3,1)], src=0 -> [0, 3, 1, 4]

    Hint: min-heap of (dist, node); skip stale entries.
    Expected: O((V + E) log V) time, O(V + E) space.
    """
    ...


def shortest_path_binary_matrix(grid):
    """LeetCode 1091. Grid of 0 (open) / 1 (blocked). Move in 8 directions through open cells
    from (0,0) to (n-1,n-1). Return the number of cells on the shortest path, or -1.

    Example: [[0,1],[1,0]] -> 2;  [[1,0],[0,0]] -> -1;  [[0]] -> 1

    Hint: unweighted -> BFS. Check the start cell first.
    Expected: O(n^2) time and space.
    """
    ...


def network_delay_time(times, n, k):
    """LeetCode 743. `times[i] = [u, v, w]`: a signal from u reaches v in w time (directed).
    Nodes are labelled 1..n. Return the time for all nodes to receive a signal sent from k,
    or -1 if some node is unreachable.

    Example: times=[[2,1,1],[2,3,1],[3,4,1]], n=4, k=2 -> 2

    Hint: Dijkstra, answer is the max finite distance.
    Expected: O(E log V).
    """
    ...


def ladder_length(begin_word, end_word, word_list):
    """LeetCode 127. Transform begin_word to end_word changing one letter at a time; every
    intermediate word must be in word_list. Return the number of words in the shortest
    sequence (including both ends), or 0 if impossible.

    Example: "hit", "cog", ["hot","dot","dog","lot","log","cog"] -> 5

    Hint: implicit graph + BFS. Bucket words by wildcard pattern ("h*t") to find neighbours.
    Expected: O(N * L^2) time.
    """
    ...


def minimum_effort_path(heights):
    """LeetCode 1631. Grid of heights. Move 4-directionally from top-left to bottom-right.
    The effort of a path is the maximum absolute height difference between consecutive cells.
    Return the minimum possible effort.

    Example: [[1,2,2],[3,8,2],[5,3,5]] -> 2;  [[5]] -> 0

    Hint: Dijkstra where cost = max(cost_so_far, edge). (Binary search + BFS also works.)
    Expected: O(RC log(RC)).
    """
    ...


def swim_in_water(grid):
    """LeetCode 778. grid[r][c] is the elevation; at time t you can stand on cells with
    elevation <= t and swim between adjacent cells instantly. Starting at (0,0) at time 0,
    return the least time t to reach (n-1,n-1). Elevations are a permutation of 0..n*n-1.

    Example: [[0,2],[1,3]] -> 3;  [[0]] -> 0

    Hint: same "minimize the max" Dijkstra as above.
    Expected: O(n^2 log n).
    """
    ...


def cheapest_flights_within_k_stops(n, flights, src, dst, k):
    """LeetCode 787. `flights[i] = [from, to, price]` (directed). Return the cheapest price from
    src to dst with at most k stops (k stops = at most k+1 flights), or -1.

    Example: n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], src=0, dst=2, k=1 -> 200; k=0 -> 500

    Hint: Bellman-Ford for k+1 rounds with a copied array, or Dijkstra on (node, stops).
    Expected: O(k * E).
    """
    ...


def path_with_max_probability(n, edges, succ_prob, start, end):
    """LeetCode 1514. Undirected graph; edge i = edges[i] succeeds with probability
    succ_prob[i]. Return the max success probability of a path from start to end (product
    along the path), or 0.0 if there is no path.

    Example: n=3, edges=[[0,1],[1,2],[0,2]], succ_prob=[0.5,0.5,0.2], start=0, end=2 -> 0.25

    Hint: Dijkstra with a max-heap (push negative probabilities). Probabilities <= 1 so
    extending a path never improves it, which is why greedy works.
    Expected: O(E log V).
    """
    ...


def minimum_obstacles_to_remove(grid):
    """LeetCode 2290. Grid of 0 (empty) / 1 (obstacle). Move 4-directionally. Return the
    minimum number of obstacles to remove so there is a path from (0,0) to (m-1,n-1).
    (Start and end are always 0.)

    Example: [[0,1,1],[1,1,0],[1,1,0]] -> 2;  [[0]] -> 0

    Hint: entering a cell costs grid[r][c], i.e. 0 or 1 -> 0-1 BFS with a deque.
    Expected: O(mn).
    """
    ...


def min_cost_valid_path(grid):
    """LeetCode 1368. Each cell holds an arrow: 1=right, 2=left, 3=down, 4=up. Following the
    arrow is free; changing a cell's arrow costs 1 (each cell at most once). Return the
    minimum total cost so a path exists from (0,0) to (m-1,n-1).

    Example: [[1,1,3],[3,2,2],[1,1,4]] -> 0;  [[1,2],[4,3]] -> 1;  [[4]] -> 0

    Hint: 0-1 BFS: from a cell, the edge along its arrow costs 0, the other 3 cost 1.
    Expected: O(mn).
    """
    ...
