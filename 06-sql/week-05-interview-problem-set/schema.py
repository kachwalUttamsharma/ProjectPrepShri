"""Sample database for Week 5 (interview problem set). `make_db()` returns a fresh in-memory DB.

Tables
------
departments(id, name)                       1 Eng, 2 Sales, 3 Ops
employees(id, name, salary, dept_id, manager_id)   Ann (id 1) has no manager
people(id, email)                           duplicate emails on purpose
product_sales(id, product, category, sale_date, amount)
logins(user_id, login_date)                 may contain duplicate rows (same user, same day)
log_ids(id)                                 integers with gaps: 1,2,3,7,8,10,15,16,17
payments(id, account, pay_date, amount)     positive = deposit, negative = withdrawal
daily_revenue(day, revenue)                 10 consecutive days
signups(user_id, signup_date)
activity(user_id, activity_date)            a user may be active many times per day
funnel_events(user_id, step, ts)            step in 'view' | 'cart' | 'purchase'; duplicates possible
orders(id, customer, order_date, amount)
purchases(customer, category)               one row per purchased item (duplicates possible)
seats(id, student)
web_events(user_id, ts)                     ts = 'YYYY-MM-DD HH:MM:SS'
"""
import sqlite3

DEPARTMENTS = [(1, "Eng"), (2, "Sales"), (3, "Ops")]

EMPLOYEES = [
    (1, "Ann", 90000, 1, None),
    (2, "Bob", 80000, 1, 1),
    (3, "Cat", 80000, 1, 1),
    (4, "Dev", 70000, 2, 1),
    (5, "Eve", 95000, 2, 4),
    (6, "Fox", 60000, 2, 4),
    (7, "Gil", 60000, 3, 1),
    (8, "Hal", 85000, 3, 7),
    (9, "Ivy", 85000, 3, 7),
    (10, "Jon", 100000, 1, 1),
    (11, "Kim", 55000, 2, 4),
]

PEOPLE = [(1, "a@x.com"), (2, "b@x.com"), (3, "a@x.com"), (4, "c@x.com"),
          (5, "b@x.com"), (6, "a@x.com")]

PRODUCT_SALES = [
    (1, "Pen", "Stationery", "2024-01-10", 20), (2, "Pen", "Stationery", "2024-02-11", 30),
    (3, "Book", "Stationery", "2024-01-15", 100), (4, "Desk", "Furniture", "2024-03-01", 300),
    (5, "Chair", "Furniture", "2024-03-05", 150), (6, "Lamp", "Furniture", "2024-04-02", 50),
    (7, "Ink", "Stationery", "2024-04-10", 40), (8, "Book", "Stationery", "2024-05-20", 60),
    (9, "Desk", "Furniture", "2024-06-15", 200), (10, "Pen", "Stationery", "2024-07-01", 25),
    (11, "Chair", "Furniture", "2024-08-30", 100), (12, "Lamp", "Furniture", "2024-09-09", 80),
]

LOGINS = [
    (1, "2024-03-01"), (1, "2024-03-02"), (1, "2024-03-03"), (1, "2024-03-05"), (1, "2024-03-06"),
    (2, "2024-03-01"), (2, "2024-03-03"), (2, "2024-03-05"),
    (3, "2024-03-10"), (3, "2024-03-11"), (3, "2024-03-12"), (3, "2024-03-13"), (3, "2024-03-14"),
    (4, "2024-03-01"), (4, "2024-03-02"), (4, "2024-03-02"), (4, "2024-03-10"),
]

LOG_IDS = [1, 2, 3, 7, 8, 10, 15, 16, 17]

PAYMENTS = [
    (1, "A", "2024-01-01", 100), (2, "A", "2024-01-05", -30), (3, "B", "2024-01-02", 50),
    (4, "A", "2024-01-09", 20), (5, "B", "2024-01-03", -10), (6, "B", "2024-01-08", 70),
]

DAILY_REVENUE = [(f"2024-03-{i + 1:02d}", v) for i, v in
                 enumerate([10, 30, 20, 40, 60, 50, 70, 90, 80, 100])]

SIGNUPS = [(1, "2024-03-01"), (2, "2024-03-01"), (3, "2024-03-01"),
           (4, "2024-03-02"), (5, "2024-03-02")]
ACTIVITY = [(1, "2024-03-02"), (1, "2024-03-05"), (2, "2024-03-03"), (3, "2024-03-02"),
            (4, "2024-03-03"), (5, "2024-03-02"), (2, "2024-03-01")]

