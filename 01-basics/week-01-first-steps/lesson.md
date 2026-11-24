# Week 1: First steps

## 1. Running Python
- REPL (interactive): `.venv/bin/python`, type code, press Enter. Exit with `exit()`.
- Script: save code in `hello.py`, run `.venv/bin/python hello.py`.

## 2. Variables
A variable is a name pointing to a value.
```python
age = 25
name = "Uttam"
price = 9.99
is_student = True
```
Types: `int`, `float`, `str`, `bool`. Check with `type(age)`.
Names: lowercase_with_underscores. `=` means "assign", not "equals".

## 3. Numbers
```python
7 + 2    # 9
7 - 2    # 5
7 * 2    # 14
7 / 2    # 3.5   (always a float)
7 // 2   # 3     (floor division)
7 % 2    # 1     (remainder)
7 ** 2   # 49    (power)
```
`%` is used constantly in interviews (even/odd, wrap-around).

## 4. Strings
```python
s = "hello"
len(s)            # 5
s[0]              # 'h'  (indexing starts at 0)
s[-1]             # 'o'  (last character)
s[1:4]            # 'ell' (slice: start included, end excluded)
s.upper()         # 'HELLO'
s + " world"      # 'hello world'
s * 3             # 'hellohellohello'
"ell" in s        # True
f"Hi {s}, 2+2={2+2}"   # f-string: embed values
```
Strings are **immutable**: you can't change `s[0]`, only build a new string.

## 5. Input and output
```python
name = input("Name? ")      # always returns a str
age = int(input("Age? "))   # convert to int
print("Hello", name)
```
Conversions: `int("5")`, `float("2.5")`, `str(10)`.

## Common mistakes
- `"5" + 5` raises TypeError. Convert first.
- `=` vs `==` (comparison).
- Off-by-one in slices: `s[1:4]` has 3 characters, not 4.

## Your task
Fill in `exercises.py`, then run the tests (see PROGRESS.md).
