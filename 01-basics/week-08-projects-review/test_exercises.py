import json

import pytest
from exercises import *


# ----------------------------- Project A: todo -----------------------------


def test_todo_add_task():
    tasks = []
    t = add_task(tasks, "  buy milk ")
    assert t == {"id": 1, "title": "buy milk", "done": False}
    assert tasks == [t]
    t2 = add_task(tasks, "call mom")
    assert t2["id"] == 2
    assert len(tasks) == 2


def test_todo_add_task_blank_raises():
    tasks = []
    with pytest.raises(ValueError):
        add_task(tasks, "")
    with pytest.raises(ValueError):
        add_task(tasks, "   ")
    assert tasks == []


def test_todo_ids_after_removal():
    tasks = []
    add_task(tasks, "a")
    add_task(tasks, "b")
    add_task(tasks, "c")
    remove_task(tasks, 3)
    assert add_task(tasks, "d")["id"] == 3  # max id + 1
    remove_task(tasks, 1)
    assert add_task(tasks, "e")["id"] == 4  # does not reuse ids below max


def test_todo_complete_task():
    tasks = []
    add_task(tasks, "a")
    add_task(tasks, "b")
    complete_task(tasks, 2)
    assert [t["done"] for t in tasks] == [False, True]
    with pytest.raises(ValueError, match="no such task"):
        complete_task(tasks, 99)


def test_todo_remove_task():
    tasks = []
    add_task(tasks, "a")
    add_task(tasks, "b")
    remove_task(tasks, 1)
    assert [t["title"] for t in tasks] == ["b"]
    with pytest.raises(ValueError, match="no such task"):
        remove_task(tasks, 1)


def test_todo_list_tasks():
    tasks = []
    assert list_tasks(tasks) == []
    add_task(tasks, "buy milk")
    add_task(tasks, "call mom")
    complete_task(tasks, 2)
    assert list_tasks(tasks) == ["[ ] 1: buy milk", "[x] 2: call mom"]
    assert list_tasks(tasks, show_done=False) == ["[ ] 1: buy milk"]


def test_todo_save_and_load(tmp_path):
    p = tmp_path / "tasks.json"
    assert load_tasks(p) == []
    tasks = []
    add_task(tasks, "a")
    add_task(tasks, "b")
    complete_task(tasks, 1)
    save_tasks(p, tasks)
    assert json.loads(p.read_text()) == tasks
    assert load_tasks(p) == tasks
    save_tasks(p, [])
    assert load_tasks(p) == []


def test_todo_handle_command_flow():
    tasks = []
    assert handle_command(tasks, "add buy milk") == "Added 1: buy milk"
    assert handle_command(tasks, "ADD call mom") == "Added 2: call mom"
    assert handle_command(tasks, "done 1") == "Completed 1"
    assert handle_command(tasks, "list") == "[x] 1: buy milk\n[ ] 2: call mom"
    assert handle_command(tasks, "remove 1") == "Removed 1"
    assert handle_command(tasks, "list") == "[ ] 2: call mom"
    assert handle_command(tasks, "remove 2") == "Removed 2"
    assert handle_command(tasks, "list") == "No tasks"
    assert tasks == []


def test_todo_handle_command_errors():
    tasks = []
    assert handle_command(tasks, "add") == "Error: title required"
    assert handle_command(tasks, "add   ") == "Error: title required"
    assert handle_command(tasks, "done") == "Error: invalid id"
    assert handle_command(tasks, "done abc") == "Error: invalid id"
    assert handle_command(tasks, "remove x") == "Error: invalid id"
    assert handle_command(tasks, "done 5") == "Error: no such task"
    assert handle_command(tasks, "remove 5") == "Error: no such task"
    assert handle_command(tasks, "dance now") == "Unknown command: dance now"
    assert handle_command(tasks, "") == "Unknown command: "
    assert tasks == []


# -------------------------- Project B: word frequency -----------------------


def test_word_tokenize():
    assert tokenize("") == []
    assert tokenize("Hello, World... hello") == ["hello", "world", "hello"]
    assert tokenize("Don't stop!") == ["don't", "stop"]
    assert tokenize("'quoted' words") == ["quoted", "words"]
    assert tokenize("a1b 22 c") == ["a", "b", "c"]
    assert tokenize("  ... ''' ") == []
    assert tokenize("end.") == ["end"]


def test_word_count_words():
    assert count_words([]) == {}
    assert count_words(["a", "b", "a"]) == {"a": 2, "b": 1}


def test_word_top_words():
    assert top_words({"b": 2, "a": 2, "c": 1}, 2) == [("a", 2), ("b", 2)]
    assert top_words({"b": 2, "a": 2, "c": 1}, 10) == [("a", 2), ("b", 2), ("c", 1)]
    assert top_words({}, 3) == []
    assert top_words({"a": 1}, 0) == []
    assert top_words({"x": 1, "y": 5}, 1) == [("y", 5)]


def test_word_remove_stop_words():
    words = ["the", "cat", "and", "the", "dog"]
    assert remove_stop_words(words, ["the", "AND"]) == ["cat", "dog"]
    assert remove_stop_words(words, []) == words
    assert remove_stop_words([], ["the"]) == []
    assert remove_stop_words(words, {"the"}) == ["cat", "and", "dog"]


def test_word_stats():
    assert word_stats([]) == {"total": 0, "unique": 0, "longest": None, "average_length": 0}
    s = word_stats(["hello", "world", "hi"])
    assert s["total"] == 3
    assert s["unique"] == 3
    assert s["longest"] == "hello"  # first of the longest
    assert s["average_length"] == 4.0
    s = word_stats(["a", "a", "bb"])
    assert s["total"] == 3 and s["unique"] == 2
    assert s["longest"] == "bb"
    assert s["average_length"] == 1.33


def test_word_analyze_file(tmp_path):
    p = tmp_path / "text.txt"
    p.write_text("The cat and the hat. The CAT sat!\nA hat?\n")
    r = analyze_file(p)
    assert r["total"] == 10
    assert r["unique"] == 6
    assert r["top"] == [("the", 3), ("cat", 2), ("hat", 2)]
    r = analyze_file(p, n=2, stop_words=["the", "a", "and"])
    assert r["total"] == 5
    assert r["top"] == [("cat", 2), ("hat", 2)]
    assert r["longest"] == "cat"
    with pytest.raises(FileNotFoundError):
        analyze_file(tmp_path / "missing.txt")


def test_word_analyze_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("")
    r = analyze_file(p)
    assert r["total"] == 0
    assert r["top"] == []
    assert r["longest"] is None


def test_word_format_report():
    stats = {
        "total": 5,
        "unique": 3,
        "longest": "hello",
        "average_length": 4.2,
        "top": [("hello", 2), ("world", 2)],
    }
    assert format_report(stats) == (
        "Total words: 5\n"
        "Unique words: 3\n"
        "Longest word: hello\n"
        "Average length: 4.2\n"
        "Top words:\n"
        "  hello: 2\n"
        "  world: 2"
    )
    empty = {"total": 0, "unique": 0, "longest": None, "average_length": 0}
    assert format_report(empty) == (
        "Total words: 0\nUnique words: 0\nLongest word: -\nAverage length: 0\nTop words:"
    )
