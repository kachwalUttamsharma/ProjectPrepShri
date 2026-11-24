import random

from exercises import *


# ---------- UnionFind ----------
def test_uf_basic():
    uf = UnionFind(5)
    assert uf.count() == 5
    assert uf.union(0, 1) is True
    assert uf.union(1, 0) is False
    assert uf.connected(0, 1) is True
    assert uf.connected(0, 2) is False
    assert uf.count() == 4
    assert uf.size(0) == 2
    assert uf.size(4) == 1


def test_uf_transitive_and_self():
    uf = UnionFind(6)
    uf.union(0, 1)
    uf.union(2, 3)
    uf.union(1, 2)
    assert uf.connected(0, 3)
    assert uf.size(3) == 4
    assert uf.union(2, 2) is False
    assert uf.count() == 3
    assert uf.find(0) == uf.find(3)
    assert uf.find(4) != uf.find(5)


def test_uf_single_element_and_find_identity():
    uf = UnionFind(1)
    assert uf.find(0) == 0
    assert uf.count() == 1
    assert uf.connected(0, 0) is True


def test_uf_long_chain_no_recursion_error():
    n = 100000
    uf = UnionFind(n)
    for i in range(n - 1):
        assert uf.union(i, i + 1) is True
    assert uf.count() == 1
    assert uf.size(0) == n
    assert uf.connected(0, n - 1)
    assert uf.find(n - 1) == uf.find(0)


def test_uf_random_vs_brute():
    rnd = random.Random(4)
    n = 30
    uf = UnionFind(n)
    comp = list(range(n))
    for _ in range(80):
        a, b = rnd.randrange(n), rnd.randrange(n)
        merged = comp[a] != comp[b]
        assert uf.union(a, b) == merged
        if merged:
            old = comp[b]
            comp = [comp[a] if c == old else c for c in comp]
        x, y = rnd.randrange(n), rnd.randrange(n)
        assert uf.connected(x, y) == (comp[x] == comp[y])
        assert uf.count() == len(set(comp))
        assert uf.size(x) == comp.count(comp[x])


