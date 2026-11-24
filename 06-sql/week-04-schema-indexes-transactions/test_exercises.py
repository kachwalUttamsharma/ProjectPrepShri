import sqlite3

import pytest

from exercises import *
from schema import (db_accounts, db_events, db_flat_orders, db_newsletter, db_orders,
                    db_products, db_stock, db_students_courses, db_subscriptions,
                    db_users_for_migration, db_with_users, fresh_conn, plan, script)


def cols(conn, table):
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


# ---------------------------------------------------------------- constraints
def test_create_users_table():
    c = fresh_conn()
    c.executescript(script(create_users_table()))
    assert cols(c, "users") == ["id", "email", "name", "age"]
    c.execute("INSERT INTO users VALUES (1, 'a@x.com', 'A', 30)")
    c.execute("INSERT INTO users VALUES (2, 'b@x.com', 'B', NULL)")  # age optional
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO users VALUES (3, 'a@x.com', 'Dup', 20)")  # unique email
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO users VALUES (4, 'c@x.com', NULL, 20)")  # name required
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO users VALUES (5, NULL, 'E', 20)")  # email required
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO users VALUES (6, 'f@x.com', 'F', -1)")  # age check


def test_create_orders_table():
    c = db_with_users()
    c.executescript(script(create_orders_table()))
    assert cols(c, "orders") == ["id", "user_id", "total", "status", "created_at"]
    c.execute("INSERT INTO orders (user_id, total) VALUES (1, 10.5)")
    status, created = c.execute("SELECT status, created_at FROM orders").fetchone()
    assert status == "new" and created
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO orders (user_id, total) VALUES (99, 5)")  # FK
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO orders (user_id, total) VALUES (NULL, 5)")  # NOT NULL
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO orders (user_id, total) VALUES (1, -5)")  # CHECK total
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO orders (user_id, total, status) VALUES (1, 5, 'lost')")
    c.execute("INSERT INTO orders (user_id, total, status) VALUES (2, 7, 'paid')")
    c.execute("DELETE FROM users WHERE id = 1")  # cascade
    assert c.execute("SELECT user_id FROM orders").fetchall() == [(2,)]


def test_create_enrollments_table():
    c = db_students_courses()
    c.executescript(script(create_enrollments_table()))
    assert cols(c, "enrollments") == ["student_id", "course_id", "enrolled_on"]
    c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (1, 10)")
    c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (1, 20)")
    c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (2, 10)")
    assert c.execute("SELECT enrolled_on FROM enrollments LIMIT 1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (1, 10)")  # twice
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (9, 10)")  # FK
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO enrollments (student_id, course_id) VALUES (1, 99)")  # FK


def test_extract_customers():
    c = db_flat_orders()
    c.executescript(script(extract_customers()))
    assert cols(c, "customers") == ["id", "name", "email"]
    rows = c.execute("SELECT name, email FROM customers ORDER BY name").fetchall()
    assert rows == [("Ann", "ann@x.com"), ("Bob", "bob@x.com"), ("Cy", "cy@x.com")]
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO customers (name, email) VALUES ('Ann2', 'ann@x.com')")


# -------------------------------------------------------------------- indexes
def test_index_for_user_lookup():
    c = db_events()
    q = "SELECT * FROM events WHERE user_id = 5"
    assert "scan" in plan(c, q)  # before: full table scan
    c.executescript(script(index_for_user_lookup()))
    p = plan(c, q)
    assert "search" in p and "using index" in p and "scan" not in p, p


def test_index_for_user_time_range():
    c = db_events()
    q = "SELECT id FROM events WHERE user_id = 5 AND created_at >= '2024-01-05' ORDER BY created_at"
    c.executescript(script(index_for_user_time_range()))
    p = plan(c, q)
    assert "search" in p and "user_id=?" in p, p
    assert "temp b-tree" not in p, "index should also provide the ORDER BY: " + p


def test_covering_index_for_user_report():
    c = db_events()
    q = "SELECT kind, created_at FROM events WHERE user_id = 7"
    c.executescript(script(covering_index_for_user_report()))
    p = plan(c, q)
    assert "covering index" in p and "user_id=?" in p, p


