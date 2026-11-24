import random
import time
from collections import deque

from exercises import *


# ---------- RecentCounter ----------
def test_recent_counter_example():
    rc = RecentCounter()
    assert rc.ping(1) == 1
    assert rc.ping(100) == 2
    assert rc.ping(3001) == 3
    assert rc.ping(3002) == 3


def test_recent_counter_boundary_inclusive():
    rc = RecentCounter()
    assert rc.ping(0) == 1
    assert rc.ping(3000) == 2   # 0 is still in [0, 3000]
    assert rc.ping(3001) == 2   # 0 expired


def test_recent_counter_large_gap_and_many():
    rc = RecentCounter()
    for t in range(1, 1001):
        rc.ping(t)
    assert rc.ping(10 ** 9) == 1
    rc2 = RecentCounter()
    last = 0
    for t in range(0, 200000, 1):
        last = rc2.ping(t)
    assert last == 3001


# ---------- MovingAverage ----------
def test_moving_average_example():
    m = MovingAverage(3)
    assert m.next(1) == 1.0
    assert m.next(10) == 5.5
    assert abs(m.next(3) - 14 / 3) < 1e-9
    assert m.next(5) == 6.0


def test_moving_average_size_one_and_negative():
    m = MovingAverage(1)
    assert m.next(5) == 5
    assert m.next(-3) == -3
    m = MovingAverage(2)
    assert m.next(-2) == -2
    assert m.next(2) == 0
    assert m.next(4) == 3


def test_moving_average_many():
    m = MovingAverage(100)
    vals = list(range(5000))
    for i, v in enumerate(vals):
        got = m.next(v)
        window = vals[max(0, i - 99): i + 1]
        assert abs(got - sum(window) / len(window)) < 1e-6


# ---------- MyQueue ----------
def test_my_queue_example():
    q = MyQueue()
    assert q.empty() is True
    q.push(1)
    q.push(2)
    assert q.peek() == 1
    assert q.pop() == 1
    assert q.empty() is False
    assert q.pop() == 2
    assert q.empty() is True


def test_my_queue_interleaved():
    q = MyQueue()
    q.push(1)
    q.push(2)
    q.push(3)
    assert q.pop() == 1
    q.push(4)
    assert q.peek() == 2
    assert q.pop() == 2
    assert q.pop() == 3
    q.push(5)
    assert q.pop() == 4
    assert q.pop() == 5
    assert q.empty()


def test_my_queue_random_vs_deque():
    rnd = random.Random(7)
    q, ref = MyQueue(), deque()
    for i in range(20000):
        if ref and rnd.random() < 0.45:
            if rnd.random() < 0.3:
                assert q.peek() == ref[0]
            assert q.pop() == ref.popleft()
        else:
            q.push(i)
            ref.append(i)
        assert q.empty() == (not ref)


def test_my_queue_duplicates_and_none_like():
    q = MyQueue()
    for v in [0, 0, 0]:
        q.push(v)
    assert q.pop() == 0 and q.pop() == 0 and q.pop() == 0
    assert q.empty()


# ---------- time_required_to_buy ----------
def test_time_required_to_buy():
    assert time_required_to_buy([2, 3, 2], 2) == 6
    assert time_required_to_buy([5, 1, 1, 1], 0) == 8
    assert time_required_to_buy([1], 0) == 1
    assert time_required_to_buy([1, 1, 1], 2) == 3
    assert time_required_to_buy([1, 1, 1], 0) == 1
    assert time_required_to_buy([84, 49, 5, 24, 70, 77, 87, 8], 3) == 154


def test_time_required_to_buy_vs_simulation():
    rnd = random.Random(8)
    for _ in range(100):
        n = rnd.randint(1, 8)
        t = [rnd.randint(1, 6) for _ in range(n)]
        k = rnd.randrange(n)
        q = deque((i, x) for i, x in enumerate(t))
        sec = 0
        while True:
            i, x = q.popleft()
            sec += 1
            x -= 1
            if x == 0:
                if i == k:
                    break
            else:
                q.append((i, x))
        assert time_required_to_buy(t, k) == sec


