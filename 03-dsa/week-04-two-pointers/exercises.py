"""Week 4 exercises: two pointers. Replace each `...` with your code.

Run the tests from this folder:  ../../../.venv/bin/pytest -q
Aim for the stated time/space complexity; every problem has an O(n) answer except three_sum (O(n^2)).
"""


def is_palindrome(s):
    """LeetCode 125. Return True if s reads the same forwards and backwards
    after keeping only alphanumeric characters and ignoring case.

    is_palindrome("A man, a plan, a canal: Panama") -> True
    is_palindrome("race a car") -> False
    is_palindrome("") -> True

    Hint: left/right pointers moving inward, skipping non-alphanumerics (str.isalnum).
    Time O(n), space O(1) (do not build a cleaned copy).
    """
    ...


def two_sum_sorted(nums, target):
    """LeetCode 167 (0-indexed). nums is sorted ascending. Return [i, j] with
    i < j and nums[i] + nums[j] == target. If no pair exists return [].
    (If several pairs exist, any valid pair is accepted.)

    two_sum_sorted([2, 7, 11, 15], 9) -> [0, 1]
    two_sum_sorted([1, 2], 10) -> []

    Hint: sum too small -> move left up; too big -> move right down.
    Time O(n), space O(1).
    """
    ...


def remove_duplicates_sorted(nums):
    """LeetCode 26. nums is sorted. Modify it IN PLACE so the first k entries are
    the unique values in original order; return k. Contents after index k are ignored.

    nums = [0, 0, 1, 1, 2] -> returns 3, nums[:3] == [0, 1, 2]
    [] -> 0

    Hint: slow pointer = next write position, fast pointer = scanner.
    Time O(n), space O(1).
    """
    ...


def move_zeroes(nums):
    """LeetCode 283. Move all 0s to the end IN PLACE keeping the relative order of
    the non-zero elements. Return None.

    [0, 1, 0, 3, 12] -> nums becomes [1, 3, 12, 0, 0]

    Hint: write pointer for the next non-zero; swap instead of overwriting.
    Time O(n), space O(1), minimise writes.
    """
    ...


def is_subsequence(s, t):
    """LeetCode 392. Return True if s is a subsequence of t (characters of s appear
    in t in order, not necessarily adjacent).

    is_subsequence("abc", "ahbgdc") -> True
    is_subsequence("axc", "ahbgdc") -> False
    is_subsequence("", "anything") -> True

    Time O(len(t)), space O(1).
    """
    ...


def merge_sorted_in_place(nums1, m, nums2, n):
    """LeetCode 88. nums1 has length m + n; its first m entries are sorted and the
    last n are 0 placeholders. nums2 has n sorted entries. Merge nums2 into nums1
    IN PLACE so nums1 is sorted. Return None.

    nums1 = [1, 2, 3, 0, 0, 0], m = 3, nums2 = [2, 5, 6], n = 3
    -> nums1 becomes [1, 2, 2, 3, 5, 6]

    Hint: fill from the BACK so you never overwrite unread values.
    Time O(m + n), space O(1).
    """
    ...


def max_area(height):
    """LeetCode 11. height[i] is the height of a vertical line at x = i. Choose two
    lines that, with the x-axis, form a container holding the most water. Return that
    area (width * min(height of the two lines)). Fewer than 2 lines -> 0.

    max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) -> 49
    max_area([1, 1]) -> 1

    Hint: start at both ends; always move the pointer at the SHORTER line. Why is that safe?
    Time O(n), space O(1).
    """
    ...


def sort_colors(nums):
    """LeetCode 75 (Dutch national flag). nums contains only 0, 1, 2. Sort IN PLACE
    in a single pass without using sort(). Return None.

    [2, 0, 2, 1, 1, 0] -> nums becomes [0, 0, 1, 1, 2, 2]

    Hint: three pointers low / mid / high. When you swap with high, do NOT advance mid.
    Time O(n), space O(1).
    """
    ...


def three_sum(nums):
    """LeetCode 15. Return all UNIQUE triplets [a, b, c] with a + b + c == 0.
    Triplets may be in any order, and elements inside a triplet in any order, but no
    triplet value may appear twice.

    three_sum([-1, 0, 1, 2, -1, -4]) -> [[-1, -1, 2], [-1, 0, 1]]
    three_sum([0, 0, 0, 0]) -> [[0, 0, 0]]

    Hint: sort, fix the first number, then two-pointer the rest; skip duplicates
    for all three positions.
    Time O(n^2), space O(1) extra (ignoring output / sort).
    """
    ...


def trap(height):
    """LeetCode 42 (hard). height[i] is the elevation at x = i (width 1 each). Return
    how many units of rain water are trapped between the bars.

    trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) -> 6
    trap([4, 2, 0, 3, 2, 5]) -> 9

    Hint: water above bar i = min(max_left, max_right) - height[i]. Two pointers let
    you track running maxima from both sides; always process the side with the smaller max.
    Time O(n), space O(1).
    """
    ...
