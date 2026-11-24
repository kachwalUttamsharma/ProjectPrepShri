# Week 2: Conditions and loops

## 1. Booleans and comparisons
```python
5 > 3        # True
5 == 5       # True   (== compares, = assigns)
5 != 4       # True
3 <= 3       # True
"a" < "b"    # True   (alphabetical order)
1 < x < 10   # chained comparison: x between 1 and 10
```
Combine with `and`, `or`, `not`:
```python
age = 20
age >= 18 and age < 65   # True
not (age > 30)           # True
```
"Falsy" values (treated as False in an `if`): `0`, `0.0`, `""`, `[]`, `None`, `False`. Everything else is "truthy".

## 2. if / elif / else
```python
score = 72
if score >= 90:
    grade = "A"
elif score >= 70:
    grade = "B"
else:
    grade = "C"
```
- The colon `:` and the **indentation** (4 spaces) are required.
- Python checks top to bottom and runs only the FIRST branch that is True.

## 3. for loops and range
`for` repeats code once per item.
```python
for ch in "abc":
    print(ch)            # a, b, c

for i in range(5):       # 0,1,2,3,4
    print(i)
range(2, 6)              # 2,3,4,5      (end excluded)
range(10, 0, -3)         # 10,7,4,1     (step -3)
```

## 4. while loops
Repeat while a condition is True. You must make it eventually False.
```python
n = 10
while n > 0:
    n -= 2               # same as n = n - 2
```

## 5. break and continue
```python
for n in range(10):
    if n == 3:
        continue         # skip the rest of this round, go to next
    if n == 6:
        break            # leave the loop entirely
    print(n)             # 0 1 2 4 5
```

## 6. The accumulator pattern
Start with a value, update it inside the loop. You will use this forever.
```python
total = 0
for n in range(1, 5):
    total += n           # total is 10 at the end
```

## 7. FizzBuzz idea
Check the most specific condition first (divisible by 15 before 3 or 5), because only the first matching branch runs.

## 8. Nested loops
A loop inside a loop. The inner one fully runs for each step of the outer one.
```python
for row in range(3):
    for col in range(2):
        print(row, col)  # 6 lines
```

## Common mistakes
- Infinite `while` loop: forgetting to change the variable. Stop with Ctrl+C.
- `if x = 5` (should be `==`).
- Wrong order in `elif` chains (general condition first hides the specific one).
- `range(5)` stops at 4, not 5.
- Forgetting to initialize the accumulator before the loop.

## Your task
Fill in `exercises.py`, then run:
`.venv/bin/pytest 01-basics/week-02-conditions-loops -v`
