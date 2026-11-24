"""Fixtures for Week 4 (schema design, indexes, transactions).

Unlike weeks 1-3 the exercises here return DDL / DML (CREATE TABLE, CREATE INDEX,
BEGIN ... COMMIT scripts, ...), so each test builds the starting database it needs
with one of the helpers below, runs YOUR SQL on it, and inspects the result.

All connections use `isolation_level=None` (autocommit: YOU control transactions with
BEGIN/COMMIT/ROLLBACK) and `PRAGMA foreign_keys = ON` (SQLite leaves FKs OFF by default!).

Starting tables per helper
--------------------------
fresh_conn()          empty database
db_with_users()       users(id, email)                                  2 rows
db_students_courses() students(id, name), courses(id, title)           2 + 2 rows
db_flat_orders()      flat_orders(order_id, customer_name, customer_email, product, price, qty)
db_events()           events(id, user_id, kind, created_at, payload)    3000 rows, no indexes
db_subscriptions()    subscriptions(id, user_id, active)
db_accounts()         accounts(id, owner, balance CHECK >= 0), audit(id, note)
db_products()         products(id, name, stock, version)                (1, 'pen', 10, 3)
db_stock()            stock(sku PRIMARY KEY, qty)                       ('pen', 10)
db_newsletter()       newsletter(email PRIMARY KEY)
db_orders()           orders(id, customer, total)
db_users_for_migration()  users(id, email) with 2 rows
"""
import sqlite3


def fresh_conn():
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def db_with_users():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);"
        "INSERT INTO users VALUES (1, 'a@x.com'), (2, 'b@x.com');"
    )
    return c


def db_students_courses():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT);"
        "CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT);"
        "INSERT INTO students VALUES (1, 'Ann'), (2, 'Bob');"
        "INSERT INTO courses VALUES (10, 'SQL'), (20, 'Python');"
    )
    return c


def db_flat_orders():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE flat_orders (order_id INTEGER PRIMARY KEY, customer_name TEXT,"
        " customer_email TEXT, product TEXT, price REAL, qty INTEGER);"
        "INSERT INTO flat_orders VALUES"
        " (1,'Ann','ann@x.com','pen',2.0,3),(2,'Ann','ann@x.com','book',12.5,1),"
        " (3,'Bob','bob@x.com','pen',2.0,5),(4,'Cy','cy@x.com','ink',4.0,2),"
        " (5,'Bob','bob@x.com','book',12.5,1);"
    )
    return c


def db_events():
    c = fresh_conn()
    c.execute(
        "CREATE TABLE events (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,"
        " kind TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT)"
    )
    kinds = ["click", "view", "buy"]
    rows = [
        (i, i % 100, kinds[i % 3], f"2024-{1 + (i % 60) // 30:02d}-{1 + (i % 60) % 30:02d}", "x" * 20)
        for i in range(1, 3001)
    ]
    c.executemany("INSERT INTO events VALUES (?,?,?,?,?)", rows)
    return c


def db_subscriptions():
    c = fresh_conn()
    c.execute(
        "CREATE TABLE subscriptions (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,"
        " active INTEGER NOT NULL)"
    )
    return c


def db_accounts():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE accounts (id INTEGER PRIMARY KEY, owner TEXT NOT NULL,"
        " balance INTEGER NOT NULL CHECK (balance >= 0));"
        "CREATE TABLE audit (id INTEGER PRIMARY KEY AUTOINCREMENT, note TEXT NOT NULL);"
        "INSERT INTO accounts VALUES (1, 'ann', 1000), (2, 'bob', 500);"
    )
    return c


def db_products():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, version INTEGER);"
        "INSERT INTO products VALUES (1, 'pen', 10, 3);"
    )
    return c


def db_stock():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE stock (sku TEXT PRIMARY KEY, qty INTEGER NOT NULL);"
        "INSERT INTO stock VALUES ('pen', 10);"
    )
    return c


def db_newsletter():
    c = fresh_conn()
    c.execute("CREATE TABLE newsletter (email TEXT PRIMARY KEY)")
    return c


def db_orders():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT, total REAL);"
        "INSERT INTO orders VALUES (1,'acme',100),(2,'acme',50),(3,'globex',75);"
    )
    return c


def db_users_for_migration():
    c = fresh_conn()
    c.executescript(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);"
        "INSERT INTO users VALUES (1, 'a@x.com'), (2, 'b@x.com');"
    )
    return c


def plan(conn, sql, params=()):
    """EXPLAIN QUERY PLAN output as one lowercase string (one line per plan step)."""
    rows = conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
    return "\n".join(r[-1] for r in rows).lower()


def script(sql):
    """Validate that an exercise returned SQL text."""
    if not isinstance(sql, str) or not sql.strip():
        raise AssertionError("Exercise not implemented: the function must return a SQL string.")
    return sql
