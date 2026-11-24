import json
import pytest
from exercises import *


def test_write_and_read_lines(tmp_path):
    p = tmp_path / "a.txt"
    write_lines(p, ["one", "two", "three"])
    assert p.read_text() == "one\ntwo\nthree\n"
    assert read_lines(p) == ["one", "two", "three"]
    write_lines(p, ["x"])  # overwrites
    assert read_lines(p) == ["x"]
    write_lines(str(p), [])  # str path works
    assert read_lines(p) == []


def test_read_lines_without_trailing_newline(tmp_path):
    p = tmp_path / "b.txt"
    p.write_text("a\nb")
    assert read_lines(p) == ["a", "b"]


def test_count_lines(tmp_path):
    p = tmp_path / "c.txt"
    p.write_text("")
    assert count_lines(p) == 0
    p.write_text("a\nb\nc\n")
    assert count_lines(p) == 3


def test_append_line(tmp_path):
    p = tmp_path / "d.txt"
    append_line(p, "first")  # creates the file
    append_line(p, "second")
    assert p.read_text() == "first\nsecond\n"


def test_longest_line(tmp_path):
    p = tmp_path / "e.txt"
    p.write_text("hi\nhello\nworld\nyo\n")
    assert longest_line(p) == "hello"
    p.write_text("")
    assert longest_line(p) is None


def test_safe_int():
    assert safe_int("42") == 42
    assert safe_int("-7") == -7
    assert safe_int("x") == 0
    assert safe_int("3.5") == 0
    assert safe_int("", 5) == 5
    assert safe_int(None, -1) == -1


def test_safe_divide():
    assert safe_divide(10, 2) == 5
    assert safe_divide(1, 4) == 0.25
    assert safe_divide(1, 0) is None


def test_validate_age():
    assert validate_age(0) == 0
    assert validate_age(30) == 30
    assert validate_age(150) == 150
    with pytest.raises(ValueError):
        validate_age(-1)
    with pytest.raises(ValueError):
        validate_age(151)
    with pytest.raises(TypeError):
        validate_age("30")
    with pytest.raises(TypeError):
        validate_age(3.5)
    with pytest.raises(TypeError):
        validate_age(True)


def test_read_or_default(tmp_path):
    p = tmp_path / "f.txt"
    assert read_or_default(p) == ""
    assert read_or_default(p, "none") == "none"
    p.write_text("hello")
    assert read_or_default(p, "none") == "hello"


def test_save_and_load_json(tmp_path):
    p = tmp_path / "g.json"
    data = {"name": "Sam", "scores": [1, 2, 3], "ok": True, "none": None}
    save_json(p, data)
    assert json.loads(p.read_text()) == data
    assert load_json(p) == data


def test_load_json_missing_and_invalid(tmp_path):
    assert load_json(tmp_path / "missing.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ValueError, match="invalid json"):
        load_json(bad)


def test_count_files_by_extension(tmp_path):
    (tmp_path / "a.txt").write_text("")
    (tmp_path / "b.TXT").write_text("")
    (tmp_path / "c.py").write_text("")
    (tmp_path / "README").write_text("")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "d.py").write_text("")
    assert count_files_by_extension(tmp_path) == {".txt": 2, ".py": 1, "": 1}
    empty = tmp_path / "empty"
    empty.mkdir()
    assert count_files_by_extension(empty) == {}
