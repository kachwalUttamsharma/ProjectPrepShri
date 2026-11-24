import random

from exercises import *


def test_single_number():
    assert single_number([2, 2, 1]) == 1
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([7]) == 7
    assert single_number([-1, 3, 3]) == -1
    assert single_number([0, 5, 5]) == 0
    assert single_number([10**9, 1, 1]) == 10**9


def test_hamming_weight():
    assert hamming_weight(0) == 0
    assert hamming_weight(1) == 1
    assert hamming_weight(11) == 3
    assert hamming_weight(128) == 1
    assert hamming_weight(2**32 - 1) == 32
    assert hamming_weight(2**40 + 1) == 2


def test_is_power_of_two():
    assert is_power_of_two(1) is True
    assert is_power_of_two(2) is True
    assert is_power_of_two(16) is True
    assert is_power_of_two(2**30) is True
    assert is_power_of_two(0) is False
    assert is_power_of_two(-2) is False
    assert is_power_of_two(-(2**31)) is False
    assert is_power_of_two(3) is False
    assert is_power_of_two(18) is False
    assert is_power_of_two(2**30 + 1) is False


def test_missing_number():
    assert missing_number([3, 0, 1]) == 2
    assert missing_number([0, 1]) == 2
    assert missing_number([1]) == 0
    assert missing_number([0]) == 1
    assert missing_number([]) == 0
    assert missing_number([9, 6, 4, 2, 3, 5, 7, 0, 1]) == 8
    nums = list(range(1001))
    nums.remove(500)
    random.Random(1).shuffle(nums)
    assert missing_number(nums) == 500


def test_max_profit_ii():
    assert max_profit_ii([7, 1, 5, 3, 6, 4]) == 7
    assert max_profit_ii([1, 2, 3, 4, 5]) == 4
    assert max_profit_ii([7, 6, 4, 3, 1]) == 0
    assert max_profit_ii([]) == 0
    assert max_profit_ii([5]) == 0
    assert max_profit_ii([3, 3, 3]) == 0
    assert max_profit_ii([1, 5, 1, 5]) == 8


def test_can_jump():
    assert can_jump([2, 3, 1, 1, 4]) is True
    assert can_jump([3, 2, 1, 0, 4]) is False
    assert can_jump([0]) is True
    assert can_jump([0, 1]) is False
    assert can_jump([1, 0]) is True
    assert can_jump([2, 0, 0]) is True
    assert can_jump([1, 1, 0, 1]) is False
    assert can_jump([10, 0, 0, 0, 0, 0]) is True


def test_can_jump_vs_bruteforce():
    rng = random.Random(5)
    for _ in range(100):
        nums = [rng.randint(0, 3) for _ in range(rng.randint(1, 9))]
        reach = {0}
        for i in range(len(nums)):
            if i in reach:
                reach.update(range(i, min(len(nums), i + nums[i] + 1)))
        assert can_jump(nums) == ((len(nums) - 1) in reach)


def test_min_jumps():
    assert min_jumps([2, 3, 1, 1, 4]) == 2
    assert min_jumps([2, 3, 0, 1, 4]) == 2
    assert min_jumps([0]) == 0
    assert min_jumps([1, 1, 1, 1]) == 3
    assert min_jumps([5, 1, 1, 1, 1]) == 1
    assert min_jumps([1, 2, 3]) == 2
    assert min_jumps([10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 1, 0]) == 2
    assert min_jumps([1, 1]) == 1


def test_gas_station():
    assert gas_station([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert gas_station([2, 3, 4], [3, 4, 3]) == -1
    assert gas_station([5], [4]) == 0
    assert gas_station([4], [5]) == -1
    assert gas_station([5, 1, 2, 3, 4], [4, 4, 1, 5, 1]) == 4
    assert gas_station([3, 1, 1], [1, 2, 2]) == 0
    assert gas_station([2, 2, 2], [2, 2, 2]) == 0


def test_gas_station_vs_bruteforce():
    rng = random.Random(11)
    for _ in range(100):
        n = rng.randint(1, 7)
        gas = [rng.randint(0, 5) for _ in range(n)]
        cost = [rng.randint(0, 5) for _ in range(n)]
        ok = []
        for s in range(n):
            tank = 0
            good = True
            for k in range(n):
                i = (s + k) % n
                tank += gas[i] - cost[i]
                if tank < 0:
                    good = False
                    break
            if good:
                ok.append(s)
        res = gas_station(gas, cost)
        if ok:
            assert res in ok
        else:
            assert res == -1


def test_partition_labels():
    assert partition_labels("ababcbacadefegdehijhklij") == [9, 7, 8]
    assert partition_labels("eccbbbbdec") == [10]
    assert partition_labels("abc") == [1, 1, 1]
    assert partition_labels("a") == [1]
    assert partition_labels("") == []
    assert partition_labels("aaaa") == [4]
    assert partition_labels("abab") == [4]
    assert partition_labels("caedbdedda") == [1, 9]


def test_erase_overlap_intervals():
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    assert erase_overlap_intervals([]) == 0
    assert erase_overlap_intervals([[1, 5]]) == 0
    assert erase_overlap_intervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2
    assert erase_overlap_intervals([[0, 2], [1, 3], [2, 4], [3, 5], [4, 6]]) == 2
    assert erase_overlap_intervals([[-5, -1], [-3, 0], [0, 2]]) == 1


def test_erase_overlap_vs_bruteforce():
    rng = random.Random(9)
    for _ in range(60):
        n = rng.randint(0, 8)
        iv = []
        for _ in range(n):
            a = rng.randint(0, 8)
            iv.append([a, a + rng.randint(1, 4)])
        best = 0
        for mask in range(1 << n):
            chosen = sorted(iv[i] for i in range(n) if mask >> i & 1)
            if all(chosen[k][1] <= chosen[k + 1][0] for k in range(len(chosen) - 1)):
                best = max(best, len(chosen))
        assert erase_overlap_intervals(iv) == n - best
