-- Part 02 practice. Setup: sqlite3 practice.db ".read setup.sql" then open practice.db and write your answers below.
-- Or in one go: sqlite3 :memory: ".read setup.sql" ".read practice.sql"
-- Tip: .headers on and .mode column make output readable. Solutions are NOT in this repo.
-- Tasks 17-21 use SQLite json1; also write the Postgres/MySQL equivalent as a comment (cannot run here).

-- 1. Combine names+emails of customers_2023 and customers_2024 with duplicates removed, sorted by name.




-- 2. Count how many rows you get when you stack ids of both customer tables WITHOUT removing duplicates.




-- 3. Customers (id, name) present in BOTH years.




-- 4. Customers (id, name) present in 2023 but NOT in 2024.




-- 5. Ids that are in exactly one of the two years (symmetric difference), using only set operators.




-- 6. Join the two customer tables on email so that Cy (NULL email) matches Cy. Use a NULL-safe comparison.




-- 7. For each product: id and final price = price * (1 - discount), treating NULL discount as 0, rounded to 2 places.




-- 8. Return product id and note, but turn empty-string notes into NULL (keep NULL as NULL).




-- 9. Return product id, upper-cased trimmed name, and trimmed name length.




-- 10. Total qty sold per month ('YYYY-MM'), ordered by month.




-- 11. For every sale, return the last day of its month.




-- 12. Pagination by OFFSET: page 3 of size 4 of sales ordered by id (ids only).




-- 13. Keyset pagination: the next 4 sales (id, sold_on) AFTER the row (sold_on='2024-03-01', id=7), ordered by sold_on, id.




-- 14. Pivot: one row per product name with columns north and south holding total qty (0 when none).




-- 15. Unpivot your pivot result from task 14 (or recompute per product_id) back into rows (product_id, region, qty).




-- 16. Latest 2 sales (by sold_on, then id) per product. (This is what LATERAL / CROSS APPLY does in other dialects.)




-- 17. events: return id and the user name as plain text (not JSON-quoted).




-- 18. events: id and amount for events whose action is 'buy'.




-- 19. events: one row per tag (id, tag) using json_each; events without tags produce no rows.




-- 20. events: total amount per user, treating missing amount as 0.




-- 21. products: build a single JSON array of objects {id, name} with trimmed names.