# ---------- rotting_oranges ----------
def test_rotting_oranges_examples():
    assert rotting_oranges([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert rotting_oranges([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert rotting_oranges([[0, 2]]) == 0
    assert rotting_oranges([[0]]) == 0
    assert rotting_oranges([]) == 0


def test_rotting_oranges_edge():
    assert rotting_oranges([[1]]) == -1
    assert rotting_oranges([[2]]) == 0
    assert rotting_oranges([[1, 2]]) == 1
    assert rotting_oranges([[2, 0, 1]]) == -1
    assert rotting_oranges([[2, 1, 1, 1, 1, 2]]) == 2   # multi-source
    assert rotting_oranges([[1, 1], [1, 1]]) == -1


def test_rotting_oranges_does_not_mutate():
    g = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
    assert rotting_oranges(g) == 4
    assert g == [[2, 1, 1], [1, 1, 0], [0, 1, 1]]


def test_rotting_oranges_large():
    n = 300
    g = [[1] * n for _ in range(n)]
    g[0][0] = 2
    assert rotting_oranges(g) == 2 * (n - 1)


# ---------- min_steps_open_lock ----------
def test_open_lock_examples():
    assert min_steps_open_lock(["0201", "0101", "0102", "1212", "2002"], "0202") == 6
    assert min_steps_open_lock(["8888"], "0009") == 1
    assert min_steps_open_lock(
        ["8887", "8889", "8878", "8898", "8788", "8988", "7888", "9888"], "8888") == -1
    assert min_steps_open_lock(["0000"], "8888") == -1


def test_open_lock_edge():
    assert min_steps_open_lock([], "0000") == 0
    assert min_steps_open_lock([], "0001") == 1
    assert min_steps_open_lock([], "9999") == 4
    assert min_steps_open_lock([], "5555") == 20
    assert min_steps_open_lock(["0001", "0009", "0010", "0090", "0100", "0900", "1000", "9000"], "0002") == -1
    assert min_steps_open_lock(["1111"], "1111") == -1


def test_open_lock_speed():
    t = time.time()
    assert min_steps_open_lock([], "5555") == 20
    assert time.time() - t < 3


# ---------- sliding_window_maximum ----------
def test_sliding_window_maximum_examples():
    assert sliding_window_maximum([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
    assert sliding_window_maximum([1], 1) == [1]
    assert sliding_window_maximum([9, 11], 2) == [11]
    assert sliding_window_maximum([4, 3, 2, 1], 2) == [4, 3, 2]
    assert sliding_window_maximum([], 3) == []


def test_sliding_window_maximum_edge():
    assert sliding_window_maximum([1, 2, 3], 1) == [1, 2, 3]
    assert sliding_window_maximum([-5, -3, -4], 2) == [-3, -3]
    assert sliding_window_maximum([2, 2, 2, 2], 2) == [2, 2, 2]
    assert sliding_window_maximum([1, 2, 3, 4], 4) == [4]
    assert sliding_window_maximum([7, 2, 4], 2) == [7, 4]


def test_sliding_window_maximum_random_and_large():
    rnd = random.Random(9)
    for _ in range(100):
        a = [rnd.randint(-10, 10) for _ in range(rnd.randint(1, 30))]
        k = rnd.randint(1, len(a))
        exp = [max(a[i:i + k]) for i in range(len(a) - k + 1)]
        assert sliding_window_maximum(a, k) == exp
    big = list(range(200000))
    assert sliding_window_maximum(big, 1000)[:3] == [999, 1000, 1001]
    assert sliding_window_maximum(big[::-1], 50000)[0] == 199999


# ---------- longest_subarray_with_limit ----------
def test_longest_subarray_limit_examples():
    assert longest_subarray_with_limit([8, 2, 4, 7], 4) == 2
    assert longest_subarray_with_limit([10, 1, 2, 4, 7, 2], 5) == 4
    assert longest_subarray_with_limit([4, 2, 2, 2, 4, 4, 2, 2], 0) == 3
    assert longest_subarray_with_limit([], 3) == 0
    assert longest_subarray_with_limit([5], 0) == 1


def test_longest_subarray_limit_edge():
    assert longest_subarray_with_limit([1, 2, 3, 4], 100) == 4
    assert longest_subarray_with_limit([-1, -5, -3], 2) == 2
    assert longest_subarray_with_limit([1, 5, 9], 0) == 1


def test_longest_subarray_limit_random_and_large():
    rnd = random.Random(10)
    for _ in range(100):
        a = [rnd.randint(-5, 5) for _ in range(rnd.randint(1, 25))]
        lim = rnd.randint(0, 6)
        best = 0
        for i in range(len(a)):
            for j in range(i, len(a)):
                if max(a[i:j + 1]) - min(a[i:j + 1]) <= lim:
                    best = max(best, j - i + 1)
        assert longest_subarray_with_limit(a, lim) == best
    assert longest_subarray_with_limit(list(range(100000)), 10) == 11
    assert longest_subarray_with_limit([3] * 100000, 0) == 100000


# ---------- max_result_jump_game ----------
def test_max_result_examples():
    assert max_result_jump_game([1, -1, -2, 4, -7, 3], 2) == 7
    assert max_result_jump_game([10, -5, -2, 4, 0, 3], 3) == 17
    assert max_result_jump_game([1, -5, -20, 4, -1, 3, -6, -3], 2) == 0
    assert max_result_jump_game([5], 1) == 5


def test_max_result_edge():
    assert max_result_jump_game([1, 2], 1) == 3
    assert max_result_jump_game([-1, -2, -3], 1) == -6
    assert max_result_jump_game([-1, -2, -3], 2) == -4
    assert max_result_jump_game([1, 2, 3], 100) == 6


def test_max_result_random_and_large():
    rnd = random.Random(11)
    for _ in range(100):
        a = [rnd.randint(-10, 10) for _ in range(rnd.randint(1, 15))]
        k = rnd.randint(1, 5)
        n = len(a)
        dp = [None] * n
        dp[0] = a[0]
        for i in range(1, n):
            dp[i] = a[i] + max(dp[max(0, i - k):i])
        assert max_result_jump_game(a, k) == dp[-1]
    big = [1] * 200000
    assert max_result_jump_game(big, 1) == 200000
    assert max_result_jump_game(big, 100000) == 200000


# ---------- shortest_subarray_at_least_k ----------
def test_shortest_subarray_examples():
    assert shortest_subarray_at_least_k([1], 1) == 1
    assert shortest_subarray_at_least_k([1, 2], 4) == -1
    assert shortest_subarray_at_least_k([2, -1, 2], 3) == 3
    assert shortest_subarray_at_least_k([84, -37, 32, 40, 95], 167) == 3
    assert shortest_subarray_at_least_k([-28, 81, -20, 28, -29], 89) == 3


def test_shortest_subarray_edge():
    assert shortest_subarray_at_least_k([], 1) == -1
    assert shortest_subarray_at_least_k([-1, -2], 1) == -1
    assert shortest_subarray_at_least_k([5, 5, 5], 5) == 1
    assert shortest_subarray_at_least_k([1, 1, 1, 1], 4) == 4
    assert shortest_subarray_at_least_k([48, 99, 37, 4, -31], 140) == 2


def test_shortest_subarray_random_and_large():
    rnd = random.Random(12)
    for _ in range(200):
        a = [rnd.randint(-5, 8) for _ in range(rnd.randint(1, 20))]
        k = rnd.randint(1, 15)
        best = -1
        for i in range(len(a)):
            s = 0
            for j in range(i, len(a)):
                s += a[j]
                if s >= k:
                    if best == -1 or j - i + 1 < best:
                        best = j - i + 1
                    break
        assert shortest_subarray_at_least_k(a, k) == best
    big = [1] * 200000
    assert shortest_subarray_at_least_k(big, 100000) == 100000
    assert shortest_subarray_at_least_k([-1] * 100000 + [5], 5) == 1
