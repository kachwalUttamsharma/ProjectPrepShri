import random
from collections import Counter

from exercises import *


# ---------- helpers ----------
def build_list(vals):
    dummy = tail = ListNode()
    for v in vals:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def list_to_py(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def build_tree(vals):
    """Level-order list with None for gaps. Returns (root, {val: node})."""
    if not vals or vals[0] is None:
        return None, {}
    nodes = {}
    root = TreeNode(vals[0])
    nodes[vals[0]] = root
    queue = [root]
    i = 1
    while queue and i < len(vals):
        node = queue.pop(0)
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i])
            nodes[vals[i]] = node.left
            queue.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i])
            nodes[vals[i]] = node.right
            queue.append(node.right)
        i += 1
    return root, nodes


def norm_groups(groups):
    return sorted(sorted(g) for g in groups)


# ---------- Set A ----------
def test_group_anagrams():
    got = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    assert norm_groups(got) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    assert norm_groups(group_anagrams([""])) == [[""]]
    assert norm_groups(group_anagrams(["a"])) == [["a"]]
    assert group_anagrams([]) == []
    assert norm_groups(group_anagrams(["ab", "ba", "ab"])) == [["ab", "ab", "ba"]]
    assert norm_groups(group_anagrams(["abc", "abd"])) == [["abc"], ["abd"]]
    assert norm_groups(group_anagrams(["", "", "a"])) == [["", ""], ["a"]]


def test_longest_substring():
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring("a") == 1
    assert length_of_longest_substring("abba") == 2
    assert length_of_longest_substring("tmmzuxt") == 5
    assert length_of_longest_substring("dvdf") == 3
    assert length_of_longest_substring("abcdefg") == 7
    assert length_of_longest_substring("a b a") == 3


def test_longest_substring_vs_bruteforce():
    rng = random.Random(2)
    for _ in range(80):
        s = "".join(rng.choice("abcd") for _ in range(rng.randint(0, 12)))
        best = 0
        for i in range(len(s)):
            for j in range(i, len(s) + 1):
                if len(set(s[i:j])) == j - i:
                    best = max(best, j - i)
        assert length_of_longest_substring(s) == best


def test_merge_k_lists():
    lists = [build_list([1, 4, 5]), build_list([1, 3, 4]), build_list([2, 6])]
    assert list_to_py(merge_k_lists(lists)) == [1, 1, 2, 3, 4, 4, 5, 6]
    assert merge_k_lists([]) is None
    assert merge_k_lists([None]) is None
    assert merge_k_lists([None, None]) is None
    assert list_to_py(merge_k_lists([None, build_list([1])])) == [1]
    assert list_to_py(merge_k_lists([build_list([2]), build_list([1])])) == [1, 2]
    assert list_to_py(merge_k_lists([build_list([-3, -1]), build_list([-2, 5])])) == [-3, -2, -1, 5]


def test_merge_k_lists_many_duplicates_no_node_compare():
    # equal values must not trigger ListNode comparison (TypeError)
    lists = [build_list([1, 1, 1]) for _ in range(5)]
    assert list_to_py(merge_k_lists(lists)) == [1] * 15


def test_merge_k_lists_random():
    rng = random.Random(4)
    for _ in range(30):
        arrs = [sorted(rng.randint(-5, 5) for _ in range(rng.randint(0, 5))) for _ in range(rng.randint(0, 6))]
        res = merge_k_lists([build_list(a) for a in arrs])
        assert list_to_py(res) == sorted(x for a in arrs for x in a)


# ---------- Set B ----------
def test_lca_classic():
    root, n = build_tree([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4])
    assert lowest_common_ancestor(root, n[5], n[1]) is n[3]
    assert lowest_common_ancestor(root, n[5], n[4]) is n[5]
    assert lowest_common_ancestor(root, n[6], n[4]) is n[5]
    assert lowest_common_ancestor(root, n[7], n[4]) is n[2]
    assert lowest_common_ancestor(root, n[0], n[8]) is n[1]
    assert lowest_common_ancestor(root, n[3], n[8]) is n[3]


def test_lca_small():
    root, n = build_tree([1, 2])
    assert lowest_common_ancestor(root, n[1], n[2]) is n[1]
    assert lowest_common_ancestor(root, n[2], n[2]) is n[2]
    root, n = build_tree([1])
    assert lowest_common_ancestor(root, n[1], n[1]) is n[1]


def test_lca_not_a_bst():
    root, n = build_tree([10, 20, 5, 1, 30, 40, 2])
    assert lowest_common_ancestor(root, n[1], n[30]) is n[20]
    assert lowest_common_ancestor(root, n[40], n[2]) is n[5]
    assert lowest_common_ancestor(root, n[30], n[2]) is n[10]


def test_lca_deep_chain():
    root = TreeNode(0)
    cur = root
    nodes = [root]
    for i in range(1, 500):
        cur.left = TreeNode(i)
        cur = cur.left
        nodes.append(cur)
    assert lowest_common_ancestor(root, nodes[499], nodes[250]) is nodes[250]


def g(rows):
    return [list(r) for r in rows]


def test_num_islands():
    assert num_islands(g(["110", "010", "001"])) == 2
    assert num_islands(g(["11110", "11010", "11000", "00000"])) == 1
    assert num_islands(g(["11000", "11000", "00100", "00011"])) == 3
    assert num_islands([]) == 0
    assert num_islands([[]]) == 0
    assert num_islands(g(["0"])) == 0
    assert num_islands(g(["1"])) == 1
    assert num_islands(g(["101", "010", "101"])) == 5  # diagonals not connected
    assert num_islands(g(["1" * 5] * 5)) == 1


