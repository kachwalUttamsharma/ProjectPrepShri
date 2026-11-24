import random

from exercises import *


# ---------- is_valid_parentheses ----------
def test_valid_basic():
    assert is_valid_parentheses("()") is True
    assert is_valid_parentheses("()[]{}") is True
    assert is_valid_parentheses("{[]}") is True
    assert is_valid_parentheses("([{}])") is True


def test_valid_invalid():
    assert is_valid_parentheses("(]") is False
    assert is_valid_parentheses("([)]") is False
    assert is_valid_parentheses("(") is False
    assert is_valid_parentheses(")") is False
    assert is_valid_parentheses("((") is False
    assert is_valid_parentheses("))") is False
    assert is_valid_parentheses("(()") is False


def test_valid_empty_and_large():
    assert is_valid_parentheses("") is True
    assert is_valid_parentheses("(" * 100000 + ")" * 100000) is True
    assert is_valid_parentheses("(" * 100000 + ")" * 99999) is False


# ---------- remove_adjacent_duplicates ----------
def test_remove_adjacent_duplicates():
    assert remove_adjacent_duplicates("abbaca") == "ca"
    assert remove_adjacent_duplicates("azxxzy") == "ay"
    assert remove_adjacent_duplicates("aaa") == "a"
    assert remove_adjacent_duplicates("aaaa") == ""
    assert remove_adjacent_duplicates("") == ""
    assert remove_adjacent_duplicates("a") == "a"
    assert remove_adjacent_duplicates("abc") == "abc"
    assert remove_adjacent_duplicates("abccba") == ""


def test_remove_adjacent_duplicates_large():
    s = "ab" * 50000 + "ba" * 50000
    assert remove_adjacent_duplicates(s) == ""


# ---------- MinStack ----------
def test_min_stack_example():
    s = MinStack()
    s.push(-2)
    s.push(0)
    s.push(-3)
    assert s.get_min() == -3
    s.pop()
    assert s.top() == 0
    assert s.get_min() == -2


def test_min_stack_duplicates_of_min():
    s = MinStack()
    s.push(1)
    s.push(1)
    s.push(1)
    s.pop()
    assert s.get_min() == 1
    s.pop()
    assert s.get_min() == 1
    assert s.top() == 1


def test_min_stack_single_and_negatives():
    s = MinStack()
    s.push(5)
    assert s.top() == 5 and s.get_min() == 5
    s.push(-10)
    assert s.get_min() == -10
    s.pop()
    assert s.get_min() == 5


def test_min_stack_random_vs_list():
    rnd = random.Random(1)
    s, ref = MinStack(), []
    for _ in range(3000):
        if ref and rnd.random() < 0.4:
            s.pop()
            ref.pop()
        else:
            v = rnd.randint(-50, 50)
            s.push(v)
            ref.append(v)
        if ref:
            assert s.top() == ref[-1]
            assert s.get_min() == min(ref)


