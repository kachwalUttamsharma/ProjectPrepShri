"""Week 12: Sorting + checkpoint (mock set covering weeks 1-11).
Replace each `...` with your code. Run: .venv/bin/pytest 03-dsa/week-12-sorting-checkpoint -q
Part A (1-10): sorting algorithms and custom keys. Part B (11-15): MOCK INTERVIEW SET -
time yourself: 2 problems in 45 minutes, no hints, explain complexity aloud.
In problems 1, 2, 8, 9 do NOT call sorted()/list.sort() for the core algorithm."""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


# ---------------------------- Part A: sorting ----------------------------

def merge_sort(nums):
    """Return a NEW sorted list using merge sort (do not mutate the input).
    Example: [5,2,3,1] -> [1,2,3,5] ; [] -> []
    Time O(n log n) always, Space O(n). Must be stable.
    Hint: split in halves, sort each, merge with two pointers (take left on ties)."""
    ...


def quick_sort(nums):
    """Return a NEW sorted list using quick sort. Must handle many duplicates and
    already-sorted input of ~20000 elements without RecursionError or O(n^2) time.
    Example: [3,1,2,3,3] -> [1,2,3,3,3]
    Time O(n log n) expected, Space O(log n) stack (+ output copy).
    Hint: random pivot + 3-way partition (less / equal / greater)."""
    ...


def sort_colors(nums):
    """Sort a list containing only 0, 1, 2 IN PLACE in one pass (return None).
    Example: [2,0,2,1,1,0] -> nums becomes [0,0,1,1,2,2]
    Time O(n), Space O(1).
    Hint: Dutch national flag - pointers low, mid, high."""
    ...


def merge_intervals(intervals):
    """Merge all overlapping intervals ([a,b] and [b,c] touch -> merged).
    Return a list of [start, end] sorted by start.
    Example: [[1,3],[2,6],[8,10],[15,18]] -> [[1,6],[8,10],[15,18]] ; [[1,4],[4,5]] -> [[1,5]]
    Time O(n log n), Space O(n). Hint: sort by start, extend the last merged interval."""
    ...


def largest_number(nums):
    """Arrange non-negative ints so that concatenated they form the largest number.
    Return it as a string (no leading zeros: [0,0] -> '0').
    Example: [10,2] -> '210' ; [3,30,34,5,9] -> '9534330'
    Time O(n log n * L), Space O(n).
    Hint: compare a+b vs b+a as strings: functools.cmp_to_key."""
    ...


def frequency_sort(s):
    """Return s's characters ordered by frequency descending; ties broken by the
    character ascending. Example: 'tree' -> 'eert' ; 'cccaaa' -> 'aaaccc' ; '' -> ''
    Time O(n + k log k), Space O(n). Hint: Counter + sorted with key=(-count, char)."""
    ...


def k_closest(points, k):
    """Return the k points closest to the origin (Euclidean), as a list of
    [x, y] sorted by (distance, x, y). 1 <= k <= len(points).
    Example: ([[1,3],[-2,2]], 1) -> [[-2,2]] ; ([[3,3],[5,-1],[-2,4]], 2) -> [[3,3],[-2,4]]
    Time O(n log n) (O(n log k) with a heap), Space O(n).
    Hint: compare squared distances - no sqrt needed."""
    ...


def count_inversions(nums):
    """Count pairs i < j with nums[i] > nums[j].
    Example: [2,4,1,3,5] -> 3 ; [5,4,3,2,1] -> 10 ; [] -> 0
    Time O(n log n), Space O(n). Hint: during merge sort's merge step, when you take
    from the right half, every remaining left element is an inversion. (MEDIUM+)"""
    ...


def kth_largest(nums, k):
    """Return the k-th largest element (1-indexed, counting duplicates).
    Example: ([3,2,1,5,6,4], 2) -> 5 ; ([3,2,3,1,2,4,5,5,6], 4) -> 4
    Time O(n) average with quickselect (O(n log n) via sorting is acceptable first).
    Space O(1)-O(n). Hint: target index n-k in sorted order; partition and recurse
    on one side only. Randomise the pivot."""
    ...


def sort_students(students):
    """students: list of (name, grade, age). Return a new list sorted by grade
    DESCENDING, then age ASCENDING, then name ASCENDING.
    Example: [('bo',90,20),('al',90,19),('cy',95,30)] -> [('cy',95,30),('al',90,19),('bo',90,20)]
    Time O(n log n), Space O(n). Hint: key=lambda s: (-s[1], s[2], s[0])."""
    ...


# ------------------- Part B: mock interview checkpoint -------------------

def longest_unique_substring(s):
    """(Sliding window, wk5) Length of the longest substring without repeating chars.
    Example: 'abcabcbb' -> 3 ; 'bbbbb' -> 1 ; '' -> 0 ; 'pwwkew' -> 3
    Time O(n), Space O(min(n, alphabet))."""
    ...


def daily_temperatures(temps):
    """(Monotonic stack, wk7) For each day, number of days until a warmer
    temperature; 0 if none. Example: [73,74,75,71,69,72,76,73] -> [1,1,4,2,1,1,0,0]
    Time O(n), Space O(n)."""
    ...


def subarray_sum_k(nums, k):
    """(Prefix sums + hash map, wk3/6) Number of contiguous subarrays summing to k.
    Negatives allowed. Example: ([1,1,1], 2) -> 2 ; ([1,-1,0], 0) -> 3
    Time O(n), Space O(n)."""
    ...


def merge_two_lists(a, b):
    """(Linked lists, wk9) Merge two sorted singly linked lists (heads a, b; may be
    None) into one sorted list by splicing nodes; return the new head.
    Example: 1->2->4 and 1->3->4 -> 1->1->2->3->4->4
    Time O(m + n), Space O(1). Hint: dummy head node."""
    ...


def min_meeting_rooms(intervals):
    """(Sorting + intervals, wk6/12) Minimum rooms needed so all meetings
    [start, end) can happen; a meeting ending at t does not conflict with one
    starting at t. Example: [[0,30],[5,10],[15,20]] -> 2 ; [[7,10],[2,4]] -> 1
    Time O(n log n), Space O(n). Hint: sort starts and ends separately, two pointers
    (or a min-heap of end times)."""
    ...
