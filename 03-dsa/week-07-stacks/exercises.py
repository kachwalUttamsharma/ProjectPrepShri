"""Week 7 exercises: stacks and monotonic stacks. Replace each `...` with your code.

Run tests from the repo root:  .venv/bin/pytest 03-dsa/week-07-stacks -q
Aim for the stated time/space complexity.
"""


def is_valid_parentheses(s):
    """LeetCode 20. Given a string of only '()[]{}' return True if brackets are
    closed by the same type and in the correct order. Empty string is valid.

    '()[]{}' -> True    '(]' -> False    '([)]' -> False    '{[]}' -> True
    Hint: push openers; on a closer, the top of the stack must be its partner.
    Time O(n), Space O(n).
    """
    ...


def remove_adjacent_duplicates(s):
    """LeetCode 1047. Repeatedly remove pairs of equal ADJACENT characters until
    none remain; return the result.

    'abbaca' -> 'ca'    'azxxzy' -> 'ay'    'aaa' -> 'a'    '' -> ''
    Hint: compare each char with the top of the stack.
    Time O(n), Space O(n).
    """
    ...


class MinStack:
    """LeetCode 155. Stack supporting push, pop, top and get_min, all in O(1).

    s = MinStack(); s.push(-2); s.push(0); s.push(-3)
    s.get_min() -> -3;  s.pop();  s.top() -> 0;  s.get_min() -> -2
    Hint: store (value, min_so_far) pairs, or a second stack of minimums.
    You may assume pop/top/get_min are only called on a non-empty stack.
    """

    def __init__(self):
        ...

    def push(self, val):
        ...

    def pop(self):
        """Remove the top element (return value is ignored)."""
        ...

    def top(self):
        """Return the top element."""
        ...

    def get_min(self):
        """Return the minimum element currently in the stack."""
        ...


def eval_rpn(tokens):
    """LeetCode 150. Evaluate a Reverse Polish Notation expression.
    tokens is a list of strings: integers (possibly negative) and + - * /.
    Division truncates toward zero.

    ['2','1','+','3','*'] -> 9      ['4','13','5','/','+'] -> 6
    ['10','6','9','3','+','-11','*','/','*','17','+','5','+'] -> 22
    ['-7','2','/'] -> -3  (NOT -4)
    Hint: for a - b, b is popped first. Use int(a / b) for truncation.
    Time O(n), Space O(n).
    """
    ...


def daily_temperatures(temps):
    """LeetCode 739. For each day, return how many days until a warmer
    temperature; 0 if there is none.

    [73,74,75,71,69,72,76,73] -> [1,1,4,2,1,1,0,0]
    [30,40,50,60] -> [1,1,1,0]      [30] -> [0]      [] -> []
    Hint: monotonic (decreasing) stack of indices.
    Time O(n), Space O(n).
    """
    ...


def next_greater_circular(nums):
    """LeetCode 503. For each element, find the next strictly greater element,
    searching circularly (wrap around). Use -1 if none exists.

    [1,2,1] -> [2,-1,2]      [1,2,3,4,3] -> [2,3,4,-1,4]      [5] -> [-1]
    Hint: loop i over range(2*n), use nums[i % n], only push when i < n.
    Time O(n), Space O(n).
    """
    ...


def simplify_path(path):
    """LeetCode 71. Convert an absolute Unix path to its canonical form.
    '.' = current dir, '..' = parent dir (no-op at root), multiple slashes
    collapse, no trailing slash (except root '/').

    '/home/' -> '/home'      '/../' -> '/'      '/home//foo/' -> '/home/foo'
    '/a/./b/../../c/' -> '/c'      '/a/../../b' -> '/b'      '/...' -> '/...'
    Hint: split on '/', handle '', '.', '..' specially.
    Time O(n), Space O(n).
    """
    ...


def asteroid_collision(asteroids):
    """LeetCode 735. Each integer is an asteroid: |value| = size, sign =
    direction (positive moves right, negative left). All move at the same speed.
    When two meet, the smaller explodes; equal sizes both explode. Asteroids
    moving the same direction never meet. Return the survivors in order.

    [5,10,-5] -> [5,10]      [8,-8] -> []      [10,2,-5] -> [10]
    [-2,-1,1,2] -> [-2,-1,1,2]      [] -> []
    Hint: collisions only happen when top > 0 and the new one < 0.
    Time O(n), Space O(n).
    """
    ...


def decode_string(s):
    """LeetCode 394. Decode k[encoded] -> encoded repeated k times. k can have
    multiple digits and groups can be nested. Input is always valid.

    '3[a]2[bc]' -> 'aaabcbc'      '3[a2[c]]' -> 'accaccacc'
    '2[abc]3[cd]ef' -> 'abcabccdcdcdef'      'abc' -> 'abc'      '10[a]' -> 'aaaaaaaaaa'
    Hint: on '[' push (current_string, k); on ']' pop and combine.
    Time O(output length), Space O(output length).
    """
    ...


def largest_rectangle_in_histogram(heights):
    """LeetCode 84 (Hard). Given bar heights (each bar width 1), return the area
    of the largest rectangle in the histogram.

    [2,1,5,6,2,3] -> 10      [2,4] -> 4      [] -> 0      [5] -> 5
    [1,1,1,1] -> 4           [6,5,4,3,2,1] -> 12
    Hint: increasing stack of indices; when a shorter bar arrives, pop and
    compute width using the new top of the stack. Append a 0 sentinel.
    Time O(n), Space O(n).
    """
    ...


def trap_rain_water(height):
    """LeetCode 42 (Hard). Given elevation heights (width 1 each), return how
    much water is trapped after raining. Solve it with a monotonic stack
    (a two-pointer O(1)-space solution also exists; try both).

    [0,1,0,2,1,0,1,3,2,1,2,1] -> 6      [4,2,0,3,2,5] -> 9
    [] -> 0      [3] -> 0      [1,2,3] -> 0
    Time O(n), Space O(n) (stack) or O(1) (two pointers).
    """
    ...
