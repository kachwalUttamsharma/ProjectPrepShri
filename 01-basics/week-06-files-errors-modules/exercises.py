"""Week 6 exercises. Replace each `...` with your code.
Functions that take a `path` receive a str or pathlib.Path."""

import json
from pathlib import Path


def write_lines(path, lines):
    """Write each string in `lines` to the file at `path`, one per line (each ends with '\\n').
    Overwrites existing content."""
    ...


def read_lines(path):
    """Return the lines of the file as a list of strings WITHOUT trailing newlines.
    An empty file gives []."""
    ...


def count_lines(path):
    """Return the number of lines in the file."""
    ...


def append_line(path, line):
    """Append `line` plus a newline to the end of the file (create the file if missing)."""
    ...


def longest_line(path):
    """Return the longest line (no newline) in the file; the first one on ties.
    Return None if the file is empty."""
    ...


def safe_int(text, default=0):
    """Convert text to int. If it can't be converted, return `default`.
    safe_int('42') -> 42; safe_int('x') -> 0; safe_int(None, -1) -> -1.
    Hint: try/except (ValueError, TypeError)."""
    ...


def safe_divide(a, b):
    """Return a / b, or None if b is zero. Use try/except ZeroDivisionError."""
    ...


def validate_age(age):
    """Return age if it is an int between 0 and 150 (inclusive).
    Raise TypeError if it is not an int, ValueError if it is out of range.
    (Hint: bool is an int in Python, but reject it too with TypeError.)"""
    ...


def read_or_default(path, default=""):
    """Return the file's text, or `default` if the file doesn't exist.
    Hint: catch FileNotFoundError."""
    ...


def save_json(path, data):
    """Save `data` (dict/list) as JSON to `path`."""
    ...


def load_json(path):
    """Load and return JSON from `path`. If the file is missing return {}.
    If the file has invalid JSON raise ValueError('invalid json').
    Hint: json.JSONDecodeError is a subclass of ValueError, but re-raise with the message above."""
    ...


def count_files_by_extension(folder):
    """Return a dict {extension: count} for the FILES directly inside `folder`
    (not subfolders). Extension includes the dot, lowercased; files with no extension
    use ''. Hint: Path(folder).iterdir(), p.is_file(), p.suffix.lower()."""
    ...
