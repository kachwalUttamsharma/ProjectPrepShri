"""Week 23 exercises: greedy algorithms and bit manipulation. Replace each `...` with your code."""


def single_number(nums):
    """Every element appears twice except one. Return that one.

    [4,1,2,1,2] -> 4
    Expected: O(n) time, O(1) space.
    Hint: x ^ x == 0 and x ^ 0 == x.
    """
    ...


def hamming_weight(n):
    """Number of 1 bits in non-negative int n.

    11 (0b1011) -> 3
    0 -> 0
    Expected: O(number of set bits).
    Hint: n & (n - 1) clears the lowest set bit.
    """
    ...


def is_power_of_two(n):
    """True iff n is a positive power of two (1, 2, 4, ...). 0 and negatives -> False.

    16 -> True, 18 -> False, 0 -> False
    Expected: O(1).
    Hint: powers of two have exactly one set bit.
    """
    ...


def missing_number(nums):
    """nums holds n distinct values from 0..n; return the missing one.

    [3,0,1] -> 2
    [0] -> 1
    Expected: O(n) time, O(1) space.
    Hint: XOR all indices 0..n with all values (or use the sum formula).
    """
    ...


def max_profit_ii(prices):
    """Buy/sell stock any number of times (one share at a time). Max profit.

    [7,1,5,3,6,4] -> 7
    [5,4,3] -> 0
    Expected: O(n) time, O(1) space.
    Hint: greedy -- take every positive day-to-day difference.
    """
    ...


def can_jump(nums):
    """nums[i] = max jump length from i. Can you reach the last index from index 0?

    [2,3,1,1,4] -> True
    [3,2,1,0,4] -> False
    Expected: O(n) time, O(1) space.
    Hint: track the farthest reachable index; fail if you stand beyond it.
    """
    ...


def min_jumps(nums):
    """Minimum jumps to reach the last index (guaranteed reachable). len 1 -> 0.

    [2,3,1,1,4] -> 2
    [2,3,0,1,4] -> 2
    Expected: O(n) time, O(1) space.
    Hint: BFS by "levels": current window end, farthest next reach.
    """
    ...


def gas_station(gas, cost):
    """Circular route. gas[i] gained at station i, cost[i] to drive to i+1.
    Return the starting index that completes the circuit, or -1. (Answer is unique if it exists.)

    gas=[1,2,3,4,5], cost=[3,4,5,1,2] -> 3
    gas=[2,3,4], cost=[3,4,3] -> -1
    Expected: O(n) time, O(1) space.
    Hint: if total gas < total cost -> -1. Otherwise when the tank goes
    negative at i, restart from i+1.
    """
    ...


def partition_labels(s):
    """Partition s into as many parts as possible so each letter appears in at
    most one part. Return the list of part sizes. Empty -> [].

    "ababcbacadefegdehijhklij" -> [9,7,8]
    Expected: O(n) time, O(1) space (26 letters).
    Hint: record last index of each char; extend the current part's end.
    """
    ...


def erase_overlap_intervals(intervals):
    """Minimum number of intervals to remove so the rest do not overlap.
    Intervals that only touch ([1,2],[2,3]) do NOT overlap.

    [[1,2],[2,3],[3,4],[1,3]] -> 1
    [[1,2],[1,2],[1,2]] -> 2
    Expected: O(n log n) time.
    Hint: sort by END time; keep an interval if it starts >= last kept end.
    """
    ...
