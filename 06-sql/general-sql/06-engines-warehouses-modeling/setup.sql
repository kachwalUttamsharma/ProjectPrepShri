-- Part 06 setup: a tiny star schema + an SCD2 customer dimension.
-- Run:  sqlite3 :memory: ".read setup.sql" ".read practice.sql"
-- or:   sqlite3 part06.db < setup.sql   (then open part06.db interactively)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_customer_scd2;

CREATE TABLE dim_date (
  date_key   INTEGER PRIMARY KEY,   -- 20240115 style surrogate
  full_date  TEXT NOT NULL,
  year       INTEGER NOT NULL,
  month      INTEGER NOT NULL,
  quarter    INTEGER NOT NULL,
  is_weekend INTEGER NOT NULL
);
CREATE TABLE dim_product (
  product_key INTEGER PRIMARY KEY,
  sku         TEXT NOT NULL,
  name        TEXT NOT NULL,
  category    TEXT NOT NULL
);
CREATE TABLE dim_customer (
  customer_key INTEGER PRIMARY KEY,
  customer_id  TEXT NOT NULL,       -- natural / business key
  name         TEXT NOT NULL,
  region       TEXT NOT NULL
);
CREATE TABLE fact_sales (
  sale_id      INTEGER PRIMARY KEY,
  date_key     INTEGER NOT NULL REFERENCES dim_date(date_key),
  product_key  INTEGER NOT NULL REFERENCES dim_product(product_key),
  customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
  quantity     INTEGER NOT NULL,
  amount       REAL NOT NULL
);

INSERT INTO dim_date VALUES
 (20240105,'2024-01-05',2024,1,1,0),
 (20240106,'2024-01-06',2024,1,1,1),
 (20240215,'2024-02-15',2024,2,1,0),
 (20240410,'2024-04-10',2024,4,2,0),
 (20240720,'2024-07-20',2024,7,3,1);
INSERT INTO dim_product VALUES
 (1,'KB-01','Keyboard','Peripherals'),
 (2,'MS-01','Mouse','Peripherals'),
 (3,'MN-27','Monitor 27in','Displays'),
 (4,'DK-01','Desk','Furniture'),
 (5,'CH-01','Chair','Furniture');   -- never sold
INSERT INTO dim_customer VALUES
 (1,'C001','Asha','South'),
 (2,'C002','Ben','North'),
 (3,'C003','Chen','South'),
 (4,'C004','Dana','West');          -- never bought
INSERT INTO fact_sales VALUES
 (1,20240105,1,1,2,100.0),
 (2,20240105,3,2,1,300.0),
 (3,20240106,2,1,3,60.0),
 (4,20240215,3,3,2,600.0),
 (5,20240215,4,2,1,250.0),
 (6,20240410,1,3,1,50.0),
 (7,20240410,3,1,1,310.0),
 (8,20240720,4,1,2,500.0),
 (9,20240720,2,2,5,100.0);

-- SCD Type 2 customer dimension: one row per VERSION of a customer.
CREATE TABLE dim_customer_scd2 (
  customer_sk INTEGER PRIMARY KEY AUTOINCREMENT,  -- surrogate key per version
  customer_id TEXT NOT NULL,
  name        TEXT NOT NULL,
  city        TEXT NOT NULL,
  valid_from  TEXT NOT NULL,
  valid_to    TEXT NOT NULL DEFAULT '9999-12-31',
  is_current  INTEGER NOT NULL DEFAULT 1
);
INSERT INTO dim_customer_scd2 (customer_id,name,city,valid_from,valid_to,is_current) VALUES
 ('C001','Asha','Pune',  '2023-01-01','2024-03-01',0),
 ('C001','Asha','Mumbai','2024-03-01','9999-12-31',1),
 ('C002','Ben', 'Delhi', '2023-06-01','9999-12-31',1);

-- Incoming change feed (what the source system says today).
DROP TABLE IF EXISTS stg_customer;
CREATE TABLE stg_customer (customer_id TEXT PRIMARY KEY, name TEXT, city TEXT);
INSERT INTO stg_customer VALUES
 ('C001','Asha','Bengaluru'),   -- changed city
 ('C002','Ben','Delhi'),        -- unchanged
 ('C005','Esha','Chennai');     -- brand new
