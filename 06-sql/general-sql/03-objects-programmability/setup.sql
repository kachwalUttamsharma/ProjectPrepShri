-- setup.sql: sample schema for part 03. Run in SQLite:
--   sqlite3 :memory: ".read setup.sql"     (or: sqlite3 part03.db < setup.sql)
PRAGMA foreign_keys = ON;

CREATE TABLE customers (
  id      INTEGER PRIMARY KEY,
  name    TEXT NOT NULL,
  email   TEXT UNIQUE,
  country TEXT NOT NULL
);

CREATE TABLE products (
  id    INTEGER PRIMARY KEY,
  name  TEXT NOT NULL,
  price NUMERIC NOT NULL CHECK (price >= 0),
  stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
  id          INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  status      TEXT NOT NULL DEFAULT 'new',
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE order_items (
  order_id   INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  qty        INTEGER NOT NULL CHECK (qty > 0),
  unit_price NUMERIC NOT NULL,
  PRIMARY KEY (order_id, product_id)
);

-- Audit table, to be filled by triggers in the practice tasks
CREATE TABLE price_audit (
  id         INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL,
  old_price  NUMERIC,
  new_price  NUMERIC,
  changed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO customers VALUES
 (1,'Asha','asha@x.com','IN'),(2,'Ben','ben@x.com','US'),
 (3,'Chen','chen@x.com','CN'),(4,'Dara',NULL,'US');
INSERT INTO products VALUES
 (1,'Keyboard',50,10),(2,'Mouse',20,25),(3,'Monitor',200,5),(4,'Cable',5,100);
INSERT INTO orders (id,customer_id,status,created_at) VALUES
 (1,1,'paid','2026-01-05 10:00:00'),(2,1,'shipped','2026-01-20 12:00:00'),
 (3,2,'paid','2026-02-02 09:30:00'),(4,3,'new','2026-02-10 15:00:00');
INSERT INTO order_items VALUES
 (1,1,1,50),(1,2,2,20),(2,3,1,200),(3,2,1,20),(3,4,5,5),(4,1,2,50);
