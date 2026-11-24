"""Week 1 exercises: Big-O and complexity analysis. Replace each `...` with your code.

Pay attention to the required complexity in each docstring; the tests use
large-ish inputs, so a too-slow solution will take forever or time out.
"""


def contains_duplicate(nums):
    """Return True if any value appears at least twice in nums.

    Example: [1, 2, 3, 1] -> True; [1, 2, 3] -> False; [] -> False
    Brute force is O(n^2). Target: O(n) time, O(n) space.
    Hint: a set.
    """
    ...


def dedupe_preserve_order(items):
    """Return a new list with duplicates removed, keeping first occurrences in order.

    Example: [3, 1, 3, 2, 1] -> [3, 1, 2]
    Target: O(n) time, O(n) space. Hint: `x in list` is O(n); use a set for seen.
    """
    ...


def common_elements(a, b):
    """Return a sorted list of the distinct values present in both lists.

    Example: [4, 1, 2, 2], [2, 2, 4, 9] -> [2, 4]
    Target: O(n + m + k log k) where k is the result size. Hint: set intersection.
    """
    ...


def first_unique_char(s):
    """Return the index of the first character that appears exactly once, else -1.

    Example: "leetcode" -> 0; "loveleetcode" -> 2; "aabb" -> -1
    Target: O(n) time, O(1) space (alphabet is bounded) / O(k) for k distinct chars.
    Hint: count first (dict / Counter), then scan again.
    """
    ...


def is_anagram(s, t):
    """Return True if t is a rearrangement of s (same letters, same counts).

    Example: "anagram", "nagaram" -> True; "rat", "car" -> False
    Target: O(n) time. (Sorting both is O(n log n): works, but can you beat it?)
    """
    ...


def build_csv_line(values):
    """Return the values converted to str and joined with commas, no trailing comma.

    Example: [1, "a", 2.5] -> "1,a,2.5"; [] -> ""
    Target: O(total length). Do NOT build the answer with repeated `+=` in a loop;
    use "".join / ",".join over a list of pieces.
    """
    ...


def rotate_left(nums, k):
    """Return a NEW list: nums rotated left by k positions (k may exceed len(nums)).

    Example: [1, 2, 3, 4, 5], 2 -> [3, 4, 5, 1, 2]; [1, 2], 5 -> [2, 1]; [] -> []
    Target: O(n) time, O(n) space. Hint: k %= n, then slicing is fine here.
    """
    ...


def merge_sorted(a, b):
    """Merge two ascending-sorted lists into one sorted list.

    Example: [1, 4, 7], [2, 3, 9] -> [1, 2, 3, 4, 7, 9]
    Target: O(n + m) time. Do NOT concatenate and sort (that is O((n+m) log(n+m))).
    Hint: two indices. Do not use list.pop(0) (O(n) each!).
    """
    ...


def fast_power(x, n):
    """Return x ** n for integer n >= 0 WITHOUT using ** or pow().

    Example: (2, 10) -> 1024; (5, 0) -> 1; (3, 1) -> 3
    Target: O(log n) multiplications. Hint: square x and halve n each step.
    """
    ...


def is_prime(n):
    """Return True if n is a prime number (n >= 0 integer; 0 and 1 are not prime).

    Example: 2 -> True; 15 -> False; 97 -> True; 1 -> False
    Target: O(sqrt n). Hint: only test divisors up to isqrt(n).
    """
    ...


def max_subarray_sum(nums):
    """Return the largest sum of any non-empty contiguous subarray (Kadane's algorithm).

    Example: [-2, 1, -3, 4, -1, 2, 1, -5, 4] -> 6 (subarray [4, -1, 2, 1]); [-3, -1] -> -1
    Brute force is O(n^2) (or O(n^3)). Target: O(n) time, O(1) space.
    Hint: best sum ending here = max(x, x + best ending at previous index).
    """
    ...


def count_pairs_with_sum(nums, target):
    """Return the number of index pairs (i, j), i < j, with nums[i] + nums[j] == target.

    Example: [1, 5, 3, 3, 3], 6 -> 4 (1+5 and three 3+3 pairs); [] -> 0
    Brute force O(n^2). Target: O(n) time, O(n) space.
    Hint: for each x, add how many earlier values equal target - x, then record x.
    """
    ...


def analyze(snippet):
    """ANALYSIS: return the time complexity (string) of the named snippet, one of
    "O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(2^n)".

    Snippets (n = len(nums) unless stated):
      "a": for x in nums: total += x
      "b": for i in range(n): for j in range(n): count += 1
      "c": i = n; while i > 1: i //= 2
      "d": sorted(nums)
      "e": def f(k): return 1 if k < 2 else f(k - 1) + f(k - 2)    (called as f(n))
      "f": nums[len(nums) // 2]
      "g": for i in range(n): for j in range(i): count += 1
      "h": for x in nums: if x in nums_list_copy: ...   (nums_list_copy is a list)
      "i": for i in range(n):            # outer loop over the input
               k = n
               while k > 1: k //= 2      # inner loop halves k each pass
    """
    ...
