# Week 8: Two small projects and Stage 1 review

This week you combine everything from weeks 1-7. Take your time: planning before coding is the real skill. For each project, first read the spec, then write in plain words (or comments) the steps each function needs, then code.

Work function by function. Run the tests often:
`.venv/bin/pytest 01-basics/week-08-projects-review -v`
Use `-k todo` or `-k word` to run one project only, or `-x` to stop at the first failure.

---

## Project A: Todo list (command line)

A task is a dict: `{"id": 1, "title": "buy milk", "done": False}`. The task list is a plain `list` of such dicts. Functions take the list as a parameter and change it in place (like a tiny database). There is no `input()` in the functions, so they are easy to test. After the tests pass you can add a `main()` loop at the bottom that reads a line with `input()` and prints `handle_command(...)`.

Functions (full details in the docstrings):
| Function | What it does |
|---|---|
| `add_task(tasks, title)` | Adds a task with the next free id (max id + 1, starting at 1). Blank title -> `ValueError`. Returns the new task. |
| `complete_task(tasks, task_id)` | Marks done. Unknown id -> `ValueError`. |
| `remove_task(tasks, task_id)` | Deletes it. Unknown id -> `ValueError`. |
| `list_tasks(tasks, show_done=True)` | Returns display lines like `[ ] 1: buy milk` / `[x] 2: call mom`. |
| `save_tasks(path, tasks)` / `load_tasks(path)` | JSON persistence. Missing file -> `[]`. |
| `handle_command(tasks, line)` | Parses `add buy milk`, `done 1`, `remove 1`, `list` and returns a message string. |

Ideas to practice: `line.split(maxsplit=1)`, `try/except ValueError` around `int(...)`, never using an id after a task is removed (ids are not reused for existing tasks).

## Project B: Word-frequency analyzer

Read a text file and report which words are most common.

| Function | What it does |
|---|---|
| `tokenize(text)` | Lowercase words. A word is a run of letters or apostrophes; leading/trailing apostrophes are removed. `"Don't stop!"` -> `["don't", "stop"]` |
| `count_words(words)` | `{word: count}` |
| `top_words(counts, n)` | `n` pairs `(word, count)`, highest count first, ties alphabetical. |
| `remove_stop_words(words, stop_words)` | Drops common words like "the" (case-insensitive on the stop list). |
| `word_stats(words)` | Dict with `total`, `unique`, `longest` (first one on ties) and `average_length` (rounded to 2 decimals; `0` and `None` for empty input). |
| `analyze_file(path, n=3, stop_words=())` | Reads the file, returns the stats dict plus a `"top"` list. |
| `format_report(stats)` | Turns that dict into a printable multi-line string (format in the docstring). |

## Stage 1 review checklist
Tick these off honestly. If you can't do one without looking, re-read that week and redo its exercises from a blank file.

**Week 1 - basics**
- [ ] I can explain variables, `int/float/str/bool`, and convert between them.
- [ ] I know `/`, `//`, `%`, `**` and use `%` for even/odd and wrap-around.
- [ ] I can index and slice strings, including negative indexes and `[::-1]`.

**Week 2 - control flow**
- [ ] I can write if/elif/else chains in the right order.
- [ ] I know when to use `for` vs `while`, and what `range(a, b, step)` produces.
- [ ] I can use `break`, `continue` and the accumulator pattern.

**Week 3 - functions**
- [ ] I understand parameters vs arguments, `return` vs `print`, default args, `*args`, `**kwargs`.
- [ ] I can explain local scope and the mutable-default trap.
- [ ] I can write a recursive function with a base case.

**Week 4 - lists, tuples, strings**
- [ ] I can slice, sort (`sorted` vs `.sort()`), and explain copy vs reference.
- [ ] I know the common string methods (`split`, `join`, `strip`, `replace`).
- [ ] I can work with nested lists (grids) safely.

**Week 5 - dicts, sets**
- [ ] I can count and group with a dict.
- [ ] I can use set union/intersection/difference.
- [ ] I can explain why `x in set` is faster than `x in list`.

**Week 6 - files, errors, modules**
- [ ] I can read/write files with `with open`, and use `pathlib`.
- [ ] I can `try/except` a specific error and `raise` my own.
- [ ] I can import modules and read/write JSON.

**Week 7 - comprehensions and generators**
- [ ] I can write list/dict/set comprehensions and know when a loop is clearer.
- [ ] I can use `sorted(key=...)`, `enumerate`, `zip`, `lambda`.
- [ ] I can write a generator with `yield` and explain why it saves memory.

**Interview readiness for Stage 1**
- [ ] I can solve FizzBuzz, reverse a string, check a palindrome, count characters, and two-sum from a blank file.
- [ ] I can say out loud what my code does, step by step, and test it with an empty input, one item and a repeated item.
- [ ] I know how to debug: read the error from the bottom up, add `print`, run the failing test alone with `-k`.

## Common mistakes
- Writing everything first and testing at the end. Do one function, run its test.
- Forgetting empty input (`""`, `[]`, missing file).
- Changing a list while looping over it (build a new one instead).
- Printing inside functions instead of returning.
- Mixing up `id` (int) and the text typed by the user (str): convert with `int(...)`.

## Your task
Fill in `exercises.py` (both projects), make all tests pass, then tick the checklist. Stage 2 (OOP) comes next.
