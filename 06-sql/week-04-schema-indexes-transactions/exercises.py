"""Week 4 SQL exercises: schema design, constraints, indexes, transactions.

Each function RETURNS SQL text. Most return a script of one or more statements
(the test runs it with `conn.executescript(...)`); the ones that say "named
parameters" return a single statement using :name placeholders.

The test builds a starting database (see schema.py), runs your SQL, then checks
behaviour: constraints must raise sqlite3.IntegrityError, EXPLAIN QUERY PLAN must
show your index in use, transactions must leave the right data behind.
Foreign keys are ON and the connection is in autocommit mode (you write BEGIN/COMMIT).
"""


def create_users_table():
    """CREATE TABLE users with exactly these columns, in this order:
        id     integer primary key
        email  text, required, unique
        name   text, required
        age    integer, optional, but if present must be >= 0
    """
    ...


def create_orders_table():
    """CREATE TABLE orders (a `users(id, email)` table already exists). Columns in this order:
        id          integer primary key
        user_id     integer, required, foreign key -> users(id), deleting a user deletes their orders
        total       real, required, must be >= 0
        status      text, required, default 'new', only 'new' / 'paid' / 'shipped' allowed
        created_at  text, required, defaults to the current timestamp (CURRENT_TIMESTAMP)
    """
    ...


def create_enrollments_table():
    """Many-to-many junction table between existing students(id) and courses(id):
    CREATE TABLE enrollments with columns
        student_id  integer, FK -> students(id)
        course_id   integer, FK -> courses(id)
        enrolled_on text, default CURRENT_DATE
    A student may enroll in a course only once (composite PRIMARY KEY (student_id, course_id)).
    """
    ...


def extract_customers():
    """Normalize the denormalized flat_orders table: create table
        customers(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)
    and fill it with one row per distinct (customer_name, customer_email) found in flat_orders
    (INSERT ... SELECT DISTINCT).  Return the whole script.
    """
    ...


def index_for_user_lookup():
    """Return CREATE INDEX for the query
        SELECT * FROM events WHERE user_id = 5
    so EXPLAIN QUERY PLAN shows a SEARCH using your index instead of a full SCAN.
    """
    ...


def index_for_user_time_range():
    """One composite index that serves
        SELECT id FROM events WHERE user_id = 5 AND created_at >= '2024-01-05' ORDER BY created_at
    both for filtering and for the ordering (no temp b-tree sort). Mind the column order:
    equality column first, range/sort column second.
    """
    ...


def covering_index_for_user_report():
    """A COVERING index for
        SELECT kind, created_at FROM events WHERE user_id = 7
    i.e. the query is answered from the index alone, without touching the table.
    """
    ...


def one_active_subscription_per_user():
    """A user may have many inactive subscriptions but at most ONE with active = 1.
    Return a partial UNIQUE index on subscriptions(user_id) restricted to active rows.
    """
    ...


def transfer_funds():
    """Atomically move 100 from account 1 to account 2 (both UPDATEs inside BEGIN ... COMMIT).
    Table: accounts(id, owner, balance).
    """
    ...


def rollback_demo():
    """A script that starts a transaction, deletes ALL rows from accounts, and then
    ROLLBACKs, so the table is unchanged afterwards.
    """
    ...


def savepoint_demo():
    """Using table audit(id, note): in ONE transaction
      insert note 'a'; SAVEPOINT s1; insert note 'b'; ROLLBACK TO s1; insert note 'c'; COMMIT.
    Final audit notes must be 'a' and 'c' (in that id order).
    """
    ...


def optimistic_decrement():
    """Optimistic locking. ONE UPDATE statement with named parameters :id and :version that
    decrements products.stock by 1 and bumps version by 1, but only if the row still has the
    version the client read (WHERE id = :id AND version = :version).
    A stale version must update 0 rows.
    """
    ...


def upsert_stock():
    """Upsert with named parameters :sku and :qty on stock(sku PRIMARY KEY, qty):
    insert the sku with qty, or if it exists add :qty to the existing qty
    (INSERT ... ON CONFLICT(sku) DO UPDATE SET ... excluded.qty).
    """
    ...


def subscribe_once():
    """Idempotent insert with named parameter :email into newsletter(email PRIMARY KEY):
    inserting an existing email must silently do nothing (ON CONFLICT ... DO NOTHING), not raise.
    """
    ...


def create_customer_totals_view():
    """CREATE VIEW customer_totals AS the sum of orders.total per customer.
    Columns: customer, total
    """
    ...


def add_is_active_column():
    """Migration: add column is_active INTEGER NOT NULL DEFAULT 1 to the existing users table
    (ALTER TABLE ... ADD COLUMN). Existing rows must read 1.
    """
    ...
