"""Week 3 exercises: hash maps and sets. Replace each `...` with your code.

Where several answers are valid, the tests check validity, not an exact output.
"""


def two_sum(nums, target):
    """Return indices [i, j], i != j, with nums[i] + nums[j] == target.
    Exactly one valid pair exists. Any order of the two indices is accepted.

    Example: [2, 7, 11, 15], 9 -> [0, 1]; [3, 3], 6 -> [0, 1]
    Target: O(n) time, O(n) space. Hint: dict value -> index, check complement first.
    """
    ...


def ransom_note(note, magazine):
    """Return True if note can be built from the letters of magazine (each letter used once).

    Example: "aa", "aab" -> True; "aa", "ab" -> False; "", "x" -> True
    Target: O(n + m) time, O(1) space (bounded alphabet). Hint: Counter.
    """
    ...


def isomorphic_strings(s, t):
    """Return True if s and t are isomorphic: characters of s can be replaced to get t,
    with a consistent ONE-TO-ONE mapping (no two chars map to the same char).

    Example: "egg", "add" -> True; "foo", "bar" -> False; "badc", "baba" -> False
    Target: O(n) time. Hint: keep both s->t and t->s maps.
    """
    ...


def contains_nearby_duplicate(nums, k):
    """Return True if there are i != j with nums[i] == nums[j] and |i - j| <= k.

    Example: [1, 2, 3, 1], 3 -> True; [1, 0, 1, 1], 1 -> True; [1, 2, 3, 1, 2, 3], 2 -> False
    Target: O(n) time. Hint: dict value -> last index seen.
    """
    ...


def group_anagrams(strs):
    """Group the strings that are anagrams of each other. Return a list of groups
    (lists). Group order and order inside groups do not matter.

    Example: ["eat","tea","tan","ate","nat","bat"] -> [["eat","tea","ate"],["tan","nat"],["bat"]]
    Target: O(n * k log k) with sorted keys, or O(n * k) with count-tuple keys.
    """
    ...


def top_k_frequent(nums, k):
    """Return the k most frequent values (any order). A unique answer is guaranteed
    (no ties across the k-th boundary).

    Example: [1,1,1,2,2,3], 2 -> [1, 2]; [1], 1 -> [1]
    Target: better than O(n log n): O(n) with bucket sort, or O(n log k) with a heap.
    Hint: Counter, then buckets indexed by frequency.
    """
    ...


def longest_consecutive(nums):
    """Return the length of the longest run of consecutive integers (as a set of values,
    order in nums irrelevant; duplicates count once).

    Example: [100, 4, 200, 1, 3, 2] -> 4 (1,2,3,4); [] -> 0; [0,3,7,2,5,8,4,6,0,1] -> 9
    Target: O(n) time. Hint: only start counting at x where x - 1 is not in the set.
    """
    ...


def subarray_sum_equals_k(nums, k):
    """Return the number of contiguous subarrays whose sum equals k (nums may hold negatives).

    Example: [1, 1, 1], 2 -> 2; [1, 2, 3], 3 -> 2; [1, -1, 0], 0 -> 3
    Target: O(n) time, O(n) space. Hint: prefix sums; count[prefix - k]. Seed count[0] = 1.
    """
    ...


def four_sum_count(a, b, c, d):
    """Four equal-length lists. Return the number of tuples (i, j, k, l) with
    a[i] + b[j] + c[k] + d[l] == 0.

    Example: [1, 2], [-2, -1], [-1, 2], [0, 2] -> 2
    Target: O(n^2) time and space (not O(n^4)). Hint: map sums of a+b, look up -(c+d).
    """
    ...


class LRUCache:
    """Least-recently-used cache with fixed capacity (capacity >= 1).

    get(key)       -> value or -1 if absent; marks key as most recently used.
    put(key, val)  -> insert or update (update also marks as most recent); if the
                      size would exceed capacity, evict the least recently used key.
    Both operations must be O(1). Hint: collections.OrderedDict (move_to_end,
    popitem(last=False)), or dict + doubly linked list.

    Example: c = LRUCache(2); c.put(1, 1); c.put(2, 2); c.get(1) -> 1;
             c.put(3, 3) evicts key 2; c.get(2) -> -1
    """

    def __init__(self, capacity):
        ...

    def get(self, key):
        ...

    def put(self, key, value):
        ...