# ---------- eval_rpn ----------
def test_eval_rpn_examples():
    assert eval_rpn(["2", "1", "+", "3", "*"]) == 9
    assert eval_rpn(["4", "13", "5", "/", "+"]) == 6
    assert eval_rpn(["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]) == 22


def test_eval_rpn_edge():
    assert eval_rpn(["5"]) == 5
    assert eval_rpn(["-5"]) == -5
    assert eval_rpn(["3", "4", "-"]) == -1  # order of operands
    assert eval_rpn(["-7", "2", "/"]) == -3  # truncate toward zero
    assert eval_rpn(["7", "-2", "/"]) == -3
    assert eval_rpn(["-7", "-2", "/"]) == 3
    assert eval_rpn(["0", "3", "/"]) == 0
    assert isinstance(eval_rpn(["6", "3", "/"]), int)


# ---------- daily_temperatures ----------
def test_daily_temperatures():
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([30, 60, 90]) == [1, 1, 0]
    assert daily_temperatures([90, 80, 70]) == [0, 0, 0]
    assert daily_temperatures([50, 50, 50]) == [0, 0, 0]
    assert daily_temperatures([30]) == [0]
    assert daily_temperatures([]) == []


def test_daily_temperatures_large_vs_bruteforce():
    rnd = random.Random(2)
    t = [rnd.randint(30, 100) for _ in range(300)]
    exp = []
    for i in range(len(t)):
        d = 0
        for j in range(i + 1, len(t)):
            if t[j] > t[i]:
                d = j - i
                break
        exp.append(d)
    assert daily_temperatures(t) == exp
    big = list(range(200000, 0, -1))
    assert daily_temperatures(big) == [0] * 200000


# ---------- next_greater_circular ----------
def test_next_greater_circular():
    assert next_greater_circular([1, 2, 1]) == [2, -1, 2]
    assert next_greater_circular([1, 2, 3, 4, 3]) == [2, 3, 4, -1, 4]
    assert next_greater_circular([5]) == [-1]
    assert next_greater_circular([]) == []
    assert next_greater_circular([2, 2, 2]) == [-1, -1, -1]
    assert next_greater_circular([5, 4, 3, 2, 1]) == [-1, 5, 5, 5, 5]


def test_next_greater_circular_negatives_and_random():
    assert next_greater_circular([-3, -1, -2]) == [-1, -1, -1]
    rnd = random.Random(3)
    a = [rnd.randint(-5, 5) for _ in range(200)]
    n = len(a)
    exp = []
    for i in range(n):
        r = -1
        for k in range(1, n):
            if a[(i + k) % n] > a[i]:
                r = a[(i + k) % n]
                break
        exp.append(r)
    assert next_greater_circular(a) == exp


# ---------- simplify_path ----------
def test_simplify_path():
    assert simplify_path("/home/") == "/home"
    assert simplify_path("/../") == "/"
    assert simplify_path("/home//foo/") == "/home/foo"
    assert simplify_path("/a/./b/../../c/") == "/c"
    assert simplify_path("/a/../../b") == "/b"
    assert simplify_path("/...") == "/..."
    assert simplify_path("/") == "/"
    assert simplify_path("///") == "/"
    assert simplify_path("/a/b/c/../../..") == "/"
    assert simplify_path("/a/b/c/../../../..") == "/"
    assert simplify_path("/.hidden/../..a/./b") == "/..a/b"


# ---------- asteroid_collision ----------
def test_asteroid_collision():
    assert asteroid_collision([5, 10, -5]) == [5, 10]
    assert asteroid_collision([8, -8]) == []
    assert asteroid_collision([10, 2, -5]) == [10]
    assert asteroid_collision([-2, -1, 1, 2]) == [-2, -1, 1, 2]
    assert asteroid_collision([]) == []
    assert asteroid_collision([7]) == [7]
    assert asteroid_collision([1, -2]) == [-2]
    assert asteroid_collision([1, 2, 3, -10]) == [-10]
    assert asteroid_collision([-5, 5, -5]) == [-5]
    assert asteroid_collision([3, 3, -3]) == [3]


def test_asteroid_collision_more():
    assert asteroid_collision([2, -1, -1]) == [2]
    assert asteroid_collision([2, -1, -1, -1]) == [2]
    assert asteroid_collision([4, 3, 2, 1, -5]) == [-5]
    assert asteroid_collision([1] * 1000 + [-1] * 1000) == []


def test_asteroid_collision_large_chain():
    res = asteroid_collision([1] * 1000 + [-2] * 1000)
    assert res == [-2] * 1000
    assert asteroid_collision([-1] * 50000 + [1] * 50000) == [-1] * 50000 + [1] * 50000


# ---------- decode_string ----------
def test_decode_string():
    assert decode_string("3[a]2[bc]") == "aaabcbc"
    assert decode_string("3[a2[c]]") == "accaccacc"
    assert decode_string("2[abc]3[cd]ef") == "abcabccdcdcdef"
    assert decode_string("abc") == "abc"
    assert decode_string("") == ""
    assert decode_string("10[a]") == "a" * 10
    assert decode_string("1[a]") == "a"
    assert decode_string("2[2[2[a]]]") == "a" * 8
    assert decode_string("a2[b]c") == "abbc"
    assert decode_string("2[]") == ""
    assert decode_string("100[ab]") == "ab" * 100
    assert decode_string("2[a2[b]c]d") == "abbcabbcd"


# ---------- largest_rectangle_in_histogram ----------
def test_histogram_examples():
    assert largest_rectangle_in_histogram([2, 1, 5, 6, 2, 3]) == 10
    assert largest_rectangle_in_histogram([2, 4]) == 4
    assert largest_rectangle_in_histogram([]) == 0
    assert largest_rectangle_in_histogram([5]) == 5
    assert largest_rectangle_in_histogram([0]) == 0
    assert largest_rectangle_in_histogram([1, 1, 1, 1]) == 4
    assert largest_rectangle_in_histogram([6, 5, 4, 3, 2, 1]) == 12
    assert largest_rectangle_in_histogram([1, 2, 3, 4, 5, 6]) == 12
    assert largest_rectangle_in_histogram([0, 0, 0]) == 0
    assert largest_rectangle_in_histogram([2, 0, 2]) == 2


def test_histogram_random_vs_bruteforce():
    rnd = random.Random(4)
    for _ in range(100):
        h = [rnd.randint(0, 8) for _ in range(rnd.randint(1, 15))]
        best = 0
        for i in range(len(h)):
            m = h[i]
            for j in range(i, len(h)):
                m = min(m, h[j])
                best = max(best, m * (j - i + 1))
        assert largest_rectangle_in_histogram(h) == best


def test_histogram_large():
    assert largest_rectangle_in_histogram([1] * 200000) == 200000
    h = list(range(1, 2001))
    assert largest_rectangle_in_histogram(h) == max(x * (2001 - x) for x in h)


# ---------- trap_rain_water ----------
def test_trap_rain_water():
    assert trap_rain_water([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap_rain_water([4, 2, 0, 3, 2, 5]) == 9
    assert trap_rain_water([]) == 0
    assert trap_rain_water([3]) == 0
    assert trap_rain_water([3, 3]) == 0
    assert trap_rain_water([1, 2, 3]) == 0
    assert trap_rain_water([3, 2, 1]) == 0
    assert trap_rain_water([3, 0, 3]) == 3
    assert trap_rain_water([0, 0, 0]) == 0


def test_trap_rain_water_random_vs_bruteforce():
    rnd = random.Random(5)
    for _ in range(100):
        h = [rnd.randint(0, 9) for _ in range(rnd.randint(0, 20))]
        exp = sum(
            max(0, min(max(h[: i + 1]), max(h[i:])) - h[i]) for i in range(len(h))
        )
        assert trap_rain_water(h) == exp


def test_trap_rain_water_large():
    h = [5] + [0] * 100000 + [5]
    assert trap_rain_water(h) == 500000
