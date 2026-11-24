"""Week 8 exercises: queues, deque, BFS and monotonic queues. Replace each `...` with your code.

Run tests from the repo root:  .venv/bin/pytest 03-dsa/week-08-queues-deque-monotonic-queue -q
Use collections.deque. Never use list.pop(0) in a loop.
"""
from collections import deque


class RecentCounter:
    """LeetCode 933. Count requests in the last 3000 ms (inclusive window).

    ping(t) records a request at time t (ms) and returns the number of requests
    with time in [t - 3000, t]. Calls have strictly increasing t.

    rc = RecentCounter(); rc.ping(1) -> 1; rc.ping(100) -> 2
    rc.ping(3001) -> 3; rc.ping(3002) -> 3
    Hint: deque; pop from the left while the front is older than t - 3000.
    Amortized O(1) per ping.
    """

    def __init__(self):
        ...

    def ping(self, t):
        ...


class MovingAverage:
    """LeetCode 346. Moving average of the last `size` values of a stream.

    m = MovingAverage(3); m.next(1) -> 1.0; m.next(10) -> 5.5
    m.next(3) -> 4.666...; m.next(5) -> 6.0   (window is now 10, 3, 5)
    Hint: deque + running sum (or deque(maxlen=size)). O(1) per call.
    """

    def __init__(self, size):
        ...

    def next(self, val):
        ...


class MyQueue:
    """LeetCode 232. FIFO queue using only two stacks (Python lists, using only
    append / pop from the end / peek at [-1] / len).

    q = MyQueue(); q.push(1); q.push(2); q.peek() -> 1; q.pop() -> 1; q.empty() -> False
    Operations: push(x), pop() -> value, peek() -> value, empty() -> bool.
    pop/peek are only called on a non-empty queue.
    Amortized O(1) per operation.
    """

    def __init__(self):
        ...

    def push(self, x):
        ...

    def pop(self):
        ...

    def peek(self):
        ...

    def empty(self):
        ...


def time_required_to_buy(tickets, k):
    """LeetCode 2073. People stand in a line; person i wants tickets[i] tickets.
    Each second the person at the front buys ONE ticket and, if they still want
    more, goes to the back of the line (the purchase takes 1 second; leaving the
    line when done takes no time). Return the seconds until person k finishes.

    tickets=[2,3,2], k=2 -> 6      tickets=[5,1,1,1], k=0 -> 8      [1], 0 -> 1
    Hint: simulate with a deque of (index, remaining), or find an O(n) formula
    (person i contributes min(tickets[i], tickets[k]) if i <= k else
    min(tickets[i], tickets[k] - 1)).
    Time O(n) (formula) / O(sum) (simulation).
    """
    ...


def rotting_oranges(grid):
    """LeetCode 994. grid[r][c]: 0 empty, 1 fresh orange, 2 rotten orange.
    Every minute, each fresh orange 4-directionally adjacent to a rotten one
    becomes rotten. Return the minutes until no fresh orange remains, or -1 if
    impossible. No fresh oranges at the start -> 0.

    [[2,1,1],[1,1,0],[0,1,1]] -> 4      [[2,1,1],[0,1,1],[1,0,1]] -> -1
    [[0,2]] -> 0      [[0]] -> 0      [] -> 0
    Hint: multi-source BFS: enqueue ALL rotten oranges first, process level by level.
    Time O(R*C), Space O(R*C). Do not mutate the caller's grid (copy it).
    """
    ...


def min_steps_open_lock(deadends, target):
    """LeetCode 752. A lock has 4 wheels, each '0'-'9' wrapping around (9 -> 0
    and 0 -> 9). Start at '0000'. One move turns one wheel one step up or down.
    If the lock shows a deadend it jams (you can't move further from it). Return
    the minimum moves to reach `target`, or -1.

    deadends=["0201","0101","0102","1212","2002"], target="0202" -> 6
    deadends=["8888"], target="0009" -> 1
    deadends=["8887","8889","8878","8898","8788","8988","7888","9888"], "8888" -> -1
    deadends=["0000"], "8888" -> -1      target == "0000" -> 0 (unless "0000" is a deadend -> -1)
    Hint: BFS over 10^4 states; each state has 8 neighbours.
    Time O(10^4 * 8).
    """
    ...


def sliding_window_maximum(nums, k):
    """LeetCode 239. Return the max of every contiguous window of size k.

    [1,3,-1,-3,5,3,6,7], k=3 -> [3,3,5,5,6,7]      [1], 1 -> [1]
    [9,11], 2 -> [11]      [4,3,2,1], 2 -> [4,3,2]      [], k -> []
    Assume 1 <= k <= len(nums) when nums is non-empty.
    Hint: monotonic decreasing deque of indices; expire the front.
    Time O(n), Space O(k).
    """
    ...


def longest_subarray_with_limit(nums, limit):
    """LeetCode 1438. Return the length of the longest contiguous subarray in
    which max - min <= limit.

    [8,2,4,7], 4 -> 2      [10,1,2,4,7,2], 5 -> 4      [4,2,2,2,4,4,2,2], 0 -> 3
    [], 3 -> 0      [5], 0 -> 1
    Hint: sliding window (two pointers) + two monotonic deques (max and min).
    Time O(n), Space O(n).
    """
    ...


def max_result_jump_game(nums, k):
    """LeetCode 1696. Start at index 0, score nums[0]. From index i you may jump
    to any index in [i+1, min(i+k, n-1)], adding that element's value to the
    score. Reach the last index; return the maximum possible score.

    [1,-1,-2,4,-7,3], k=2 -> 7      [10,-5,-2,4,0,3], k=3 -> 17
    [1,-5,-20,4,-1,3,-6,-3], k=2 -> 0      [5], k=1 -> 5
    Hint: dp[i] = nums[i] + max(dp[i-k..i-1]); keep the window max with a
    monotonic deque of indices.
    Time O(n), Space O(n).
    """
    ...


def shortest_subarray_at_least_k(nums, k):
    """LeetCode 862 (Hard). Return the length of the shortest non-empty
    contiguous subarray with sum >= k, or -1. nums may contain NEGATIVES
    (so the simple sliding window fails). k >= 1.

    [1], 1 -> 1      [1,2], 4 -> -1      [2,-1,2], 3 -> 3
    [84,-37,32,40,95], 167 -> 3      [-28,81,-20,28,-29], 89 -> 3
    Hint: prefix sums P; for each j, find the nearest i < j with P[j]-P[i] >= k.
    Keep a deque of indices with INCREASING prefix sums: pop the front while
    P[j]-P[front] >= k (record length), and pop the back while P[back] >= P[j].
    Time O(n), Space O(n).
    """
    ...
