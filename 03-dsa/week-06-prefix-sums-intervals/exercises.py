"""Week 6 exercises: prefix sums and intervals. Replace each `...` with your code.

Run the tests from this folder:  ../../../.venv/bin/pytest -q
Intervals are lists [start, end] with start <= end. Unless a problem says otherwise,
intervals that only touch at an endpoint (e.g. [1, 2] and [2, 3]) are treated as overlapping
for merging, and as NOT overlapping for meeting rooms / removal problems.
"""


def running_sum(nums):
    """LeetCode 1480. Return a new list where result[i] = nums[0] + ... + nums[i].

    running_sum([1, 2, 3, 4]) -> [1, 3, 6, 10]
    running_sum([]) -> []

    Time O(n), space O(n) for the output.
    """
    ...


class NumArray:
    """LeetCode 303. Build once, then answer many range-sum queries in O(1).

    na = NumArray([-2, 0, 3, -5, 2, -1])
    na.sum_range(0, 2) -> 1     (inclusive on both ends)
    na.sum_range(2, 5) -> -1
    na.sum_range(3, 3) -> -5
    """

    def __init__(self, nums):
        """Precompute a prefix array of length n + 1 (prefix[0] = 0). O(n)."""
        ...

    def sum_range(self, left, right):
        """Return sum(nums[left..right]) inclusive. O(1)."""
        ...


def pivot_index(nums):
    """LeetCode 724. Return the leftmost index where the sum of the elements strictly to its
    left equals the sum strictly to its right (an empty side sums to 0). Return -1 if none.

    pivot_index([1, 7, 3, 6, 5, 6]) -> 3
    pivot_index([1, 2, 3]) -> -1
    pivot_index([2, 1, -1]) -> 0

    Hint: left_sum and total - left_sum - nums[i].
    Time O(n), space O(1).
    """
    ...


def subarray_sum(nums, k):
    """LeetCode 560. Return the number of contiguous subarrays whose sum equals k.
    nums may contain negatives and zeros (so a sliding window does NOT work).

    subarray_sum([1, 1, 1], 2) -> 2
    subarray_sum([1, 2, 3], 3) -> 2     ([1, 2] and [3])
    subarray_sum([0, 0, 0], 0) -> 6

    Hint: sum(i..j) = prefix[j+1] - prefix[i]. Count how many earlier prefixes equal
    current_prefix - k, using a dict of prefix -> frequency (seed it with {0: 1}).
    Time O(n), space O(n).
    """
    ...


def product_except_self(nums):
    """LeetCode 238. Return a list where result[i] is the product of all elements of nums
    except nums[i]. Do NOT use division (nums may contain zeros).

    product_except_self([1, 2, 3, 4]) -> [24, 12, 8, 6]
    product_except_self([-1, 1, 0, -3, 3]) -> [0, 0, 9, 0, 0]

    Hint: prefix products going right, then a running suffix product going left.
    Time O(n), space O(1) extra (the output list does not count).
    """
    ...


def range_addition(length, updates):
    """LeetCode 370. Start with a list of `length` zeros. Each update is [start, end, inc]:
    add inc to every element with index start..end inclusive. Return the final list.

    range_addition(5, [[1, 3, 2], [2, 4, 3], [0, 2, -2]]) -> [-2, 0, 3, 5, 3]
    range_addition(3, []) -> [0, 0, 0]

    Hint: difference array. diff[start] += inc; diff[end + 1] -= inc; then prefix-sum it.
    Time O(n + q), space O(n). (Naively applying each update is O(n * q).)
    """
    ...


def merge_intervals(intervals):
    """LeetCode 56. Merge all overlapping intervals (touching endpoints count as overlapping)
    and return the result sorted by start. Do not mutate the input.

    merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) -> [[1, 6], [8, 10], [15, 18]]
    merge_intervals([[1, 4], [4, 5]]) -> [[1, 5]]
    merge_intervals([]) -> []

    Hint: sort by start, then extend the last merged interval or start a new one.
    Time O(n log n), space O(n).
    """
    ...


def insert_interval(intervals, new_interval):
    """LeetCode 57. intervals is sorted by start and non-overlapping. Insert new_interval,
    merging where needed, and return the new sorted non-overlapping list.

    insert_interval([[1, 3], [6, 9]], [2, 5]) -> [[1, 5], [6, 9]]
    insert_interval([], [5, 7]) -> [[5, 7]]
    insert_interval([[1, 5]], [2, 3]) -> [[1, 5]]

    Hint: three phases in one pass: everything ending before new starts, everything
    overlapping (merge), everything starting after new ends.
    Time O(n), space O(n).
    """
    ...


def erase_overlap_intervals(intervals):
    """LeetCode 435. Return the minimum number of intervals to remove so the rest are
    non-overlapping. Intervals that only touch ([1, 2] and [2, 3]) do NOT overlap.

    erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) -> 1
    erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) -> 2
    erase_overlap_intervals([]) -> 0

    Hint: greedy. Sort by END; keep an interval if it starts at/after the last kept end.
    Time O(n log n), space O(1) extra.
    """
    ...


def min_meeting_rooms(intervals):
    """LeetCode 253. Each interval is a meeting [start, end). Return the minimum number of
    rooms needed so no two overlapping meetings share a room. A meeting ending at time t and
    another starting at t can use the same room.

    min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) -> 2
    min_meeting_rooms([[7, 10], [2, 4]]) -> 1
    min_meeting_rooms([]) -> 0

    Hint: sort starts and ends separately and sweep, OR use a min-heap of end times.
    Time O(n log n), space O(n).
    """
    ...


def interval_intersection(first, second):
    """LeetCode 986. first and second are each lists of closed intervals, sorted and
    pairwise disjoint within their own list. Return the sorted list of their intersections
    (a single shared point like [5, 5] counts).

    interval_intersection([[0, 2], [5, 10], [13, 23], [24, 25]],
                          [[1, 5], [8, 12], [15, 24], [25, 26]])
      -> [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    interval_intersection([], [[1, 2]]) -> []

    Hint: two pointers; advance the one whose interval ends first.
    Time O(m + n), space O(1) extra.
    """
    ...
