import random

from exercises import *


# ---------- Trie ----------
def test_trie_basic():
    t = Trie()
    t.insert("apple")
    assert t.search("apple") is True
    assert t.search("app") is False
    assert t.starts_with("app") is True
    t.insert("app")
    assert t.search("app") is True


def test_trie_empty_and_missing():
    t = Trie()
    assert t.search("a") is False
    assert t.starts_with("a") is False
    t.insert("abc")
    assert t.search("abd") is False
    assert t.search("abcd") is False
    assert t.starts_with("abcd") is False
    assert t.starts_with("b") is False


def test_trie_duplicates_and_shared_prefix():
    t = Trie()
    for w in ["car", "card", "care", "car", "cat"]:
        t.insert(w)
    assert t.search("car") and t.search("card") and t.search("care") and t.search("cat")
    assert not t.search("ca")
    assert t.starts_with("ca") and t.starts_with("car") and not t.starts_with("cab")


def test_trie_independent_instances():
    a, b = Trie(), Trie()
    a.insert("x")
    assert a.search("x") is True
    assert b.search("x") is False


def test_trie_random_vs_set():
    rnd = random.Random(1)
    words = {"".join(rnd.choice("ab") for _ in range(rnd.randint(1, 6))) for _ in range(30)}
    t = Trie()
    for w in words:
        t.insert(w)
    for _ in range(200):
        q = "".join(rnd.choice("ab") for _ in range(rnd.randint(1, 7)))
        assert t.search(q) == (q in words)
        assert t.starts_with(q) == any(w.startswith(q) for w in words)


# ---------- longest_common_prefix ----------
def test_lcp():
    assert longest_common_prefix(["flower", "flow", "flight"]) == "fl"
    assert longest_common_prefix(["dog", "racecar", "car"]) == ""
    assert longest_common_prefix([]) == ""
    assert longest_common_prefix(["alone"]) == "alone"
    assert longest_common_prefix(["", "abc"]) == ""
    assert longest_common_prefix(["abc", "abc", "abc"]) == "abc"
    assert longest_common_prefix(["ab", "abc"]) == "ab"
    assert longest_common_prefix(["a", "b"]) == ""


# ---------- replace_words ----------
def test_replace_words():
    assert replace_words(["cat", "bat", "rat"], "the cattle was rattled by the battery") == \
        "the cat was rat by the bat"
    assert replace_words(["a", "b", "c"], "aadsfasf absbs bbab cadsfafs") == "a a b c"


def test_replace_words_shortest_root():
    assert replace_words(["catt", "cat", "bat", "rat"], "the cattle was rattled by the battery") == \
        "the cat was rat by the bat"
    assert replace_words(["ab", "abc"], "abcd") == "ab"


def test_replace_words_edges():
    assert replace_words([], "hello world") == "hello world"
    assert replace_words(["x"], "hello") == "hello"
    assert replace_words(["hello"], "hello") == "hello"
    assert replace_words(["hello"], "hell") == "hell"
    assert replace_words(["he"], "") == ""


# ---------- WordDictionary ----------
def test_word_dictionary_basic():
    d = WordDictionary()
    for w in ["bad", "dad", "mad"]:
        d.add_word(w)
    assert d.search("pad") is False
    assert d.search("bad") is True
    assert d.search(".ad") is True
    assert d.search("b..") is True
    assert d.search("b.") is False
    assert d.search("b...") is False


def test_word_dictionary_edges():
    d = WordDictionary()
    assert d.search("a") is False
    assert d.search(".") is False
    d.add_word("a")
    d.add_word("ab")
    assert d.search("a") is True
    assert d.search(".") is True
    assert d.search("..") is True
    assert d.search("a.") is True
    assert d.search("...") is False
    assert d.search("..b") is False
    assert d.search(".b") is True


def test_word_dictionary_prefix_not_word():
    d = WordDictionary()
    d.add_word("apple")
    assert d.search("app") is False
    assert d.search("app..") is True
    assert d.search("a....") is True
    assert d.search(".....") is True


# ---------- MapSum ----------
def test_map_sum_basic():
    m = MapSum()
    m.insert("apple", 3)
    assert m.sum("ap") == 3
    m.insert("app", 2)
    assert m.sum("ap") == 5


def test_map_sum_overwrite():
    m = MapSum()
    m.insert("apple", 3)
    m.insert("app", 2)
    m.insert("apple", 5)
    assert m.sum("ap") == 7
    assert m.sum("apple") == 5
    assert m.sum("app") == 7


def test_map_sum_missing_and_exact():
    m = MapSum()
    assert m.sum("a") == 0
    m.insert("abc", 10)
    assert m.sum("abcd") == 0
    assert m.sum("b") == 0
    assert m.sum("abc") == 10
    m.insert("abc", 1)
    assert m.sum("a") == 1


def test_map_sum_random_vs_brute():
    rnd = random.Random(7)
    m = MapSum()
    ref = {}
    for _ in range(100):
        k = "".join(rnd.choice("abc") for _ in range(rnd.randint(1, 4)))
        v = rnd.randint(-5, 20)
        m.insert(k, v)
        ref[k] = v
        p = "".join(rnd.choice("abc") for _ in range(rnd.randint(1, 3)))
        assert m.sum(p) == sum(x for key, x in ref.items() if key.startswith(p))


# ---------- longest_word ----------
def test_longest_word():
    assert longest_word(["w", "wo", "wor", "worl", "world"]) == "world"
    assert longest_word(["a", "banana", "app", "appl", "ap", "apply", "apple"]) == "apple"
    assert longest_word(["b", "c"]) == "b"
    assert longest_word([]) == ""
    assert longest_word(["abc", "ab"]) == ""
    assert longest_word(["yo", "ew", "fc", "zrc", "yodn", "fcm", "qm", "qmo", "fcmz", "z", "ewq",
                         "yod", "ewqz", "y"]) == "yodn"