def test_one_active_subscription_per_user():
    c = db_subscriptions()
    c.executescript(script(one_active_subscription_per_user()))
    c.execute("INSERT INTO subscriptions (user_id, active) VALUES (1, 0)")
    c.execute("INSERT INTO subscriptions (user_id, active) VALUES (1, 0)")
    c.execute("INSERT INTO subscriptions (user_id, active) VALUES (1, 1)")
    c.execute("INSERT INTO subscriptions (user_id, active) VALUES (2, 1)")
    with pytest.raises(sqlite3.IntegrityError):
        c.execute("INSERT INTO subscriptions (user_id, active) VALUES (1, 1)")


# --------------------------------------------------------------- transactions
def test_transfer_funds():
    c = db_accounts()
    c.executescript(script(transfer_funds()))
    assert not c.in_transaction
    assert c.execute("SELECT id, balance FROM accounts ORDER BY id").fetchall() == [(1, 900), (2, 600)]
    sql = transfer_funds().lower()
    assert "begin" in sql and "commit" in sql


def test_rollback_demo():
    c = db_accounts()
    sql = script(rollback_demo())
    c.executescript(sql)
    assert not c.in_transaction
    assert c.execute("SELECT COUNT(*) FROM accounts").fetchone() == (2,)
    assert "delete" in sql.lower() and "rollback" in sql.lower()


def test_savepoint_demo():
    c = db_accounts()
    c.executescript(script(savepoint_demo()))
    assert not c.in_transaction
    assert c.execute("SELECT note FROM audit ORDER BY id").fetchall() == [("a",), ("c",)]
    assert "savepoint" in savepoint_demo().lower()


def test_optimistic_decrement():
    c = db_products()
    sql = script(optimistic_decrement())
    cur = c.execute(sql, {"id": 1, "version": 3})
    assert cur.rowcount == 1
    assert c.execute("SELECT stock, version FROM products").fetchone() == (9, 4)
    cur = c.execute(sql, {"id": 1, "version": 3})  # stale read
    assert cur.rowcount == 0
    assert c.execute("SELECT stock, version FROM products").fetchone() == (9, 4)


def test_upsert_stock():
    c = db_stock()
    sql = script(upsert_stock())
    c.execute(sql, {"sku": "pen", "qty": 5})
    c.execute(sql, {"sku": "ink", "qty": 7})
    c.execute(sql, {"sku": "ink", "qty": 1})
    assert c.execute("SELECT sku, qty FROM stock ORDER BY sku").fetchall() == [("ink", 8), ("pen", 15)]


def test_subscribe_once():
    c = db_newsletter()
    sql = script(subscribe_once())
    assert c.execute(sql, {"email": "a@x.com"}).rowcount == 1
    assert c.execute(sql, {"email": "a@x.com"}).rowcount == 0
    assert c.execute("SELECT COUNT(*) FROM newsletter").fetchone() == (1,)


# ---------------------------------------------------------- views / migrations
def test_create_customer_totals_view():
    c = db_orders()
    c.executescript(script(create_customer_totals_view()))
    assert cols(c, "customer_totals") == ["customer", "total"]
    assert sorted(c.execute("SELECT customer, total FROM customer_totals").fetchall()) == [
        ("acme", 150.0), ("globex", 75.0)]
    c.execute("INSERT INTO orders VALUES (4, 'globex', 25)")  # views are live
    assert dict(c.execute("SELECT customer, total FROM customer_totals").fetchall())["globex"] == 100.0


def test_add_is_active_column():
    c = db_users_for_migration()
    c.executescript(script(add_is_active_column()))
    assert cols(c, "users") == ["id", "email", "is_active"]
    assert c.execute("SELECT is_active FROM users").fetchall() == [(1,), (1,)]
    c.execute("INSERT INTO users (id, email) VALUES (3, 'c@x.com')")
    assert c.execute("SELECT is_active FROM users WHERE id = 3").fetchone() == (1,)
