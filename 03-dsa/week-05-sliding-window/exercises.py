"""Week 5 exercises: sliding window. Replace each `...` with your code.

Run the tests from this folder:  ../../../.venv/bin/pytest -q
Every problem here has an O(n) (or O(n) with a small alphabet) solution.
The tests include large inputs, so an O(n*k) or O(n^2) answer will be slow.
"""


def max_sum_subarray_k(nums, k):
    """Return the maximum sum of any contiguous subarray of length exactly k.
    If k <= 0 or k > len(nums), return 0.

    max_sum_subarray_k([2, 1, 5, 1, 3, 2], 3) -> 9
    max_sum_subarray_k([-1, -2, -3], 2) -> -3

    Hint: fixed-size window; add the entering element, subtract the leaving one.
    Time O(n), space O(1).
    """
    ...


def contains_nearby_duplicate(nums, k):
    """LeetCode 219. Return True if there are two DISTINCT indices i, j with
    nums[i] == nums[j] and abs(i - j) <= k.

    contains_nearby_duplicate([1, 2, 3, 1], 3) -> True
    contains_nearby_duplicate([1, 2, 3, 1, 2, 3], 2) -> False
    contains_nearby_duplicate([1, 1], 0) -> False

    Hint: a window of the last k elements kept in a set.
    Time O(n), space O(k).
    """
    ...


def min_subarray_len(target, nums):
    """LeetCode 209. nums contains positive integers. Return the minimal length of a
    contiguous subarray whose sum is >= target, or 0 if none exists.

    min_subarray_len(7, [2, 3, 1, 2, 4, 3]) -> 2   ([4, 3])
    min_subarray_len(100, [1, 2, 3]) -> 0

    Hint: variable window; expand right, then shrink left while the sum is still enough.
    Why does this need positive numbers?
    Time O(n), space O(1).
    """
    ...


def length_of_longest_substring(s):
    """LeetCode 3. Length of the longest substring of s without repeating characters.

    length_of_longest_substring("abcabcbb") -> 3
    length_of_longest_substring("bbbbb") -> 1
    length_of_longest_substring("") -> 0

    Hint: dict char -> last index; when you see a repeat inside the window jump left
    past it (never move left backwards).
    Time O(n), space O(min(n, alphabet)).
    """
    ...


def longest_ones(nums, k):
    """LeetCode 1004. nums contains only 0 and 1. You may flip at most k zeros to 1.
    Return the length of the longest run of 1s you can get.

    longest_ones([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2) -> 6
    longest_ones([0, 0, 0], 0) -> 0

    Hint: window may contain at most k zeros.
    Time O(n), space O(1).
    """
    ...


def character_replacement(s, k):
    """LeetCode 424. s is uppercase letters. You may change at most k characters to any
    letter. Return the length of the longest substring of one repeated letter you can get.

    character_replacement("ABAB", 2) -> 4
    character_replacement("AABABBA", 1) -> 4

    Hint: a window is valid if (window length - count of its most frequent letter) <= k.
    You do not need to shrink max_count when the window slides; think about why.
    Time O(n), space O(26).
    """
    ...


def check_inclusion(s1, s2):
    """LeetCode 567. Return True if s2 contains a permutation of s1 as a substring.

    check_inclusion("ab", "eidbaooo") -> True
    check_inclusion("ab", "eidboaoo") -> False
    check_inclusion("", "abc") -> True

    Hint: fixed window of len(s1) with a character-count comparison (collections.Counter,
    or a 'matches' counter for O(1) updates).
    Time O(n), space O(alphabet).
    """
    ...


def find_anagrams(s, p):
    """LeetCode 438. Return the start indices (ascending) of every substring of s that is
    an anagram of p.

    find_anagrams("cbaebabacd", "abc") -> [0, 6]
    find_anagrams("abab", "ab") -> [0, 1, 2]
    find_anagrams("a", "ab") -> []

    Time O(n), space O(alphabet).
    """
    ...


def longest_substring_k_distinct(s, k):
    """Length of the longest substring with at most k distinct characters.
    k <= 0 -> 0.

    longest_substring_k_distinct("eceba", 2) -> 3    ("ece")
    longest_substring_k_distinct("aa", 1) -> 2
    longest_substring_k_distinct("abc", 0) -> 0

    Hint: dict of counts in the window; shrink while len(dict) > k.
    Time O(n), space O(k).
    """
    ...


def min_window(s, t):
    """LeetCode 76 (hard). Return the smallest substring of s that contains every
    character of t (with multiplicity). If none exists return "". If several windows
    have the minimum length, return the leftmost.

    min_window("ADOBECODEBANC", "ABC") -> "BANC"
    min_window("a", "aa") -> ""
    min_window("aa", "aa") -> "aa"
    t == "" -> ""

    Hint: track `missing` = number of required characters still not covered; expand right
    until missing == 0, then shrink left as far as possible while it stays 0.
    Time O(len(s) + len(t)), space O(alphabet).
    """
    ...


def max_sliding_window(nums, k):
    """LeetCode 239 (hard). Return a list with the maximum of every window of size k.
    Empty nums or k <= 0 -> []. If k > len(nums) -> [].

    max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) -> [3, 3, 5, 5, 6, 7]
    max_sliding_window([1], 1) -> [1]

    Hint: monotonic deque of INDICES whose values are decreasing; the front is the max.
    Pop the front when it leaves the window, pop the back while it is <= the new value.
    Time O(n), space O(k).
    """
    ...