FUNNEL = [
    (1, "view", "2024-03-01 10:00:00"), (1, "view", "2024-03-01 10:05:00"),
    (1, "cart", "2024-03-01 10:10:00"), (1, "purchase", "2024-03-01 10:20:00"),
    (2, "view", "2024-03-01 11:00:00"), (2, "cart", "2024-03-01 11:05:00"),
    (3, "view", "2024-03-01 12:00:00"),
    (4, "view", "2024-03-02 09:00:00"), (4, "cart", "2024-03-02 09:10:00"),
    (4, "purchase", "2024-03-02 09:30:00"),
    (5, "view", "2024-03-02 13:00:00"), (5, "cart", "2024-03-02 13:02:00"),
    (6, "view", "2024-03-03 08:00:00"), (6, "view", "2024-03-03 08:01:00"),
]

ORDERS = [
    (1, "ann", "2024-01-05", 50), (2, "bob", "2024-01-10", 80), (3, "ann", "2024-01-20", 70),
    (4, "cy", "2024-02-01", 20), (5, "bob", "2024-02-11", 120), (6, "ann", "2024-02-15", 90),
    (7, "cy", "2024-02-20", 60), (8, "bob", "2024-03-05", 40), (9, "ann", "2024-03-10", 100),
]

PURCHASES = [
    ("ann", "Stationery"), ("ann", "Stationery"), ("ann", "Furniture"), ("ann", "Tech"),
    ("bob", "Stationery"), ("bob", "Furniture"), ("cy", "Tech"), ("dan", "Tech"), ("dan", "Furniture"),
]

SEATS = [(1, "Abbot"), (2, "Doris"), (3, "Emerson"), (4, "Green"), (5, "Jeames")]

WEB_EVENTS = [
    (1, "2024-03-01 10:00:00"), (1, "2024-03-01 10:10:00"), (1, "2024-03-01 10:25:00"),
    (1, "2024-03-01 11:30:00"), (1, "2024-03-01 11:50:00"), (1, "2024-03-01 14:00:00"),
    (2, "2024-03-01 09:00:00"), (2, "2024-03-01 09:30:00"), (2, "2024-03-01 10:01:00"),
    (3, "2024-03-01 12:00:00"),
]


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT NOT NULL, salary INTEGER NOT NULL,
            dept_id INTEGER REFERENCES departments(id), manager_id INTEGER REFERENCES employees(id));
        CREATE TABLE people (id INTEGER PRIMARY KEY, email TEXT NOT NULL);
        CREATE TABLE product_sales (id INTEGER PRIMARY KEY, product TEXT, category TEXT,
            sale_date TEXT, amount INTEGER);
        CREATE TABLE logins (user_id INTEGER, login_date TEXT);
        CREATE TABLE log_ids (id INTEGER PRIMARY KEY);
        CREATE TABLE payments (id INTEGER PRIMARY KEY, account TEXT, pay_date TEXT, amount INTEGER);
        CREATE TABLE daily_revenue (day TEXT PRIMARY KEY, revenue INTEGER);
        CREATE TABLE signups (user_id INTEGER PRIMARY KEY, signup_date TEXT);
        CREATE TABLE activity (user_id INTEGER, activity_date TEXT);
        CREATE TABLE funnel_events (user_id INTEGER, step TEXT, ts TEXT);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, order_date TEXT, amount INTEGER);
        CREATE TABLE purchases (customer TEXT, category TEXT);
        CREATE TABLE seats (id INTEGER PRIMARY KEY, student TEXT);
        CREATE TABLE web_events (user_id INTEGER, ts TEXT);
        """
    )
    ins = lambda t, n, rows: conn.executemany(f"INSERT INTO {t} VALUES ({','.join('?' * n)})", rows)
    ins("departments", 2, DEPARTMENTS)
    ins("employees", 5, EMPLOYEES)
    ins("people", 2, PEOPLE)
    ins("product_sales", 5, PRODUCT_SALES)
    ins("logins", 2, LOGINS)
    ins("log_ids", 1, [(i,) for i in LOG_IDS])
    ins("payments", 4, PAYMENTS)
    ins("daily_revenue", 2, DAILY_REVENUE)
    ins("signups", 2, SIGNUPS)
    ins("activity", 2, ACTIVITY)
    ins("funnel_events", 3, FUNNEL)
    ins("orders", 4, ORDERS)
    ins("purchases", 2, PURCHASES)
    ins("seats", 2, SEATS)
    ins("web_events", 2, WEB_EVENTS)
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
