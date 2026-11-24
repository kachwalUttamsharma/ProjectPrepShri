"""Sample database for Week 3 (CTEs, window functions, CASE, dates).

Tables
------
employees(id, name, dept, salary, manager_id, hire_date)
    Ava (id 1) is the top of the hierarchy (manager_id NULL).
    Ben and Cara tie on salary, Fay and Gus tie (good for RANK vs DENSE_RANK).
sales(id, sale_date, region, amount)         -- 9 sales, Jan-Mar 2024, regions East/West
tickets(id, opened_at, closed_at, priority)  -- timestamps as 'YYYY-MM-DD HH:MM:SS'; closed_at NULL = still open
"""
import sqlite3

EMPLOYEES = [
    (1, "Ava", "Exec", 200000, None, "2015-01-10"),
    (2, "Ben", "Eng", 150000, 1, "2016-03-01"),
    (3, "Cara", "Eng", 150000, 2, "2018-06-15"),
    (4, "Dan", "Eng", 120000, 2, "2019-09-01"),
    (5, "Eli", "Eng", 100000, 3, "2021-01-20"),
    (6, "Fay", "Sales", 90000, 1, "2017-05-05"),
    (7, "Gus", "Sales", 90000, 6, "2020-02-02"),
    (8, "Hana", "Sales", 70000, 6, "2022-08-08"),
    (9, "Ian", "Sales", 60000, 7, "2023-04-04"),
    (10, "Jo", "HR", 80000, 1, "2019-11-11"),
    (11, "Kim", "HR", 65000, 10, "2021-07-07"),
]

SALES = [
    (1, "2024-01-03", "East", 100), (2, "2024-01-15", "West", 200),
    (3, "2024-01-28", "East", 150), (4, "2024-02-02", "West", 120),
    (5, "2024-02-14", "East", 300), (6, "2024-02-20", "West", 80),
    (7, "2024-03-05", "East", 250), (8, "2024-03-18", "West", 400),
    (9, "2024-03-25", "East", 50),
]

TICKETS = [
    (1, "2024-03-01 09:00:00", "2024-03-01 17:30:00", "high"),
    (2, "2024-03-02 10:15:00", "2024-03-04 10:15:00", "low"),
    (3, "2024-03-04 08:00:00", None, "medium"),
    (4, "2024-03-10 23:30:00", "2024-03-11 01:00:00", "high"),
    (5, "2024-04-01 12:00:00", "2024-04-08 12:00:00", "low"),
    (6, "2024-04-15 09:00:00", None, "high"),
]


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, dept TEXT NOT NULL,
            salary INTEGER NOT NULL, manager_id INTEGER REFERENCES employees(id),
            hire_date TEXT NOT NULL);
        CREATE TABLE sales (id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL,
            region TEXT NOT NULL, amount INTEGER NOT NULL);
        CREATE TABLE tickets (id INTEGER PRIMARY KEY, opened_at TEXT NOT NULL,
            closed_at TEXT, priority TEXT NOT NULL);
        """
    )
    conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?)", EMPLOYEES)
    conn.executemany("INSERT INTO sales VALUES (?,?,?,?)", SALES)
    conn.executemany("INSERT INTO tickets VALUES (?,?,?,?)", TICKETS)
    conn.commit()
    conn.execute("PRAGMA query_only = ON")
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
