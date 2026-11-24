-- practice.sql: part 03. First:  sqlite3 part03.db ".read setup.sql"  then open part03.db.
-- Write your answers in the blank spaces. Lines starting "--" are tasks. No solutions here.
.headers on
.mode column

-- ===== SQLite-runnable =====

-- T1. Create a view order_totals(order_id, customer, status, total) where total = SUM(qty*unit_price).
--     Then SELECT all rows ordered by order_id.



-- T2. Create a view customer_spend(customer, spend) built ON the view from T1, counting only
--     orders with status 'paid' or 'shipped'. Query it ordered by spend desc.



-- T3. Create a trigger that, after price changes on products, inserts a row into price_audit
--     (product_id, old_price, new_price). It must NOT log updates that leave the price unchanged.
--     Test: update product 1 to 55 twice. How many audit rows exist? Why?



-- T4. Create an AFTER INSERT trigger on order_items that decrements products.stock by qty.
--     Then create a BEFORE INSERT trigger that aborts with 'insufficient stock' when stock < qty.
--     Test with a valid insert and an invalid one. Does the failed insert leave stock untouched?



-- T5. Create a TEMP table big_orders holding orders from the view with total >= 100.
--     Confirm it is not visible from a second sqlite3 connection (open one and try).



-- T6. Make a view v_products(id, name, price) updatable with an INSTEAD OF UPDATE trigger,
--     then run UPDATE v_products SET price = 6 WHERE id = 4 and check products.



-- T7. List every view and trigger in the database using the catalog table sqlite_master.



-- T8. Create a table with an AUTOINCREMENT id and a random 32-hex-char token default.
--     Insert two rows with DEFAULT VALUES. Explain the difference between INTEGER PRIMARY KEY
--     and INTEGER PRIMARY KEY AUTOINCREMENT in a comment.



-- T9. ATTACH an in-memory database as "archive", copy shipped orders into archive.old_orders,
--     and count them with a qualified name.



-- ===== Postgres-only (not run here; try in the Docker Postgres from README) =====

-- P1. Create a MATERIALIZED VIEW of revenue per customer, add a unique index, and refresh it
--     CONCURRENTLY. Why is the unique index needed?



-- P2. Create a sequence invoice_no starting at 1000. Call nextval three times, roll back a
--     transaction that used one. Do you get that number back? Explain.



-- P3. Write a PL/pgSQL (or SQL) function order_total(bigint) and a procedure ship_order(bigint)
--     that raises an exception unless the order is 'paid'.



-- P4. Create an ENUM type order_status and a DOMAIN positive_int. Use them in a table.
--     Try inserting an invalid value. What error do you get?



-- P5. Create schema reporting, a role report_ro (NOLOGIN) with SELECT on all its tables,
--     and a login role you add to it. Verify with SET ROLE that INSERT is denied.



-- P6. Add a tenant_id column to orders, enable ROW LEVEL SECURITY with a policy using
--     current_setting('app.tenant_id'). Test with SET LOCAL as a non-owner role. What happens to the owner?



-- P7. Write a trigger FUNCTION + trigger that keeps orders.updated_at current on every UPDATE.



-- ===== MySQL-only (not run here) =====

-- M1. Write a stored procedure ship_order(IN p BIGINT) that uses SIGNAL when no row was updated.
--     Remember DELIMITER.


