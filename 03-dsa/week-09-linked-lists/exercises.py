"""Week 9 exercises: linked lists. Replace each `...` with your code.

Run tests from the repo root:  .venv/bin/pytest 03-dsa/week-09-linked-lists -q
Lists are given by their head node (None = empty list). Prefer iterative
solutions: inputs can have 100,000 nodes, which would overflow Python recursion.
"""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head):
    """LeetCode 206. Reverse a singly linked list and return the new head.

    1->2->3->4->5  ->  5->4->3->2->1      1->2 -> 2->1      [] -> []   (None -> None)
    Hint: three pointers prev / cur / nxt.
    Time O(n), Space O(1).
    """
    ...


def middle_node(head):
    """LeetCode 876. Return the middle node of the list (the node itself, not
    its value). With two middle nodes return the SECOND one.

    1->2->3->4->5 -> node 3      1->2->3->4 -> node 3      1 -> node 1
    Hint: slow moves 1 step, fast moves 2.
    Time O(n), Space O(1). Assume the list is non-empty.
    """
    ...


def merge_two_lists(l1, l2):
    """LeetCode 21. Merge two sorted lists into one sorted list by splicing the
    existing nodes together. Return the head.

    1->2->4 and 1->3->4 -> 1->1->2->3->4->4      [] and [] -> []      [] and 0 -> 0
    Hint: dummy head + tail pointer. Keep it stable (take l1 on ties).
    Time O(n + m), Space O(1).
    """
    ...


def has_cycle(head):
    """LeetCode 141. Return True if the list contains a cycle (some node's
    `next` points back to an earlier node), else False.

    3->2->0->-4->(back to 2) -> True      1->2 -> False      None -> False
    Hint: Floyd's tortoise and hare. Do not use a set (aim for O(1) space).
    Time O(n), Space O(1).
    """
    ...


def is_palindrome_list(head):
    """LeetCode 234. Return True if the list reads the same forwards and
    backwards.

    1->2->2->1 -> True      1->2 -> False      1 -> True      None -> True
    1->2->3->2->1 -> True
    Hint: find the middle, reverse the second half, compare. Aim for O(1) space
    (you may restore the list afterwards, but it is not required).
    Time O(n), Space O(1).
    """
    ...


def remove_nth_from_end(head, n):
    """LeetCode 19. Remove the n-th node from the END of the list (1-indexed)
    and return the head. 1 <= n <= length.

    1->2->3->4->5, n=2 -> 1->2->3->5      1, n=1 -> None      1->2, n=1 -> 1
    1->2, n=2 -> 2
    Hint: dummy node + two pointers separated by n nodes. One pass.
    Time O(n), Space O(1).
    """
    ...


def detect_cycle_start(head):
    """LeetCode 142. Return the node where the cycle begins, or None if there is
    no cycle (return the node object itself, not its value).

    3->2->0->-4->(back to 2) -> node 2      1->2->(back to 1) -> node 1
    1->2 -> None      None -> None      1->(self loop) -> node 1
    Hint: Floyd phase 1 finds a meeting point; phase 2 restarts one pointer at
    head and moves both one step at a time until they meet.
    Time O(n), Space O(1).
    """
    ...


def add_two_numbers(l1, l2):
    """LeetCode 2. Two non-empty lists represent non-negative integers with the
    digits stored in REVERSE order (least significant digit first). Return the
    sum as a list in the same format.

    2->4->3 + 5->6->4 -> 7->0->8   (342 + 465 = 807)
    0 + 0 -> 0      9->9->9->9 + 1 -> 0->0->0->0->1      1 + 9->9 -> 0->0->1
    Hint: dummy head, carry; loop while l1 or l2 or carry.
    Time O(max(n, m)), Space O(1) extra (the output list does not count).
    """
    ...


def reorder_list(head):
    """LeetCode 143. Reorder L0->L1->...->Ln-1->Ln into
    L0->Ln->L1->Ln-1->L2->Ln-2->... IN PLACE. Return nothing (modify the list).

    1->2->3->4 -> 1->4->2->3      1->2->3->4->5 -> 1->5->2->4->3
    1 -> 1      1->2 -> 1->2      None -> None
    Hint: find the middle, reverse the second half, then interleave the halves.
    Remember to cut the first half (`mid.next = None`) or you create a cycle.
    Time O(n), Space O(1).
    """
    ...


def reverse_k_group(head, k):
    """LeetCode 25 (Hard). Reverse the nodes of the list k at a time and return
    the head. If the number of remaining nodes is less than k, leave them as is.
    Only node links may change (not values). k >= 1.

    1->2->3->4->5, k=2 -> 2->1->4->3->5      1->2->3->4->5, k=3 -> 3->2->1->4->5
    1->2->3, k=1 -> 1->2->3      1->2, k=5 -> 1->2      None -> None
    Hint: check k nodes exist, reverse that segment, connect it to the previous
    group's tail and recurse/loop on the rest. Use a dummy node.
    Time O(n), Space O(1).
    """
    ...


def merge_k_sorted_lists(lists):
    """LeetCode 23 (Hard). Merge k sorted linked lists into one sorted list and
    return its head. `lists` may be empty or contain None entries.

    [1->4->5, 1->3->4, 2->6] -> 1->1->2->3->4->4->5->6      [] -> None      [None] -> None
    Hint: min-heap of (value, list_index, node) -- the index breaks ties so Python
    never compares ListNodes. Or divide and conquer with merge_two_lists logic.
    Time O(N log k), Space O(k).
    """
    ...
