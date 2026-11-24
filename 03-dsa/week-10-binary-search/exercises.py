"""Week 10: Binary search (including binary search on the answer).
Replace each `...` with your code. Run: .venv/bin/pytest 03-dsa/week-10-binary-search -q
Aim for the stated complexity: every problem here is O(log n) or O(n log(range))."""


def binary_search(nums, target):
    """Return the index of target in sorted list nums, or -1 if absent.
    Example: ([-1,0,3,5,9,12], 9) -> 4 ; ([-1,0,3,5,9,12], 2) -> -1
    Time O(log n), Space O(1).
    Hint: lo, hi = 0, len(nums)-1 ; loop while lo <= hi ; mid = (lo+hi)//2."""
    ...


def search_insert(nums, target):
    """Sorted list of distinct ints. Return index of target, or the index where it
    would be inserted to keep order.
    Example: ([1,3,5,6], 5) -> 2 ; ([1,3,5,6], 2) -> 1 ; ([1,3,5,6], 7) -> 4
    Time O(log n), Space O(1).
    Hint: this is 'first index with nums[i] >= target' (lower bound)."""
    ...


def search_range(nums, target):
    """Sorted list (duplicates allowed). Return [first, last] index of target,
    or [-1, -1] if absent.
    Example: ([5,7,7,8,8,10], 8) -> [3, 4] ; ([5,7,7,8,8,10], 6) -> [-1, -1]
    Time O(log n), Space O(1).
    Hint: write one helper `lower_bound` and use lower_bound(t) and lower_bound(t+1)-1."""
    ...


def my_sqrt(x):
    """Return floor(sqrt(x)) for int x >= 0 without using ** 0.5 / math.sqrt.
    Example: 8 -> 2 ; 16 -> 4 ; 0 -> 0
    Time O(log x), Space O(1).
    Hint: binary search on the answer in [0, x]; find the largest m with m*m <= x."""
    ...


def search_rotated(nums, target):
    """Sorted list of DISTINCT ints rotated at an unknown pivot. Return index of
    target or -1.
    Example: ([4,5,6,7,0,1,2], 0) -> 4 ; ([4,5,6,7,0,1,2], 3) -> -1
    Time O(log n), Space O(1).
    Hint: at each mid, one half [lo..mid] or [mid..hi] is always sorted.
    Check whether target lies in the sorted half."""
    ...


def find_min_rotated(nums):
    """Sorted list of distinct ints rotated at an unknown pivot (maybe 0 times).
    Return the minimum element.
    Example: [3,4,5,1,2] -> 1 ; [11,13,15,17] -> 11 ; [2,1] -> 1
    Time O(log n), Space O(1).
    Hint: compare nums[mid] with nums[hi]; if nums[mid] > nums[hi] min is right of mid."""
    ...


def find_peak(nums):
    """Return the index of ANY peak: nums[i] > both neighbours (out-of-bounds
    counts as -infinity). Adjacent elements are never equal.
    Example: [1,2,3,1] -> 2 ; [1,2,1,3,5,6,4] -> 1 or 5
    Time O(log n), Space O(1).
    Hint: if nums[mid] < nums[mid+1] a peak exists on the right, else on the left (incl. mid)."""
    ...


def min_eating_speed(piles, h):
    """Koko has piles of bananas and h hours. Each hour she picks one pile and eats
    up to k bananas from it (leftovers of that pile are wasted for the hour).
    Return the minimum integer k so she finishes all piles within h hours.
    Guaranteed len(piles) <= h.
    Example: ([3,6,7,11], 8) -> 4 ; ([30,11,23,4,20], 5) -> 30 ; ([30,11,23,4,20], 6) -> 23
    Time O(n log(max)), Space O(1).
    Hint: binary search on k in [1, max(piles)]; feasibility = sum(ceil(p/k)) <= h."""
    ...


def ship_within_days(weights, days):
    """Packages must be shipped in the given order; each day the ship carries a
    contiguous run of packages whose total weight <= capacity. Return the least
    capacity that ships everything within `days` days.
    Example: ([1,2,3,4,5,6,7,8,9,10], 5) -> 15 ; ([3,2,2,4,1,4], 3) -> 6 ; ([1,2,3,1,1], 4) -> 3
    Time O(n log(sum)), Space O(1).
    Hint: capacity in [max(weights), sum(weights)]; greedy simulate to test feasibility."""
    ...


def split_array(nums, k):
    """Split nums (non-negative ints) into k non-empty contiguous subarrays so the
    largest subarray sum is minimised. Return that minimised largest sum.
    Example: ([7,2,5,10,8], 2) -> 18 ; ([1,2,3,4,5], 2) -> 9 ; ([1,4,4], 3) -> 4
    Time O(n log(sum)), Space O(1).
    Hint: same shape as ship_within_days - binary search on the answer."""
    ...


def find_median_sorted_arrays(a, b):
    """Two sorted lists (not both empty). Return the median of their union as a float.
    Example: ([1,3], [2]) -> 2.0 ; ([1,2], [3,4]) -> 2.5
    Time O(log(min(m, n))), Space O(1).  (HARD)
    Hint: binary search the partition of the SMALLER array; the partition is valid when
    left_a_max <= right_b_min and left_b_max <= right_a_min. Use +-inf at the borders."""
    ...
