-- scd2_demo.sql : star schema + SCD Type 2 in sqlite3-compatible SQL
-- Run: sqlite3 :memory: < scd2_demo.sql
-- Needs SQLite >= 3.25 (window functions) and >= 3.35 not required.

PRAGMA foreign_keys = ON;

-- ---------- 1. Dimensions ----------
CREATE TABLE dim_date (
  date_key     INTEGER PRIMARY KEY,   -- smart key yyyymmdd (acceptable for date dim)
  full_date    TEXT NOT NULL,
  year         INTEGER, month INTEGER, day INTEGER
);

CREATE TABLE dim_product (
  product_key  INTEGER PRIMARY KEY,   -- surrogate
  product_id   TEXT NOT NULL,         -- natural / business key
  name         TEXT NOT NULL,
  category     TEXT NOT NULL
);

-- SCD2 customer dimension
CREATE TABLE dim_customer (
  customer_key   INTEGER PRIMARY KEY AUTOINCREMENT,  -- surrogate, one per version
  customer_id    TEXT NOT NULL,                      -- natural key
  name           TEXT NOT NULL,
  city           TEXT NOT NULL,                      -- tracked attribute
  segment        TEXT NOT NULL,                      -- tracked attribute
  valid_from     TEXT NOT NULL,
  valid_to       TEXT NOT NULL DEFAULT '9999-12-31',
  is_current     INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX ux_customer_current ON dim_customer(customer_id) WHERE is_current = 1;

-- ---------- 2. Fact (grain: one row per order line) ----------
CREATE TABLE fact_sales (
  order_id      TEXT NOT NULL,            -- degenerate dimension
  line_no       INTEGER NOT NULL,
  date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
  customer_key  INTEGER NOT NULL REFERENCES dim_customer(customer_key),
  product_key   INTEGER NOT NULL REFERENCES dim_product(product_key),
  quantity      INTEGER NOT NULL,
  amount        REAL NOT NULL,
  PRIMARY KEY (order_id, line_no)
);

-- ---------- 3. Seed ----------
INSERT INTO dim_date VALUES
 (20240101,'2024-01-01',2024,1,1),
 (20240215,'2024-02-15',2024,2,15),
 (20240601,'2024-06-01',2024,6,1);
INSERT INTO dim_product VALUES (1,'P1','Widget','Hardware'),(2,'P2','Gadget','Hardware');

-- Initial load (day 1)
INSERT INTO dim_customer (customer_id,name,city,segment,valid_from)
VALUES ('C1','Asha','Pune','SMB','2024-01-01'),
       ('C2','Ben','Austin','Enterprise','2024-01-01');

-- Fact row before the change: points at the OLD version of C1
INSERT INTO fact_sales VALUES
 ('O1',1,20240101,(SELECT customer_key FROM dim_customer WHERE customer_id='C1' AND is_current=1),1,2,20.0);

-- ---------- 4. SCD2 change feed ----------
CREATE TABLE stg_customer (customer_id TEXT, name TEXT, city TEXT, segment TEXT, effective_date TEXT);
INSERT INTO stg_customer VALUES
 ('C1','Asha','Mumbai','SMB','2024-02-15'),        -- city changed
 ('C2','Ben','Austin','Enterprise','2024-02-15'),  -- unchanged
 ('C3','Chen','Berlin','SMB','2024-02-15');        -- brand new

-- Step A: close current rows whose tracked attributes differ
UPDATE dim_customer
SET valid_to = (SELECT s.effective_date FROM stg_customer s WHERE s.customer_id = dim_customer.customer_id),
    is_current = 0
WHERE is_current = 1
  AND EXISTS (SELECT 1 FROM stg_customer s
              WHERE s.customer_id = dim_customer.customer_id
                AND (s.city <> dim_customer.city OR s.segment <> dim_customer.segment));

-- Step B: insert new versions for changed + new customers (no current row exists now)
INSERT INTO dim_customer (customer_id,name,city,segment,valid_from)
SELECT s.customer_id, s.name, s.city, s.segment, s.effective_date
FROM stg_customer s
WHERE NOT EXISTS (SELECT 1 FROM dim_customer d WHERE d.customer_id = s.customer_id AND d.is_current = 1);

-- Fact load AFTER change: look up the version valid on the transaction date
INSERT INTO fact_sales
SELECT 'O2',1,20240215,
       (SELECT customer_key FROM dim_customer
         WHERE customer_id='C1' AND '2024-02-15' >= valid_from AND '2024-02-15' < valid_to),
       2,1,15.0;

-- ---------- 5. Checks / demo queries ----------
.headers on
.mode column
SELECT '--- dim_customer versions ---' AS info;
SELECT customer_key,customer_id,city,valid_from,valid_to,is_current FROM dim_customer ORDER BY customer_id,valid_from;

SELECT '--- sales by city AS-WAS (historical truth) ---' AS info;
SELECT c.city, SUM(f.amount) AS revenue
FROM fact_sales f JOIN dim_customer c USING (customer_key)
GROUP BY c.city ORDER BY c.city;

SELECT '--- sales by CURRENT city AS-IS (join on natural key to current row) ---' AS info;
SELECT cur.city, SUM(f.amount) AS revenue
FROM fact_sales f
JOIN dim_customer v   ON v.customer_key = f.customer_key
JOIN dim_customer cur ON cur.customer_id = v.customer_id AND cur.is_current = 1
GROUP BY cur.city ORDER BY cur.city;

SELECT '--- integrity: exactly one current row per customer (expect 0 rows) ---' AS info;
SELECT customer_id, COUNT(*) FROM dim_customer WHERE is_current=1 GROUP BY 1 HAVING COUNT(*)<>1;

SELECT '--- integrity: no overlapping validity ranges (expect 0 rows) ---' AS info;
SELECT a.customer_id FROM dim_customer a JOIN dim_customer b
  ON a.customer_id=b.customer_id AND a.customer_key<b.customer_key
 AND a.valid_from < b.valid_to AND b.valid_from < a.valid_to;

SELECT '--- idempotency: re-run steps A and B, row count must stay 4 ---' AS info;
UPDATE dim_customer
SET valid_to = (SELECT s.effective_date FROM stg_customer s WHERE s.customer_id = dim_customer.customer_id), is_current = 0
WHERE is_current = 1 AND EXISTS (SELECT 1 FROM stg_customer s WHERE s.customer_id = dim_customer.customer_id
      AND (s.city <> dim_customer.city OR s.segment <> dim_customer.segment));
INSERT INTO dim_customer (customer_id,name,city,segment,valid_from)
SELECT s.customer_id, s.name, s.city, s.segment, s.effective_date FROM stg_customer s
WHERE NOT EXISTS (SELECT 1 FROM dim_customer d WHERE d.customer_id = s.customer_id AND d.is_current = 1);
SELECT COUNT(*) AS rows_after_rerun FROM dim_customer;
