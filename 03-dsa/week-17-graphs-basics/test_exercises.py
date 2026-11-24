import random
from collections import deque

from exercises import *


# ---------- helpers ----------
def build_graph(adj):
    """adj[i] = neighbor values (1-indexed values) of node with value i+1. Returns node 1 or None."""
    if not adj:
        return None
    nodes = [Node(i + 1) for i in range(len(adj))]
    for i, nbrs in enumerate(adj):
        nodes[i].neighbors = [nodes[v - 1] for v in nbrs]
    return nodes[0]


def graph_to_adj(start):
    if start is None:
        return []
    seen = {start: None}
    order = [start]
    q = deque([start])
    while q:
        u = q.popleft()
        for v in u.neighbors:
            if v not in seen:
                seen[v] = None
                order.append(v)
                q.append(v)
    order.sort(key=lambda n: n.val)
    return [[v.val for v in n.neighbors] for n in order]


def collect(start):
    seen = {start}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in u.neighbors:
            if v not in seen:
                seen.add(v)
                q.append(v)
    return seen


# ---------- valid_path ----------
def test_valid_path_basic():
    assert valid_path(3, [[0, 1], [1, 2], [2, 0]], 0, 2) is True
    assert valid_path(6, [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]], 0, 5) is False


def test_valid_path_edges():
    assert valid_path(1, [], 0, 0) is True
    assert valid_path(2, [], 0, 1) is False
    assert valid_path(2, [[0, 1]], 1, 0) is True  # undirected
    assert valid_path(4, [[0, 1], [1, 2], [2, 3]], 3, 0) is True
    assert valid_path(3, [[0, 0], [1, 2]], 0, 2) is False  # self loop


def test_valid_path_large_chain():
    n = 50000
    edges = [[i, i + 1] for i in range(n - 1)]
    assert valid_path(n, edges, 0, n - 1) is True
    assert valid_path(n, edges[:-1], 0, n - 1) is False


# ---------- flood_fill ----------
def test_flood_fill_basic():
    img = [[1, 1, 1], [1, 1, 0], [1, 0, 1]]
    assert flood_fill(img, 1, 1, 2) == [[2, 2, 2], [2, 2, 0], [2, 0, 1]]


def test_flood_fill_same_color_no_infinite_loop():
    assert flood_fill([[0, 0, 0], [0, 0, 0]], 0, 0, 0) == [[0, 0, 0], [0, 0, 0]]


def test_flood_fill_not_diagonal():
    img = [[1, 0], [0, 1]]
    assert flood_fill(img, 0, 0, 5) == [[5, 0], [0, 1]]


def test_flood_fill_single_and_all():
    assert flood_fill([[3]], 0, 0, 9) == [[9]]
    assert flood_fill([[1, 1], [1, 1]], 1, 0, 7) == [[7, 7], [7, 7]]


def test_flood_fill_large_no_recursion_error():
    img = [[0] * 200 for _ in range(200)]
    out = flood_fill(img, 0, 0, 1)
    assert all(v == 1 for row in out for v in row)


# ---------- num_islands ----------
def g(rows):
    return [list(r) for r in rows]


def test_num_islands_basic():
    assert num_islands(g(["1100", "1100", "0010", "0001"])) == 3
    assert num_islands(g(["11110", "11010", "11000", "00000"])) == 1


def test_num_islands_edges():
    assert num_islands([]) == 0
    assert num_islands([[]]) == 0
    assert num_islands(g(["0"])) == 0
    assert num_islands(g(["1"])) == 1
    assert num_islands(g(["000", "000"])) == 0
    assert num_islands(g(["101", "010", "101"])) == 5  # diagonals do not connect


def test_num_islands_large_all_land():
    assert num_islands([["1"] * 300 for _ in range(300)]) == 1


def test_num_islands_checkerboard():
    grid = [["1" if (i + j) % 2 == 0 else "0" for j in range(20)] for i in range(20)]
    assert num_islands(grid) == 200


# ---------- max_area_of_island ----------
def test_max_area_basic():
    assert max_area_of_island([[0, 1, 1], [0, 1, 0], [1, 0, 0]]) == 3
    assert max_area_of_island([[0, 0, 0]]) == 0
    assert max_area_of_island([[1]]) == 1


def test_max_area_bigger():
    grid = [
        [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
    ]
    assert max_area_of_island(grid) == 6


def test_max_area_edges():
    assert max_area_of_island([]) == 0
    assert max_area_of_island([[1, 0, 1]]) == 1
    assert max_area_of_island([[1] * 100 for _ in range(100)]) == 10000


# ---------- valid_tree ----------
def test_valid_tree_basic():
    assert valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]) is True
    assert valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]) is False
    assert valid_tree(4, [[0, 1], [2, 3]]) is False


def test_valid_tree_edges():
    assert valid_tree(1, []) is True
    assert valid_tree(2, []) is False
    assert valid_tree(2, [[1, 0]]) is True
    assert valid_tree(3, [[0, 1], [0, 1]]) is False  # duplicate edge
    assert valid_tree(4, [[0, 1], [1, 2], [2, 0]]) is False  # cycle + isolated node
    assert valid_tree(4, [[0, 1], [1, 2], [2, 3]]) is True


def test_valid_tree_big_path():
    n = 20000
    assert valid_tree(n, [[i, i + 1] for i in range(n - 1)]) is True


# ---------- clone_graph ----------
def test_clone_none_and_single():
    assert clone_graph(None) is None
    n = Node(1)
    c = clone_graph(n)
    assert c is not n and c.val == 1 and c.neighbors == []


