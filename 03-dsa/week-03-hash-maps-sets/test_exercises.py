from exercises import *


def check_two_sum(nums, target):
    r = two_sum(nums, target)
    assert isinstance(r, (list, tuple)) and len(r) == 2
    i, j = r
    assert i != j and 0 <= i < len(nums) and 0 <= j < len(nums)
    assert nums[i] + nums[j] == target


def test_two_sum():
    check_two_sum([2, 7, 11, 15], 9)
    check_two_sum([3, 2, 4], 6)
    check_two_sum([3, 3], 6)
    check_two_sum([-1, -2, -3, -4, -5], -8)
    check_two_sum([0, 4, 3, 0], 0)
    check_two_sum([5, 75, 25], 100)
    big = list(range(100000)) + [10 ** 9, 5]
    check_two_sum(big, 10 ** 9 + 5)
    assert sorted(two_sum([3, 2, 4], 6)) == [1, 2]


def test_ransom_note():
    assert ransom_note("aa", "aab") is True
    assert ransom_note("aa", "ab") is False
    assert ransom_note("", "x") is True
    assert ransom_note("", "") is True
    assert ransom_note("a", "") is False
    assert ransom_note("abc", "cba") is True
    assert ransom_note("a" * 50000, "a" * 49999 + "b") is False
    assert ransom_note("a" * 50000, "b" + "a" * 50000) is True


def test_isomorphic_strings():
    assert isomorphic_strings("egg", "add") is True
    assert isomorphic_strings("foo", "bar") is False
    assert isomorphic_strings("badc", "baba") is False
    assert isomorphic_strings("paper", "title") is True
    assert isomorphic_strings("", "") is True
    assert isomorphic_strings("a", "b") is True
    assert isomorphic_strings("ab", "aa") is False
    assert isomorphic_strings("aa", "ab") is False
    assert isomorphic_strings("ab", "abc") is False
    assert isomorphic_strings("ab" * 50000, "cd" * 50000) is True


def test_contains_nearby_duplicate():
    assert contains_nearby_duplicate([1, 2, 3, 1], 3) is True
    assert contains_nearby_duplicate([1, 0, 1, 1], 1) is True
    assert contains_nearby_duplicate([1, 2, 3, 1, 2, 3], 2) is False
    assert contains_nearby_duplicate([], 5) is False
    assert contains_nearby_duplicate([1], 1) is False
    assert contains_nearby_duplicate([1, 1], 0) is False
    assert contains_nearby_duplicate([1, 2, 1], 1) is False
    assert contains_nearby_duplicate([1, 2, 1], 2) is True
    assert contains_nearby_duplicate(list(range(100000)) + [0], 99999) is False
    assert contains_nearby_duplicate(list(range(100000)) + [0], 100000) is True


def norm(groups):
    return sorted(sorted(g) for g in groups)


def test_group_anagrams():
    got = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    assert norm(got) == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    assert group_anagrams([]) == []
    assert norm(group_anagrams([""])) == [[""]]
    assert norm(group_anagrams(["a"])) == [["a"]]
    assert norm(group_anagrams(["", ""])) == [["", ""]]
    assert norm(group_anagrams(["ab", "ba", "ab"])) == [["ab", "ab", "ba"]]
    assert norm(group_anagrams(["abc", "abd"])) == [["abc"], ["abd"]]
    words = ["".join(sorted(str(i))) + "x" for i in range(5000)]
    assert sum(len(g) for g in group_anagrams(words)) == 5000


def test_top_k_frequent():
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    assert sorted(top_k_frequent([4, 4, 4, 5, 5, 6], 1)) == [4]
    assert sorted(top_k_frequent([-1, -1, 2, 2, 2, 3], 2)) == [-1, 2]
    assert sorted(top_k_frequent([1, 2, 3, 3, 2, 3, 2, 3], 2)) == [2, 3]
    nums = []
    for v in range(1, 301):
        nums += [v] * v
    assert sorted(top_k_frequent(nums, 3)) == [298, 299, 300]
    assert len(top_k_frequent(nums, 300)) == 300


def test_longest_consecutive():
    assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4
    assert longest_consecutive([]) == 0
    assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
    assert longest_consecutive([5]) == 1
    assert longest_consecutive([1, 1, 1]) == 1
    assert longest_consecutive([-2, -1, 0, 1]) == 4
    assert longest_consecutive([1, 3, 5]) == 1
    assert longest_consecutive([9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6]) == 7
    import random
    nums = list(range(200000))
    random.Random(1).shuffle(nums)
    assert longest_consecutive(nums) == 200000


def test_subarray_sum_equals_k():
    assert subarray_sum_equals_k([1, 1, 1], 2) == 2
    assert subarray_sum_equals_k([1, 2, 3], 3) == 2
    assert subarray_sum_equals_k([1, -1, 0], 0) == 3
    assert subarray_sum_equals_k([], 0) == 0
    assert subarray_sum_equals_k([5], 5) == 1
    assert subarray_sum_equals_k([5], 4) == 0
    assert subarray_sum_equals_k([0, 0, 0], 0) == 6
    assert subarray_sum_equals_k([-1, -1, 1], 0) == 1
    assert subarray_sum_equals_k([1] * 100000, 1) == 100000
    assert subarray_sum_equals_k([0] * 2000, 0) == 2000 * 2001 // 2


def test_four_sum_count():
    assert four_sum_count([1, 2], [-2, -1], [-1, 2], [0, 2]) == 2
    assert four_sum_count([0], [0], [0], [0]) == 1
    assert four_sum_count([1], [1], [1], [1]) == 0
    assert four_sum_count([], [], [], []) == 0
    assert four_sum_count([-1, -1], [-1, 1], [-1, 1], [1, -1]) == 6
    n = 400
    assert four_sum_count([0] * n, [0] * n, [0] * n, [0] * n) == n ** 4
    a = list(range(500)); b = [-x for x in a]
    # a[i] + b[j] == 0 iff i == j (500 pairs); c, d all zeros -> 500 * 500 * 500
    assert four_sum_count(a, b, [0] * 500, [0] * 500) == 500 * 500 * 500


def test_lru_cache_basic():
    c = LRUCache(2)
    c.put(1, 1)
    c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)
    assert c.get(2) == -1
    c.put(4, 4)
    assert c.get(1) == -1
    assert c.get(3) == 3
    assert c.get(4) == 4


def test_lru_cache_update_and_capacity_one():
    c = LRUCache(1)
    c.put(1, "a")
    assert c.get(1) == "a"
    c.put(2, "b")
    assert c.get(1) == -1
    assert c.get(2) == "b"
    d = LRUCache(2)
    d.put(1, 1)
    d.put(2, 2)
    d.put(1, 10)       # update refreshes recency
    d.put(3, 3)        # evicts 2, not 1
    assert d.get(1) == 10
    assert d.get(2) == -1
    assert d.get(3) == 3
    assert d.get(99) == -1


def test_lru_cache_large():
    c = LRUCache(1000)
    for i in range(100000):
        c.put(i, i)
    assert c.get(0) == -1
    assert c.get(99999) == 99999
    assert c.get(99000) == 99000
    assert c.get(98999) == -1
