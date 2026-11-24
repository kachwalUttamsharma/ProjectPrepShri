-- Part 02 sample data. Run: sqlite3 :memory: ".read setup.sql" or sqlite3 part02.db < setup.sql
DROP TABLE IF EXISTS customers_2023;
DROP TABLE IF EXISTS customers_2024;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS events;

CREATE TABLE customers_2023 (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
CREATE TABLE customers_2024 (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
INSERT INTO customers_2023 VALUES (1,'Ann','ann@x.com'),(2,'Bob','bob@x.com'),(3,'Cy',NULL),(4,'Di','di@x.com');
INSERT INTO customers_2024 VALUES (2,'Bob','bob@x.com'),(3,'Cy',NULL),(5,'Eve','eve@x.com'),(6,'Fay','fay@x.com');

CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, discount REAL, note TEXT);
INSERT INTO products VALUES
 (1,'  Widget ','tools',9.99,NULL,'basic'),
 (2,'Gadget','tools',24.50,0.10,''),
 (3,'Doohickey','toys',5.00,0,NULL),
 (4,'Thingamajig','toys',12.75,0.25,'sale'),
 (5,'Whatsit','garden',7.20,NULL,NULL);

CREATE TABLE sales (id INTEGER PRIMARY KEY, product_id INTEGER, sold_on TEXT, qty INTEGER, region TEXT);
INSERT INTO sales VALUES
 (1,1,'2024-01-05',3,'N'),(2,1,'2024-01-20',2,'S'),(3,2,'2024-01-25',1,'N'),
 (4,2,'2024-02-03',4,'N'),(5,3,'2024-02-14',10,'S'),(6,4,'2024-02-20',2,'S'),
 (7,1,'2024-03-01',5,'N'),(8,3,'2024-03-09',1,'N'),(9,4,'2024-03-15',3,'S'),
 (10,2,'2024-03-30',2,'S'),(11,5,'2024-03-31',6,'N'),(12,1,'2024-04-02',1,'S');

-- JSON stored as TEXT (json1 is built in to modern SQLite)
CREATE TABLE events (id INTEGER PRIMARY KEY, payload TEXT);
INSERT INTO events VALUES
 (1,'{"user":"ann","action":"login","meta":{"ip":"1.1.1.1","tags":["web","mfa"]}}'),
 (2,'{"user":"bob","action":"buy","meta":{"ip":"2.2.2.2","tags":["mobile"]},"amount":19.5}'),
 (3,'{"user":"ann","action":"buy","meta":{"ip":"1.1.1.1","tags":[]},"amount":5}'),
 (4,'{"user":"cy","action":"logout","meta":null}');
