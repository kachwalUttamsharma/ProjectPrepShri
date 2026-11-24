"""Sample database for Week 2 (joins and subqueries). `make_db()` returns a fresh in-memory DB.

Tables
------
departments(id, name, location)          -- 'Legal' has no employees
employees(id, name, dept_id, manager_id, salary)
    dept_id is NULL for contractor Ian; manager_id is NULL for the CEO (Ava).
projects(id, name, dept_id)              -- dept_id NULL = company-wide project
assignments(emp_id, project_id, hours)   -- who works on which project (Fay, Gus, Hana have none)
customers(id, name, country)             -- Hooli and Stark have no orders
orders(id, customer_id, order_date, total)
"""
import sqlite3

DEPARTMENTS = [(1, "Engineering", "NYC"), (2, "Sales", "Austin"),
               (3, "HR", "SF"), (4, "Legal", "Chicago")]

EMPLOYEES = [
    (1, "Ava", 1, None, 200000),
    (2, "Ben", 1, 1, 150000),
    (3, "Cara", 1, 2, 160000),
    (4, "Dan", 2, 1, 90000),
    (5, "Eli", 2, 4, 95000),
    (6, "Fay", 2, 4, 70000),
    (7, "Gus", 3, 1, 65000),
    (8, "Hana", 3, 7, 60000),
    (9, "Ian", None, 1, 80000),
    (10, "Jo", 1, 2, 120000),
]

PROJECTS = [(1, "Atlas", 1), (2, "Beacon", 1), (3, "Compass", 2), (4, "Delta", None)]

ASSIGNMENTS = [(2, 1, 100), (3, 1, 150), (3, 2, 80), (4, 3, 60),
               (5, 3, 90), (10, 2, 40), (9, 4, 30), (1, 1, 10)]

CUSTOMERS = [(1, "Acme", "US"), (2, "Globex", "US"), (3, "Initech", "UK"),
             (4, "Umbrella", "DE"), (5, "Hooli", "US"), (6, "Stark", "UK")]

ORDERS = [
    (1, 1, "2024-01-05", 250), (2, 1, "2024-02-10", 100),
    (3, 2, "2024-01-22", 300), (4, 3, "2024-02-14", 125),
    (5, 3, "2024-03-01", 400), (6, 4, "2024-03-09", 220),
    (7, 2, "2024-03-15", 80), (8, 1, "2024-03-20", 150),
]


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL, location TEXT);
        CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            dept_id INTEGER REFERENCES departments(id),
            manager_id INTEGER REFERENCES employees(id), salary INTEGER NOT NULL);
        CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            dept_id INTEGER REFERENCES departments(id));
        CREATE TABLE assignments (emp_id INTEGER REFERENCES employees(id),
            project_id INTEGER REFERENCES projects(id), hours INTEGER NOT NULL,
            PRIMARY KEY (emp_id, project_id));
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_date TEXT NOT NULL, total REAL NOT NULL);
        """
    )
    conn.executemany("INSERT INTO departments VALUES (?,?,?)", DEPARTMENTS)
    conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?)", EMPLOYEES)
    conn.executemany("INSERT INTO projects VALUES (?,?,?)", PROJECTS)
    conn.executemany("INSERT INTO assignments VALUES (?,?,?)", ASSIGNMENTS)
    conn.executemany("INSERT INTO customers VALUES (?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", ORDERS)
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
