# Week 16: Tries (prefix trees)

## 1. Concept
A **trie** stores a set of strings as a tree where each edge is one character and
each root-to-node path spells a prefix. A flag on a node marks "a word ends here".
All words sharing a prefix share the same path, so prefix questions become
"walk down the tree".

```
insert "car", "card", "cat"
root - c - a - r*  - d*
           \ t*          (* = end of word)
```

Compared to a hash set of words:
| Operation            | Hash set        | Trie          |
|----------------------|-----------------|---------------|
| exact lookup         | O(L) (hashing)  | O(L)          |
| "any word starting with p?" | O(N * L) | O(len(p))   |
| enumerate words with prefix | O(N * L) | O(len(p) + output) |
| wildcard / char-by-char pruning | hard | natural (DFS on tree) |

## 2. How to recognize the pattern
- "Starts with", "prefix", "autocomplete", "dictionary of words".
- Many words + many queries over the same set.
- Matching words on a grid/board (Word Search II): prune DFS when no word has this prefix.
- Streaming characters, checking suffixes (reverse the words).
- Maximum XOR / bitwise problems: a **binary trie** over bits, choose the opposite bit greedily.
- Wildcards (`.`): DFS branching over children.

## 3. Template code
Dict-of-dicts trie (fastest to write on a whiteboard):
```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True            # end-of-word marker (not a lowercase letter)

    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and "$" in node

    def starts_with(self, prefix):
        return self._walk(prefix) is not None
```
Class-based node (use when nodes carry extra data such as counts or top-3 lists):
```python
class TrieNode:
    __slots__ = ("children", "end", "count")
    def __init__(self):
        self.children = {}
        self.end = False
        self.count = 0              # words passing through this node
```
Binary trie for XOR: children keyed by 0/1, insert bits 30..0 of each number.

Trie + DFS on a grid (Word Search II): build one trie of all words, DFS from every
cell moving to `node[board[r][c]]`, store the full word at the terminal node, and
delete finished branches to prune.

## 4. Complexity
- Build: O(total characters of all words). Space O(total characters) worst case
  (alphabet-size factor if you use arrays of 26 children instead of dicts).
- Insert / search / prefix: O(L).
- Wildcard search: O(L) typical, O(26^dots * L) worst case.
- Word Search II: O(M * N * 3^(L-1)) worst case, pruning makes it practical.

## 5. Common mistakes
- Forgetting the end-of-word marker: `search("app")` returns True just because "apple" exists.
- Using `"$"` as a key then iterating children for `.` wildcards: skip the marker key.
- Overwriting vs adding in `MapSum`: on re-insert, add the **delta**, not the new value.
- Returning duplicates in Word Search II: pop the word from the node when found.
- Forgetting to restore the board cell after DFS (backtracking).
- Reaching for a trie when sorting + binary search is simpler (autocomplete with top-3).
- Mutable default / shared node bug: `[{}] * 26` shares one dict. Use a comprehension.
- Recursion depth: a trie over long strings (10^5 chars) should be iterative.

## 6. Interview tips
- Say: "Words share prefixes, so a trie gives O(L) per query regardless of how many words."
- State the trade-off: tries use more memory than a hash set; mention compressed tries (radix) if asked.
- Always ask: alphabet (lowercase only? unicode?), case sensitivity, duplicates, empty string.
- Ask if the trie must support delete; the usual approach is to decrement counts or prune childless nodes.
- For Google-style follow-ups: "what if the dictionary does not fit in memory?" (shard by prefix, on-disk structure),
  "return top-k by frequency" (store top-k / counts per node).
- Reverse words for suffix problems (StreamChecker); mention Aho-Corasick for many-pattern matching in a stream.

## Your task
Fill in `exercises.py`, then run the tests from this directory with `../../.venv/bin/pytest` (see PROGRESS.md).
