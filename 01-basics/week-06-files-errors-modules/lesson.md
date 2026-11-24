# Week 6: Files, errors, modules

## 1. Reading and writing files
Always use `with`: it closes the file for you, even if an error happens.
```python
with open("notes.txt", "w") as f:      # "w" write (overwrites), "a" append, "r" read (default)
    f.write("line 1\n")                # write does NOT add newlines
    f.write("line 2\n")

with open("notes.txt") as f:
    text = f.read()                    # whole file as one string
with open("notes.txt") as f:
    for line in f:                     # one line at a time, includes '\n'
        print(line.strip())
```
`f.readlines()` gives a list of lines. Use `encoding="utf-8"` for non-English text.

## 2. pathlib (modern paths)
```python
from pathlib import Path
p = Path("data") / "notes.txt"    # / joins parts
p.exists(); p.name; p.suffix      # 'notes.txt', '.txt'
p.parent.mkdir(exist_ok=True)     # make folder
p.write_text("hi\n")              # shortcut: write whole file
p.read_text()                     # shortcut: read whole file
```

## 3. Errors (exceptions)
When something goes wrong Python raises an exception and the program stops, unless you catch it.
```python
try:
    n = int("abc")
except ValueError:
    n = 0
else:
    print("no error")      # runs only if no exception
finally:
    print("always runs")   # cleanup
```
Common ones: `ValueError`, `TypeError`, `KeyError`, `IndexError`, `ZeroDivisionError`, `FileNotFoundError`.
- Catch the **specific** error you expect. A bare `except:` hides bugs.
- Keep the `try` block small.

## 4. Raising your own errors
```python
def set_age(age):
    if age < 0:
        raise ValueError("age cannot be negative")
    return age
```
Tests check this with `pytest.raises(ValueError)`.

## 5. Modules and imports
A module is a `.py` file. Import to reuse code.
```python
import math
math.sqrt(16)                      # 4.0
from collections import Counter
from math import pi as PI
```
Your own file `helpers.py` can be imported with `import helpers` (same folder). Useful standard modules: `math`, `random`, `datetime`, `os`, `pathlib`, `json`, `collections`, `itertools`.

`if __name__ == "__main__":` runs code only when the file is run directly, not when imported.

## 6. JSON
A text format for dicts/lists/strings/numbers/booleans/null.
```python
import json
text = json.dumps({"a": [1, 2]})       # to string
data = json.loads(text)                # from string
with open("x.json", "w") as f:
    json.dump(data, f)                 # to file
with open("x.json") as f:
    data = json.load(f)                # from file
```
Python `None` becomes `null`, tuples become lists, dict keys become strings.

## Common mistakes
- Forgetting `\n` when writing lines.
- Opening with `"w"` when you meant `"a"` (it erases the file).
- Not stripping `\n` from lines you read.
- `except Exception: pass` silently hiding problems.
- Reading a file after it was closed (use it inside the `with` block).

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-06-files-errors-modules -v`
The tests create temporary files for you, so nothing is left on your disk.
