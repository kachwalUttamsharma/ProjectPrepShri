"""Week 2 exercises: arrays and strings. Replace each `...` with your code.

Several problems say "in place": mutate the given list (don't just return a new one).
"""


def reverse_string(chars):
    """Reverse the list of characters IN PLACE. Return None.

    Example: ["h", "e", "l", "l", "o"] -> ["o", "l", "l", "e", "h"]
    Target: O(n) time, O(1) space. Hint: swap from both ends.
    """
    ...


def move_zeroes(nums):
    """Move all 0s to the end IN PLACE, keeping the order of the non-zero values. Return None.

    Example: [0, 1, 0, 3, 12] -> [1, 3, 12, 0, 0]
    Target: O(n) time, O(1) space. Hint: read/write pointer, then fill zeros.
    """
    ...


def is_palindrome(s):
    """Return True if s reads the same forwards and backwards, considering only
    alphanumeric characters and ignoring case.

    Example: "A man, a plan, a canal: Panama" -> True; "race a car" -> False; "" -> True
    Target: O(n) time, O(1) space (two pointers; don't build a cleaned copy if you can avoid it).
    Hint: str.isalnum(), str.lower().
    """
    ...


def longest_common_prefix(strs):
    """Return the longest common prefix of all strings ("" if none or list is empty).

    Example: ["flower", "flow", "flight"] -> "fl"; ["dog", "car"] -> ""; ["a"] -> "a"
    Target: O(total characters), O(1) extra space.
    """
    ...


def remove_duplicates_sorted(nums):
    """Given a sorted list, remove duplicates IN PLACE so each value appears once.
    Return the new length k; the first k items of nums must be the unique values in order.

    Example: [0, 0, 1, 1, 1, 2] -> returns 3, nums[:3] == [0, 1, 2]
    Target: O(n) time, O(1) space. Hint: read/write pointer.
    """
    ...


def rotate_array(nums, k):
    """Rotate nums to the RIGHT by k steps IN PLACE (k may exceed len). Return None.

    Example: [1, 2, 3, 4, 5, 6, 7], k=3 -> [5, 6, 7, 1, 2, 3, 4]
    Target: O(n) time, O(1) space. Hint: reverse all, reverse first k, reverse the rest.
    """
    ...


def product_except_self(nums):
    """Return a list where out[i] is the product of all nums except nums[i].
    No division allowed. Zeros must work.

    Example: [1, 2, 3, 4] -> [24, 12, 8, 6]; [0, 2, 3] -> [6, 0, 0]
    Target: O(n) time, O(1) extra space (the output list doesn't count).
    Hint: prefix products pass, then a suffix products pass.
    """
    ...


def merge_sorted_array(nums1, m, nums2, n):
    """nums1 has length m + n; its first m items are sorted and the last n are 0 padding.
    nums2 has n sorted items. Merge nums2 into nums1 IN PLACE so nums1 is sorted. Return None.

    Example: nums1=[1, 2, 3, 0, 0, 0], m=3, nums2=[2, 5, 6], n=3 -> nums1=[1, 2, 2, 3, 5, 6]
    Target: O(m + n) time, O(1) space. Hint: fill from the BACK with three pointers.
    """
    ...


def compress_string(chars):
    """Compress the list of characters IN PLACE using run-length encoding and return
    the new length. For each run of a repeated char: write the char, then the count's
    digits if count > 1. After the call, chars[:returned_length] holds the result.

    Example: ["a","a","b","b","c","c","c"] -> returns 6, chars[:6] == ["a","2","b","2","c","3"]
             ["a"] -> 1;  ["a"]*12 -> returns 3, chars[:3] == ["a","1","2"]
    Target: O(n) time, O(1) extra space. Hint: read pointer scans runs, write pointer emits.
    """
    ...


def spiral_order(matrix):
    """Return all elements of an m x n matrix in clockwise spiral order.

    Example: [[1,2,3],[4,5,6],[7,8,9]] -> [1,2,3,6,9,8,7,4,5]
    Target: O(m*n) time. Hint: shrink top/bottom/left/right boundaries; beware single row/column.
    """
    ...


def rotate_image(matrix):
    """Rotate an n x n matrix 90 degrees CLOCKWISE IN PLACE. Return None.

    Example: [[1,2,3],[4,5,6],[7,8,9]] -> [[7,4,1],[8,5,2],[9,6,3]]
    Target: O(n^2) time, O(1) space. Hint: transpose, then reverse each row.
    """
    ...


def longest_palindromic_substring(s):
    """Return the longest palindromic substring of s. If several have the same
    maximal length, ANY one of them is accepted.

    Example: "babad" -> "bab" or "aba"; "cbbd" -> "bb"; "a" -> "a"
    Target: O(n^2) time, O(1) space. Hint: expand around each of the 2n-1 centers.
    """
    ...