def test_clone_square():
    adj = [[2, 4], [1, 3], [2, 4], [1, 3]]
    orig = build_graph(adj)
    c = clone_graph(orig)
    assert graph_to_adj(c) == adj
    assert collect(orig).isdisjoint(collect(c))


def test_clone_self_loop_and_pair():
    orig = build_graph([[1, 2], [1]])
    c = clone_graph(orig)
    assert graph_to_adj(c) == [[1, 2], [1]]
    assert c.neighbors[0] is c  # self loop preserved on the clone
    assert collect(orig).isdisjoint(collect(c))


def test_clone_does_not_modify_original():
    adj = [[2, 3], [1, 3], [1, 2]]
    orig = build_graph(adj)
    c = clone_graph(orig)
    assert graph_to_adj(c) == adj
    assert graph_to_adj(orig) == adj


def test_clone_node_count():
    adj = [[2, 3, 4, 5], [1], [1], [1], [1]]
    orig = build_graph(adj)
    c = clone_graph(orig)
    assert len(collect(c)) == 5
    assert graph_to_adj(c) == adj


# ---------- oranges_rotting ----------
def test_oranges_basic():
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert oranges_rotting([[0, 2]]) == 0


def test_oranges_edges():
    assert oranges_rotting([[0]]) == 0
    assert oranges_rotting([[1]]) == -1
    assert oranges_rotting([[2]]) == 0
    assert oranges_rotting([[1, 2]]) == 1
    assert oranges_rotting([[2, 1, 1, 1, 1, 2]]) == 2
    assert oranges_rotting([[2, 0, 1]]) == -1


def test_oranges_does_not_mutate_input_needed():
    grid = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
    oranges_rotting(grid)
    # Mutation is allowed, but the answer must be repeatable on a fresh copy.
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4


# ---------- shortest_path_binary_matrix ----------
def test_spbm_basic():
    assert shortest_path_binary_matrix([[0, 1], [1, 0]]) == 2
    assert shortest_path_binary_matrix([[0, 0, 0], [1, 1, 0], [1, 1, 0]]) == 4
    assert shortest_path_binary_matrix([[1, 0, 0], [1, 1, 0], [1, 1, 0]]) == -1


def test_spbm_edges():
    assert shortest_path_binary_matrix([[0]]) == 1
    assert shortest_path_binary_matrix([[1]]) == -1
    assert shortest_path_binary_matrix([[0, 0], [0, 1]]) == -1  # end blocked
    assert shortest_path_binary_matrix([[0, 1, 1], [1, 1, 1], [1, 1, 0]]) == -1
    n = 30
    assert shortest_path_binary_matrix([[0] * n for _ in range(n)]) == n


def test_spbm_winding():
    grid = [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
    ]
    assert shortest_path_binary_matrix(grid) == 13


# ---------- pacific_atlantic ----------
def brute_pa(h):
    R, C = len(h), len(h[0])

    def flows(r, c):
        seen = {(r, c)}
        stack = [(r, c)]
        pac = atl = False
        while stack:
            x, y = stack.pop()
            if x == 0 or y == 0:
                pac = True
            if x == R - 1 or y == C - 1:
                atl = True
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < R and 0 <= ny < C and (nx, ny) not in seen and h[nx][ny] <= h[x][y]:
                    seen.add((nx, ny))
                    stack.append((nx, ny))
        return pac and atl

    return sorted([r, c] for r in range(R) for c in range(C) if flows(r, c))


def test_pacific_atlantic_example():
    h = [[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]
    assert sorted(pacific_atlantic(h)) == [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]


def test_pacific_atlantic_small():
    assert sorted(pacific_atlantic([[1]])) == [[0, 0]]
    assert sorted(pacific_atlantic([[1, 1], [1, 1]])) == [[0, 0], [0, 1], [1, 0], [1, 1]]
    assert sorted(pacific_atlantic([[1, 2, 3]])) == [[0, 0], [0, 1], [0, 2]]
    assert pacific_atlantic([]) == []


def test_pacific_atlantic_random_vs_brute():
    rnd = random.Random(11)
    for _ in range(40):
        R, C = rnd.randint(1, 6), rnd.randint(1, 6)
        h = [[rnd.randint(0, 4) for _ in range(C)] for _ in range(R)]
        assert sorted(pacific_atlantic(h)) == brute_pa(h)


# ---------- ladder_length ----------
def test_ladder_basic():
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]) == 5
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log"]) == 0


def test_ladder_edges():
    assert ladder_length("a", "c", ["a", "b", "c"]) == 2
    assert ladder_length("hot", "dog", ["hot", "dog"]) == 0
    assert ladder_length("hot", "dot", ["dot"]) == 2
    assert ladder_length("abc", "xyz", []) == 0


def test_ladder_shortest_not_first():
    words = ["hot", "dot", "dog", "lot", "log", "cog", "hog"]
    assert ladder_length("hit", "cog", words) == 4  # hit hot hog cog


def test_ladder_random_vs_bfs_brute():
    rnd = random.Random(2)
    for _ in range(30):
        words = list({"".join(rnd.choice("abc") for _ in range(3)) for _ in range(12)})
        begin = "".join(rnd.choice("abc") for _ in range(3))
        end = rnd.choice(words)
        if begin == end:
            continue

        def adjacent(x, y):
            return sum(a != b for a, b in zip(x, y)) == 1

        dist = {begin: 1}
        q = deque([begin])
        while q:
            u = q.popleft()
            for w in words:
                if w not in dist and adjacent(u, w):
                    dist[w] = dist[u] + 1
                    q.append(w)
        assert ladder_length(begin, end, words) == dist.get(end, 0)
