"""Week 16 exercises: Tries (prefix trees). Replace each `...` with your code.

Problems are ordered easy -> hard. Tip: a dict-of-dicts trie is fastest to
write in an interview: node = {}, children keyed by char, "$" marks word end.
"""
from bisect import bisect_left

class Trie:
    """LeetCode 208. Implement a prefix tree.

    Trie()                 creates an empty trie.
    insert(word)           adds word (lowercase letters).
    search(word) -> bool   True only if word was inserted as a whole word.
    starts_with(prefix) -> bool   True if any inserted word begins with prefix.

    Example:
        t = Trie(); t.insert("apple")
        t.search("apple") -> True;  t.search("app") -> False
        t.starts_with("app") -> True; t.insert("app"); t.search("app") -> True

    Expected: O(L) per operation, L = length of the string.
    Hint: node = {}; walk with node.setdefault(ch, {}); mark the end with "$".
    A shared private helper that walks a string (return node or None) removes
    duplication between search and starts_with.
    """

    def __init__(self):
        """Create the root node."""
        ...

    def insert(self, word):
        """Insert word."""
        ...

    def _walk(self, s):
        ...

    def search(self, word):
        """Return True if word is in the trie as a complete word."""
        ...

    def starts_with(self, prefix):
        """Return True if any word in the trie starts with prefix."""
        ...

def longest_common_prefix(strs):
    """LeetCode 14. Return the longest common prefix of all strings ("" if none).

    Examples:
        ["flower","flow","flight"] -> "fl"
        ["dog","racecar","car"]    -> ""
        []                         -> ""
        ["alone"]                  -> "alone"

    Expected: O(total characters). O(1) extra space is possible without a trie.
    Hint: compare column by column against strs[0]; or use min/max of the list
    (lexicographic extremes) and compare only those two strings.
    """
    ...

def replace_words(dictionary, sentence):
    """LeetCode 648. Replace every word in sentence with its shortest root.

    A root is any word in dictionary that is a prefix of the word. If several
    roots match, use the shortest. Words with no root stay unchanged.

    Example:
        dictionary = ["cat","bat","rat"], sentence = "the cattle was rattled by the battery"
        -> "the cat was rat by the bat"

    Expected: O(D + S) time where D, S are total characters of dictionary / sentence.
    Hint: build a trie of roots; for each word walk the trie and stop at the
    FIRST "$" you meet (that is the shortest root).
    """
    ...

class WordDictionary:
    """LeetCode 211. Add words, search with '.' wildcard (matches any one letter).

    add_word(word)
    search(word) -> bool   word may contain '.'

    Example:
        add_word("bad"); add_word("dad"); add_word("mad")
        search("pad") -> False; search("bad") -> True
        search(".ad") -> True;  search("b..") -> True; search("b.") -> False

    Expected: add O(L); search O(L) typical, O(26^dots * L) worst case.
    Hint: recursive DFS(node, i); on '.', try every child (skip the "$" key!).
    """

    def __init__(self):
        """Create an empty dictionary."""
        ...

    def add_word(self, word):
        """Add word."""
        ...

    def search(self, word):
        """Return True if some added word matches the pattern."""
        ...

class MapSum:
    """LeetCode 677. Map with prefix sums.

    insert(key, val)   sets key -> val (overwrites an existing key!)
    sum(prefix) -> int  sum of values of all keys starting with prefix (0 if none)

    Example:
        insert("apple", 3); sum("ap") -> 3
        insert("app", 2);   sum("ap") -> 5
        insert("apple", 5); sum("ap") -> 7   (apple overwritten: 5 + 2)

    Expected: O(L) per operation.
    Hint: store at each node the running total of the subtree; on overwrite add
    the DELTA (val - old) along the path. Keep a dict key -> old value.
    """

    def __init__(self):
        """Create an empty map."""
        ...

    def insert(self, key, val):
        """Set key to val."""
        ...

    def sum(self, prefix):
        """Return the sum of values of keys starting with prefix."""
        ...

