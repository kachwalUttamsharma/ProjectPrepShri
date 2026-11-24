-- Part 04 setup. Run: sqlite3 :memory: ".read setup.sql"  (or: sqlite3 db.sqlite < setup.sql)
-- Creates customers (500), orders (5000), order_items (~15000). No indexes except primary keys.
PRAGMA foreign_keys = ON;
DROP TABLE IF EXISTS order_items; DROP TABLE IF EXISTS orders; DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL,
  country TEXT NOT NULL, created_at TEXT NOT NULL, deleted_at TEXT
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id),
  status TEXT NOT NULL, total_cents INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
  sku TEXT NOT NULL, qty INTEGER NOT NULL, price_cents INTEGER NOT NULL
);

WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < 500)
INSERT INTO customers
SELECT i, 'Customer ' || i, 'user' || i || '@example.com',
       CASE i % 5 WHEN 0 THEN 'US' WHEN 1 THEN 'IN' WHEN 2 THEN 'DE' WHEN 3 THEN 'BR' ELSE 'JP' END,
       date('2023-01-01', '+' || (i % 700) || ' days'),
       CASE WHEN i % 20 = 0 THEN '2024-06-01' END
FROM n;

WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < 5000)
INSERT INTO orders
SELECT i, (i * 7919) % 500 + 1,
       CASE WHEN i % 50 = 0 THEN 'cancelled' WHEN i % 10 < 7 THEN 'shipped' WHEN i % 10 < 9 THEN 'paid' ELSE 'pending' END,
       (i * 37) % 20000 + 500,
       date('2024-01-01', '+' || (i % 365) || ' days')
FROM n;

WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i+1 FROM n WHERE i < 15000)
INSERT INTO order_items
SELECT i, (i % 5000) + 1, 'SKU-' || (i % 200), (i % 4) + 1, (i * 13) % 5000 + 100
FROM n;

ANALYZE;
