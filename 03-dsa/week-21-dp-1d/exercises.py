"""Week 21 exercises: 1-D dynamic programming. Replace each `...` with your code."""


def climb_stairs(n):
    """LeetCode 70. You can climb 1 or 2 steps at a time. Return the number of distinct ways
    to reach the top of n steps (n >= 0; there is 1 way to climb 0 steps).

    Example: 2 -> 2;  3 -> 3;  5 -> 8

    Hint: dp[i] = dp[i-1] + dp[i-2]. Keep only two variables.
    Expected: O(n) time, O(1) space.
    """
    ...


def house_robber(nums):
    """LeetCode 198. nums[i] is the money in house i; you cannot rob two adjacent houses.
    Return the maximum amount you can rob. Empty list -> 0.

    Example: [2,7,9,3,1] -> 12;  [1,2,3,1] -> 4

    Hint: dp[i] = max(dp[i-1], dp[i-2] + nums[i]).
    Expected: O(n) time, O(1) space.
    """
    ...


def house_robber_circular(nums):
    """LeetCode 213. Same as above but the houses are in a circle (first and last are adjacent).

    Example: [2,3,2] -> 3;  [1,2,3,1] -> 4;  [5] -> 5

    Hint: answer = max(rob(nums[1:]), rob(nums[:-1])); single house is a special case.
    Expected: O(n) time.
    """
    ...


def max_subarray(nums):
    """LeetCode 53. Return the largest sum of a non-empty contiguous subarray.

    Example: [-2,1,-3,4,-1,2,1,-5,4] -> 6;  [-3,-1,-2] -> -1

    Hint: Kadane: best_ending_here = max(x, best_ending_here + x).
    Expected: O(n) time, O(1) space.
    """
    ...


def max_product_subarray(nums):
    """LeetCode 152. Return the largest product of a non-empty contiguous subarray.

    Example: [2,3,-2,4] -> 6;  [-2,0,-1] -> 0;  [-2,3,-4] -> 24

    Hint: track both the max and the min product ending here (a negative flips them).
    Expected: O(n) time, O(1) space.
    """
    ...


def coin_change(coins, amount):
    """LeetCode 322. Return the fewest coins (unlimited supply of each denomination) that sum
    to `amount`, or -1 if impossible. amount 0 -> 0.

    Example: [1,2,5], 11 -> 3;  [2], 3 -> -1;  [1,3,4], 6 -> 2

    Hint: dp[a] = min(dp[a - c] + 1 for c in coins). Greedy fails on [1,3,4].
    Expected: O(amount * len(coins)) time, O(amount) space.
    """
    ...


def coin_change_ways(amount, coins):
    """LeetCode 518. Return the number of *combinations* (order does not matter) of coins that
    make up `amount`. amount 0 -> 1.

    Example: 5, [1,2,5] -> 4;  3, [2] -> 0;  10, [10] -> 1

    Hint: coins in the OUTER loop, amounts in the inner loop (else you count permutations).
    Expected: O(amount * len(coins)) time, O(amount) space.
    """
    ...


def length_of_lis(nums):
    """LeetCode 300. Return the length of the longest strictly increasing subsequence.

    Example: [10,9,2,5,3,7,101,18] -> 4;  [7,7,7] -> 1;  [] -> 0

    Hint: O(n^2) DP first; then the O(n log n) "tails" array with bisect_left.
    Expected: O(n log n) time.
    """
    ...


def word_break(s, word_dict):
    """LeetCode 139. Return True if s can be segmented into a space-separated sequence of
    words from word_dict (words can be reused).

    Example: "leetcode", ["leet","code"] -> True;  "catsandog", ["cats","dog","sand","and","cat"] -> False

    Hint: dp[i] = True if some j < i has dp[j] and s[j:i] in the set. Convert the list to a set.
    Expected: O(n^2) time (plus hashing cost), O(n) space.
    """
    ...


def num_decodings(s):
    """LeetCode 91. 'A'=1 ... 'Z'=26. Return the number of ways to decode the digit string s.
    Return 0 if it cannot be decoded (e.g. leading '0'). s is non-empty.

    Example: "12" -> 2;  "226" -> 3;  "06" -> 0;  "10" -> 1

    Hint: dp[i] = (dp[i-1] if s[i-1] != '0') + (dp[i-2] if 10 <= int(s[i-2:i]) <= 26).
    Expected: O(n) time, O(1) space.
    """
    ...