# ---------- find_circle_num ----------
def test_provinces():
    assert find_circle_num([[1, 1, 0], [1, 1, 0], [0, 0, 1]]) == 2
    assert find_circle_num([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == 3
    assert find_circle_num([]) == 0
    assert find_circle_num([[1]]) == 1
    assert find_circle_num([[1, 1, 1], [1, 1, 1], [1, 1, 1]]) == 1


def test_provinces_indirect():
    m = [[1, 1, 0, 0], [1, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 1]]
    assert find_circle_num(m) == 2


# ---------- count_components ----------
def test_components():
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1
    assert count_components(3, []) == 3
    assert count_components(0, []) == 0
    assert count_components(1, []) == 1


def test_components_duplicates_and_loops():
    assert count_components(4, [[0, 1], [1, 0], [2, 2]]) == 3
    assert count_components(4, [[0, 1], [1, 2], [2, 0]]) == 2


def test_components_large():
    n = 50000
    assert count_components(n, [[i, i + 1] for i in range(0, n - 1, 2)]) == n // 2


# ---------- can_finish ----------
def test_can_finish():
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(3, []) is True
    assert can_finish(1, [[0, 0]]) is False
    assert can_finish(0, []) is True


def test_can_finish_cycle_inside_bigger_graph():
    assert can_finish(5, [[1, 0], [2, 1], [3, 2], [1, 3], [4, 0]]) is False
    assert can_finish(5, [[1, 0], [2, 1], [3, 2], [4, 3]]) is True
    assert can_finish(4, [[1, 0], [2, 0], [3, 1], [3, 2]]) is True  # diamond
    assert can_finish(3, [[1, 0], [1, 0]]) is True  # duplicate prerequisite


def test_can_finish_long_chain():
    n = 50000
    assert can_finish(n, [[i + 1, i] for i in range(n - 1)]) is True
    assert can_finish(n, [[i + 1, i] for i in range(n - 1)] + [[0, n - 1]]) is False


# ---------- find_order ----------
def valid_order(n, prereqs, order):
    if sorted(order) != list(range(n)):
        return False
    pos = {c: i for i, c in enumerate(order)}
    return all(pos[b] < pos[a] for a, b in prereqs)


def test_find_order_simple():
    assert find_order(2, [[1, 0]]) == [0, 1]
    assert find_order(1, []) == [0]


def test_find_order_diamond():
    pre = [[1, 0], [2, 0], [3, 1], [3, 2]]
    assert valid_order(4, pre, find_order(4, pre))


def test_find_order_cycle():
    assert find_order(2, [[0, 1], [1, 0]]) == []
    assert find_order(3, [[0, 1], [1, 2], [2, 1]]) == []
    assert find_order(1, [[0, 0]]) == []


def test_find_order_no_prereqs_returns_all():
    out = find_order(4, [])
    assert sorted(out) == [0, 1, 2, 3]
    assert find_order(0, []) == []


def test_find_order_random_dag():
    rnd = random.Random(8)
    for _ in range(30):
        n = rnd.randint(2, 15)
        perm = list(range(n))
        rnd.shuffle(perm)
        pre = []
        for _ in range(rnd.randint(0, 25)):
            i, j = sorted(rnd.sample(range(n), 2))
            pre.append([perm[j], perm[i]])  # perm[i] must come first
        assert valid_order(n, pre, find_order(n, pre))


# ---------- minimum_semesters ----------
def test_min_semesters():
    assert minimum_semesters(3, [[1, 3], [2, 3]]) == 2
    assert minimum_semesters(3, [[1, 2], [2, 3], [3, 1]]) == -1
    assert minimum_semesters(4, []) == 1


def test_min_semesters_chain_and_dag():
    assert minimum_semesters(4, [[1, 2], [2, 3], [3, 4]]) == 4
    assert minimum_semesters(5, [[1, 2], [1, 3], [2, 4], [3, 4], [4, 5]]) == 4
    assert minimum_semesters(1, []) == 1
    assert minimum_semesters(2, [[2, 1]]) == 2


def test_min_semesters_partial_cycle():
    assert minimum_semesters(4, [[1, 2], [3, 4], [4, 3]]) == -1
    assert minimum_semesters(2, [[1, 1]]) == -1


# ---------- find_redundant_connection ----------
def test_redundant_connection():
    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3]
    assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4]


def test_redundant_connection_edges():
    assert find_redundant_connection([[1, 2], [1, 2]]) == [1, 2]
    assert find_redundant_connection([[1, 2], [2, 3], [3, 1]]) == [3, 1]
    assert find_redundant_connection([[1, 4], [3, 4], [1, 3], [1, 2], [4, 5]]) == [1, 3]
    n = 5000
    edges = [[i, i + 1] for i in range(1, n)] + [[1, n]]
    assert find_redundant_connection(edges) == [1, n]


# ---------- find_min_height_trees ----------
def test_mht_examples():
    assert sorted(find_min_height_trees(4, [[1, 0], [1, 2], [1, 3]])) == [1]
    assert sorted(find_min_height_trees(6, [[3, 0], [3, 1], [3, 2], [3, 4], [5, 4]])) == [3, 4]


def test_mht_small():
    assert find_min_height_trees(1, []) == [0]
    assert sorted(find_min_height_trees(2, [[0, 1]])) == [0, 1]
    assert sorted(find_min_height_trees(3, [[0, 1], [1, 2]])) == [1]


def test_mht_path_and_star():
    n = 7
    assert sorted(find_min_height_trees(n, [[i, i + 1] for i in range(n - 1)])) == [3]
    n = 8
    assert sorted(find_min_height_trees(n, [[i, i + 1] for i in range(n - 1)])) == [3, 4]
    assert sorted(find_min_height_trees(6, [[0, i] for i in range(1, 6)])) == [0]


def test_mht_random_vs_brute():
    rnd = random.Random(6)
    for _ in range(30):
        n = rnd.randint(1, 12)
        edges = [[i, rnd.randrange(i)] for i in range(1, n)]
        adj = {i: [] for i in range(n)}
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u)

        def height(root):
            seen = {root}
            level = [root]
            h = 0
            while level:
                nxt = [v for u in level for v in adj[u] if v not in seen]
                seen.update(nxt)
                if nxt:
                    h += 1
                level = nxt
            return h

        hs = [height(r) for r in range(n)]
        best = [r for r in range(n) if hs[r] == min(hs)]
        assert sorted(find_min_height_trees(n, edges)) == best