def test_longest_word_ties_and_gaps():
    assert longest_word(["a", "b", "ab", "ba"]) == "ab"
    assert longest_word(["z", "zz", "a", "aa"]) == "aa"
    assert longest_word(["a", "abc"]) == "a"  # "ab" missing
    assert longest_word(["x"]) == "x"


# ---------- suggested_products ----------
def test_suggested_products():
    products = ["mobile", "mouse", "moneypot", "monitor", "mousepad"]
    assert suggested_products(products, "mouse") == [
        ["mobile", "moneypot", "monitor"],
        ["mobile", "moneypot", "monitor"],
        ["mouse", "mousepad"],
        ["mouse", "mousepad"],
        ["mouse", "mousepad"],
    ]


def test_suggested_products_more():
    assert suggested_products(["havana"], "havana") == [["havana"]] * 6
    assert suggested_products(["bags", "baggage", "banner", "box", "cloths"], "bags") == [
        ["baggage", "bags", "banner"],
        ["baggage", "bags", "banner"],
        ["baggage", "bags"],
        ["bags"],
    ]
    assert suggested_products(["havana"], "tatiana") == [[]] * 7


def test_suggested_products_edges():
    assert suggested_products([], "abc") == [[], [], []]
    assert suggested_products(["a", "b"], "") == []
    assert suggested_products(["abcd", "abc", "ab", "a"], "abcd") == [
        ["a", "ab", "abc"], ["ab", "abc", "abcd"], ["abc", "abcd"], ["abcd"]]


# ---------- StreamChecker ----------
def test_stream_checker_basic():
    sc = StreamChecker(["cd", "f", "kl"])
    out = [sc.query(c) for c in "abcdefghijkl"]
    assert out == [False, False, False, True, False, True, False, False, False, False, False, True]


def test_stream_checker_overlapping_and_long():
    sc = StreamChecker(["abc", "bc", "c", "xabcd"])
    assert [sc.query(c) for c in "xabcd"] == [False, False, False, True, True]
    sc = StreamChecker(["abc", "xabcd"])
    assert [sc.query(c) for c in "xabcd"] == [False, False, False, True, True]


def test_stream_checker_prefix_word_and_repeats():
    sc = StreamChecker(["aa"])
    assert [sc.query("a") for _ in range(4)] == [False, True, True, True]
    sc = StreamChecker(["a", "aaa"])
    assert sc.query("b") is False
    assert sc.query("a") is True


def test_stream_checker_random_vs_brute():
    rnd = random.Random(3)
    words = ["".join(rnd.choice("ab") for _ in range(rnd.randint(1, 5))) for _ in range(6)]
    sc = StreamChecker(words)
    s = ""
    for _ in range(200):
        c = rnd.choice("ab")
        s += c
        assert sc.query(c) == any(s.endswith(w) for w in words)


# ---------- find_maximum_xor ----------
def test_max_xor_examples():
    assert find_maximum_xor([3, 10, 5, 25, 2, 8]) == 28
    assert find_maximum_xor([14, 70, 53, 83, 49, 91, 36, 80, 92, 51, 66, 70]) == 127
    assert find_maximum_xor([8]) == 0
    assert find_maximum_xor([]) == 0
    assert find_maximum_xor([0, 0]) == 0
    assert find_maximum_xor([1, 2]) == 3
    assert find_maximum_xor([2 ** 31 - 1, 0]) == 2 ** 31 - 1


def test_max_xor_random_vs_brute():
    rnd = random.Random(5)
    for _ in range(30):
        nums = [rnd.randint(0, 2 ** 20) for _ in range(rnd.randint(1, 25))]
        expect = max(a ^ b for a in nums for b in nums)
        assert find_maximum_xor(nums) == expect


# ---------- find_words ----------
def test_find_words_example():
    board = [list("oaan"), list("etae"), list("ihkr"), list("iflv")]
    assert sorted(find_words(board, ["oath", "pea", "eat", "rain"])) == ["eat", "oath"]
    assert board == [list("oaan"), list("etae"), list("ihkr"), list("iflv")]  # restored


def test_find_words_none_and_empty():
    assert find_words([["a", "b"], ["c", "d"]], ["abcd"]) == []
    assert find_words([["a"]], []) == []
    assert find_words([], ["a"]) == []


def test_find_words_single_cell_and_reuse():
    assert find_words([["a"]], ["a"]) == ["a"]
    assert find_words([["a"]], ["aa"]) == []  # a cell cannot be reused
    assert find_words([["a", "a"]], ["aaa"]) == []
    assert sorted(find_words([["a", "a"]], ["aa"])) == ["aa"]


def test_find_words_duplicates_and_prefixes():
    board = [list("abc"), list("def"), list("ghi")]
    res = find_words(board, ["abc", "abc", "ab", "abcfe", "adg", "x"])
    assert sorted(res) == ["ab", "abc", "abcfe", "adg"]


def test_find_words_snake_path():
    board = [list("abe"), list("cfd"), list("gih")]
    # a-b-e-d-h-i-g-c is a valid snake through 8 cells; a-b-e-d-h-i-g-c-f uses all 9
    assert sorted(find_words(board, ["abedhigc", "abedhigcf", "abedhigcfa"])) == ["abedhigc", "abedhigcf"]


def test_find_words_large_prune():
    board = [["a"] * 12 for _ in range(12)]
    words = ["a" * 5, "a" * 6, "a" * 13]
    res = find_words(board, words)
    assert sorted(res) == sorted(words)
