"""Week 15 exercises: heaps / priority queues. Replace each `...` with your code.

Python's heapq is a MIN-heap on a list: heappush, heappop, heapify, nlargest, nsmallest.
For a max-heap push negated values. For tuples, comparison goes element by element
(add a tie-breaker index if the payload is not comparable).
"""
import heapq
from collections import Counter


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def kth_largest(nums, k):
    """Return the k-th largest element (1-indexed, counting duplicates) of nums.

    Example: [3, 2, 1, 5, 6, 4], k=2 -> 5 ; [3, 2, 3, 1, 2, 4, 5, 5, 6], k=4 -> 4
    Expected: O(n log k) time, O(k) space (not a full sort).
    Hint: keep a MIN-heap of size k; the root is the answer.
    """
    ...


def last_stone_weight(stones):
    """Repeatedly smash the two heaviest stones: equal -> both vanish; otherwise the
    heavier becomes (difference). Return the weight of the last stone, or 0 if none.

    Example: [2, 7, 4, 1, 8, 1] -> 1
    Expected: O(n log n) time, O(n) space.
    Hint: max-heap via negated values.
    """
    ...


class KthLargest:
    """Stream class: KthLargest(k, nums) then add(val) returns the k-th largest element
    of everything seen so far (nums plus all added values).

    Example: k=3, nums=[4, 5, 8, 2]; add(3) -> 4; add(5) -> 5; add(10) -> 5; add(9) -> 8
    Expected: O(log k) per add, O(k) memory. Guaranteed >= k elements when add is called.
    Hint: min-heap capped at size k.
    """

    def __init__(self, k, nums):
        ...

    def _offer(self, x):
        ...

    def add(self, val):
        ...


def top_k_frequent(nums, k):
    """Return the k most frequent elements in any order. The answer is unique in the tests.

    Example: [1, 1, 1, 2, 2, 3], k=2 -> [1, 2] ; [1], k=1 -> [1]
    Expected: O(n log k) time with a heap (O(n) with bucket sort is the follow-up).
    Hint: Counter, then heapq.nlargest(k, counts, key=counts.get) or a size-k min-heap.
    """
    ...


def k_closest(points, k):
    """Return the k points closest to the origin (Euclidean) in any order.
    Ties at the boundary will not appear in tests as an ambiguity of distance values.

    Example: [[1, 3], [-2, 2]], k=1 -> [[-2, 2]] ; [[3, 3], [5, -1], [-2, 4]], k=2 -> [[3, 3], [-2, 4]]
    Expected: O(n log k) time, O(k) space.
    Hint: compare squared distances (no sqrt); max-heap of size k (negated distance).
    """
    ...


def merge_k_lists(lists):
    """Merge k sorted singly linked lists (each a ListNode head or None) into one sorted list;
    return its head (None if all are empty).

    Example: [[1, 4, 5], [1, 3, 4], [2, 6]] -> 1->1->2->3->4->4->5->6
    Expected: O(N log k) time (N = total nodes), O(k) extra space.
    Hint: heap of (value, list_index, node). The index breaks ties so nodes are never compared.
    """
    ...


def reorganize_string(s):
    """Rearrange the characters of s so no two adjacent characters are equal.
    Return any valid arrangement, or "" if impossible.

    Example: "aab" -> "aba" ; "aaab" -> ""
    Expected: O(n log 26) time, O(1)-ish space.
    Hint: max-heap of (count, char). Pop the most frequent char that is not the one just placed;
          hold the previous char out for one step. Impossible iff max count > (n + 1) // 2.
    """
    ...


def task_scheduler(tasks, n):
    """tasks is a list of single-letter tasks (one per time unit). The same task must be
    separated by at least n other units (idle allowed). Return the minimum total time units.

    Example: ["A","A","A","B","B","B"], n=2 -> 8 ; n=0 -> 6
    Expected: O(T log 26) with a heap, or O(T) with the math formula.
    Hint: greedy - always run the most frequent available task. Formula:
          (max_count - 1) * (n + 1) + (number of tasks with max_count), but never less than len(tasks).
    """
    ...


class MedianFinder:
    """Data stream median. addNum(num) adds an integer; findMedian() returns the median
    (mean of the two middle values when the count is even) as a number.

    Example: add 1, add 2 -> median 1.5 ; add 3 -> median 2
    Expected: addNum O(log n), findMedian O(1).
    Hint: two heaps - a max-heap for the lower half and a min-heap for the upper half,
          kept balanced so sizes differ by at most one.
    """

    def __init__(self):
        ...

    def addNum(self, num):
        ...

    def findMedian(self):
        ...


def k_smallest_pairs(nums1, nums2, k):
    """nums1 and nums2 are sorted ascending. Return the k pairs [u, v] (u from nums1, v from
    nums2) with the smallest sums, ordered by sum ascending (ties in any order). Fewer if
    there are fewer than k pairs in total.

    Example: [1, 7, 11], [2, 4, 6], k=3 -> [[1, 2], [1, 4], [1, 6]]
    Expected: O(k log k) time - NOT O(n*m).
    Hint: start with (nums1[i] + nums2[0], i, 0) for the first min(k, len(nums1)) rows,
          pop the smallest, push its successor (i, j + 1). This is "merge k sorted lists" in disguise.
    """
    ...