def test_mht_large_path():
    n = 20001
    assert find_min_height_trees(n, [[i, i + 1] for i in range(n - 1)]) == [10000]


# ---------- accounts_merge ----------
def norm(accounts):
    return sorted([a[0]] + sorted(a[1:]) for a in accounts)


def test_accounts_merge_basic():
    accounts = [["John", "a@m", "b@m"], ["John", "c@m"], ["John", "a@m", "d@m"], ["Mary", "m@m"]]
    assert norm(accounts_merge(accounts)) == norm(
        [["John", "a@m", "b@m", "d@m"], ["John", "c@m"], ["Mary", "m@m"]])


def test_accounts_merge_chain_transitive():
    accounts = [["A", "1", "2"], ["A", "3", "4"], ["A", "2", "3"], ["A", "5"]]
    assert norm(accounts_merge(accounts)) == [["A", "1", "2", "3", "4"], ["A", "5"]]


def test_accounts_merge_same_name_different_people():
    accounts = [["Bob", "x@m"], ["Bob", "y@m"]]
    assert norm(accounts_merge(accounts)) == [["Bob", "x@m"], ["Bob", "y@m"]]


def test_accounts_merge_duplicates_and_empty():
    assert accounts_merge([]) == []
    assert accounts_merge([["Z", "a", "a", "b"]]) == [["Z", "a", "b"]]
    accounts = [["Q", "e1", "e2"], ["Q", "e2", "e1"]]
    assert accounts_merge(accounts) == [["Q", "e1", "e2"]]


def test_accounts_merge_order_independent_late_bridge():
    accounts = [["A", "1"], ["A", "2"], ["A", "3"], ["A", "1", "2", "3"]]
    assert norm(accounts_merge(accounts)) == [["A", "1", "2", "3"]]


# ---------- alien_order ----------
def check_alien(words, out):
    letters = {c for w in words for c in w}
    if len(out) != len(letters) or set(out) != letters:
        return False
    pos = {c: i for i, c in enumerate(out)}
    for w1, w2 in zip(words, words[1:]):
        for a, b in zip(w1, w2):
            if a != b:
                if pos[a] > pos[b]:
                    return False
                break
    return True


def test_alien_examples():
    w = ["wrt", "wrf", "er", "ett", "rftt"]
    assert check_alien(w, alien_order(w))
    assert alien_order(["z", "x"]) == "zx"
    assert alien_order(["a"]) == "a"


def test_alien_invalid():
    assert alien_order(["z", "x", "z"]) == ""
    assert alien_order(["abc", "ab"]) == ""
    assert alien_order(["ba", "ab", "ba"]) == ""
    assert alien_order(["a", "b", "a"]) == ""


def test_alien_isolated_letters_included():
    w = ["abc", "abd", "xyz"]
    out = alien_order(w)
    assert check_alien(w, out)
    assert set(out) == set("abcdxyz")


def test_alien_prefix_ok_and_empty():
    w = ["ab", "abc"]
    assert check_alien(w, alien_order(w))
    assert alien_order([]) == ""
    w = ["z", "z"]
    assert alien_order(w) == "z"


def test_alien_long_chain():
    w = ["ab", "bc", "cd", "de", "ef"]
    out = alien_order(w)
    assert check_alien(w, out)
    assert out.index("a") < out.index("b") < out.index("c") < out.index("d") < out.index("e")
    assert set(out) == set("abcdef")


def test_alien_random_valid():
    rnd = random.Random(9)
    for _ in range(30):
        alphabet = list("abcdef")
        rnd.shuffle(alphabet)
        rank = {c: i for i, c in enumerate(alphabet)}
        words = sorted({"".join(rnd.choice(alphabet) for _ in range(rnd.randint(1, 4))) for _ in range(8)},
                       key=lambda w: [rank[c] for c in w])
        assert check_alien(words, alien_order(words))