def longest_word(words):
    """LeetCode 720. Longest word buildable one letter at a time.

    Return the longest word in words such that every prefix of it (of length
    1..len-1) is also in words. Ties: lexicographically smallest. Return ""
    if there is none.

    Examples:
        ["w","wo","wor","worl","world"] -> "world"
        ["a","banana","app","appl","ap","apply","apple"] -> "apple"
        ["b","c"] -> "b"
        []        -> ""

    Expected: O(N log N * L) with sorting, or O(total chars) with a trie + DFS.
    Hint: sort the words; a word is buildable if word[:-1] is buildable (or empty).
    """
    ...

def suggested_products(products, search_word):
    """LeetCode 1268. Search suggestions system.

    After each character of search_word is typed, return up to 3 products
    (lexicographically smallest) that share the typed prefix.

    Example:
        products = ["mobile","mouse","moneypot","monitor","mousepad"], search_word = "mouse"
        -> [["mobile","moneypot","monitor"],
            ["mobile","moneypot","monitor"],
            ["mouse","mousepad"],
            ["mouse","mousepad"],
            ["mouse","mousepad"]]

    Expected: O(N log N + W log N) with sort + binary search.
    Hint: sort products once; for each prefix, bisect_left to the first
    candidate, then check the next 3 entries with startswith. Or a trie that
    keeps the 3 smallest words at each node.
    """
    ...

class StreamChecker:
    """LeetCode 1032. Stream of characters.

    StreamChecker(words)   words is a list of non-empty strings.
    query(letter) -> bool  Append letter to the stream. Return True if SOME
                           suffix of the stream equals one of the words.

    Example:
        sc = StreamChecker(["cd","f","kl"])
        query("a") F, "b" F, "c" F, "d" T (suffix "cd"), "e" F, "f" T, "g" F, "h" F, "i" F, "j" F, "k" F, "l" T

    Expected: query O(max word length).
    Hint: insert each word REVERSED into a trie; on query walk backwards from
    the newest letter. Remember the longest word length to bound the walk.
    """

    def __init__(self, words):
        """Build the reversed-word trie."""
        ...

    def query(self, letter):
        """Append letter; return True if a suffix of the stream is a word."""
        ...

def find_maximum_xor(nums):
    """LeetCode 421. Maximum XOR of two numbers in an array.

    Return max(nums[i] ^ nums[j]) over all i, j (i may equal j, giving 0).
    nums are non-negative ints < 2**31. Empty list -> 0.

    Examples:
        [3,10,5,25,2,8] -> 28   (5 ^ 25)
        [14,70,53,83,49,91,36,80,92,51,66,70] -> 127
        [8]  -> 0

    Expected: O(31 * N) time, O(31 * N) space. Beats the O(N^2) brute force.
    Hint: binary trie over bits 30..0. For each number greedily walk to the
    OPPOSITE bit whenever that child exists.
    """
    ...

def find_words(board, words):
    """LeetCode 212. Word Search II.

    Given an m x n board of lowercase letters and a list of words, return all
    words that can be built from sequentially adjacent cells (up/down/left/
    right), using each cell at most once per word. Return each word once, in
    any order. Do not leave the board modified.

    Example:
        board = [["o","a","a","n"],
                 ["e","t","a","e"],
                 ["i","h","k","r"],
                 ["i","f","l","v"]]
        words = ["oath","pea","eat","rain"]  -> ["eat","oath"] (any order)

    Expected: O(m * n * 4 * 3^(L-1)) worst case, but trie pruning makes it fast.
    Hint: build ONE trie of all words, DFS from every cell following trie
    children; store the full word at the terminal node; when found, remove it
    (pop) to avoid duplicates; mark visited cells temporarily (e.g. "#").
    Pruning empty trie branches after a hit is the classic optimisation.
    """
    ...
