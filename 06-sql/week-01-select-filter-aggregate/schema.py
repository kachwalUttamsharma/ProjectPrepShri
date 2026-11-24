"""Sample database for Week 1. `make_db()` returns a fresh in-memory SQLite DB.

You can explore it yourself:

    .venv/bin/python -i 06-sql/week-01-select-filter-aggregate/schema.py
    >>> db = make_db()
    >>> db.execute("SELECT * FROM employees LIMIT 3").fetchall()

Tables
------
employees(id, name, dept, salary, hire_date, city, bonus)
    dept, salary, city and bonus can be NULL (on purpose!).
orders(id, customer, amount, status, order_date)
    amount can be NULL.
"""
import sqlite3

EMPLOYEES = [
    (1, "Alice", "Engineering", 120000, "2019-03-15", "NYC", 5000),
    (2, "Bob", "Engineering", 95000, "2020-07-01", "SF", None),
    (3, "Carol", "Engineering", 105000, "2018-01-20", "NYC", 8000),
    (4, "Dave", "Sales", 70000, "2021-02-11", "Austin", 3000),
    (5, "Eve", "Sales", 65000, "2022-05-30", "Austin", None),
    (6, "Frank", "Sales", 82000, "2017-09-05", "NYC", 6000),
    (7, "Grace", "HR", 60000, "2020-11-12", "SF", None),
    (8, "Heidi", "HR", 72000, "2019-06-25", "NYC", 2000),
    (9, "Ivan", "Engineering", 95000, "2023-01-09", "SF", 1000),
    (10, "Judy", "Marketing", 68000, "2021-08-18", "Austin", None),
    (11, "Mallory", "Marketing", 68000, "2022-10-03", "NYC", 0),
    (12, "Niaj", "Sales", None, "2024-02-01", "Austin", None),
    (13, "Oleg", None, 50000, "2024-03-01", None, None),
]

ORDERS = [
    (1, "acme", 250.00, "shipped", "2024-01-05"),
    (2, "acme", 100.00, "shipped", "2024-01-20"),
    (3, "globex", 75.50, "cancelled", "2024-01-22"),
    (4, "globex", 300.00, "shipped", "2024-02-02"),
    (5, "initech", 50.00, "pending", "2024-02-10"),
    (6, "initech", 125.00, "shipped", "2024-02-14"),
    (7, "acme", 400.00, "shipped", "2024-03-01"),
    (8, "umbrella", 20.00, "cancelled", "2024-03-03"),
    (9, "umbrella", 220.00, "shipped", "2024-03-09"),
    (10, "hooli", 90.00, "pending", "2024-03-12"),
    (11, "globex", None, "pending", "2024-03-15"),
    (12, "hooli", 150.00, "shipped", "2024-03-20"),
]


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, dept TEXT,
            salary INTEGER, hire_date TEXT NOT NULL, city TEXT, bonus INTEGER);
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY, customer TEXT NOT NULL, amount REAL,
            status TEXT NOT NULL, order_date TEXT NOT NULL);
        """
    )
    conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?)", EMPLOYEES)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", ORDERS)
    conn.commit()
    conn.execute("PRAGMA query_only = ON")  # exercises may only read
    return conn


# ---------------------------------------------------------------------------
# Test helpers (you do not need to edit anything below this line)
# ---------------------------------------------------------------------------
def run(conn, sql):
    """Execute `sql` on `conn`; return (lowercased column names, rows)."""
    if not isinstance(sql, str) or not sql.strip():
        raise AssertionError(
            "Exercise not implemented: the function must return a SQL string."
        )
    cur = conn.execute(sql)
    cols = [d[0].lower() for d in cur.description] if cur.description else []
    return cols, cur.fetchall()


def _norm(v):
    return round(v, 2) if isinstance(v, float) else v


def _key(row):
    out = []
    for v in row:
        if v is None:
            out.append((0, ""))
        elif isinstance(v, (int, float)):
            out.append((1, "%020.4f" % float(v)))
        else:
            out.append((2, str(v)))
    return tuple(out)


def assert_result(conn, sql, columns, expected, ordered=False):
    """Run `sql`; compare column names and rows with the expected ones.

    Row order only matters when ordered=True (i.e. the task requires ORDER BY).
    Floats are compared after rounding to 2 decimals.
    """
    cols, rows = run(conn, sql)
    want_cols = [c.lower() for c in columns]
    assert cols == want_cols, f"Expected columns {want_cols}, got {cols}"
    got = [tuple(_norm(v) for v in r) for r in rows]
    exp = [tuple(_norm(v) for v in r) for r in expected]
    if not ordered:
        got, exp = sorted(got, key=_key), sorted(exp, key=_key)
    assert got == exp, f"\nExpected rows: {exp}\nGot rows:      {got}"