def test_num_islands_large_snake_no_recursion_error():
    n = 300
    rows = []
    for r in range(n):
        if r % 2 == 0:
            rows.append("1" * n)
        elif r % 4 == 1:
            rows.append("0" * (n - 1) + "1")
        else:
            rows.append("1" + "0" * (n - 1))
    assert num_islands(g(rows)) == 1


def test_can_finish():
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(1, []) is True
    assert can_finish(0, []) is True
    assert can_finish(3, []) is True
    assert can_finish(4, [[1, 0], [2, 1], [3, 2]]) is True
    assert can_finish(4, [[1, 0], [2, 1], [3, 2], [1, 3]]) is False
    assert can_finish(1, [[0, 0]]) is False
    assert can_finish(5, [[1, 0], [2, 0], [3, 1], [3, 2], [4, 3]]) is True
    assert can_finish(3, [[1, 0], [1, 0]]) is True  # duplicate edge


# ---------- Set C ----------
def test_top_k_frequent():
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    assert sorted(top_k_frequent([4, 4, 4, 5, 5, 6], 1)) == [4]
    assert sorted(top_k_frequent([-1, -1, 2, 2, 2, 3], 2)) == [-1, 2]
    assert sorted(top_k_frequent([5, 5, 5, 5, 3, 3, 3, 1, 1, 9], 3)) == [1, 3, 5]
    assert len(top_k_frequent(list(range(10)) * 2 + [100] * 3, 1)) == 1
    assert top_k_frequent(list(range(10)) * 2 + [100] * 3, 1) == [100]


def test_top_k_frequent_random_unique_counts():
    rng = random.Random(8)
    for _ in range(20):
        vals = list(range(rng.randint(2, 8)))
        nums = []
        for i, v in enumerate(vals):
            nums += [v] * (i + 1)  # distinct frequencies
        rng.shuffle(nums)
        k = rng.randint(1, len(vals))
        want = sorted(vals[-k:])
        assert sorted(top_k_frequent(nums, k)) == want


def test_word_break():
    assert word_break("leetcode", ["leet", "code"]) is True
    assert word_break("applepenapple", ["apple", "pen"]) is True
    assert word_break("catsandog", ["cats", "dog", "sand", "and", "cat"]) is False
    assert word_break("", ["a"]) is True
    assert word_break("a", []) is False
    assert word_break("", []) is True
    assert word_break("aaaaaaa", ["aaaa", "aaa"]) is True
    assert word_break("aaaaaaab", ["a", "aa"]) is False
    assert word_break("cars", ["car", "ca", "rs"]) is True
    assert word_break("abcd", ["a", "abc", "b", "cd"]) is True


def test_word_break_perf():
    assert word_break("a" * 300 + "b", ["a", "aa", "aaa", "aaaa"]) is False


def test_generate_parentheses():
    assert sorted(generate_parentheses(3)) == ["((()))", "(()())", "(())()", "()(())", "()()()"]
    assert generate_parentheses(0) == [""]
    assert generate_parentheses(1) == ["()"]
    assert sorted(generate_parentheses(2)) == ["(())", "()()"]
    for n, count in [(4, 14), (5, 42), (8, 1430)]:
        res = generate_parentheses(n)
        assert len(res) == count and len(set(res)) == count
        for s in res:
            bal = 0
            for ch in s:
                bal += 1 if ch == "(" else -1
                assert bal >= 0
            assert bal == 0 and len(s) == 2 * n


def test_network_delay_time():
    assert network_delay_time([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2) == 2
    assert network_delay_time([[1, 2, 1]], 2, 1) == 1
    assert network_delay_time([[1, 2, 1]], 2, 2) == -1
    assert network_delay_time([], 1, 1) == 0
    assert network_delay_time([], 2, 1) == -1
    # shorter path via detour
    assert network_delay_time([[1, 2, 10], [1, 3, 1], [3, 2, 1]], 3, 1) == 2
    # cycle
    assert network_delay_time([[1, 2, 1], [2, 1, 1], [2, 3, 5]], 3, 1) == 6
    # disconnected node
    assert network_delay_time([[1, 2, 1], [2, 3, 1]], 4, 1) == -1
    # parallel edges
    assert network_delay_time([[1, 2, 5], [1, 2, 2]], 2, 1) == 2
    # zero-weight edge
    assert network_delay_time([[1, 2, 0], [2, 3, 4]], 3, 1) == 4


def test_network_delay_time_vs_floyd():
    rng = random.Random(6)
    INF = float("inf")
    for _ in range(40):
        n = rng.randint(1, 6)
        edges = [[rng.randint(1, n), rng.randint(1, n), rng.randint(0, 9)] for _ in range(rng.randint(0, 12))]
        k = rng.randint(1, n)
        d = [[INF] * (n + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            d[i][i] = 0
        for u, v, w in edges:
            d[u][v] = min(d[u][v], w)
        for m in range(1, n + 1):
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    d[i][j] = min(d[i][j], d[i][m] + d[m][j])
        far = max(d[k][1:])
        assert network_delay_time(edges, n, k) == (-1 if far == INF else far)
