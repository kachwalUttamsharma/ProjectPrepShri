-- Part 04 practice. Setup: sqlite3 :memory:  then  .read setup.sql  then  .read practice.sql
-- (or paste tasks one by one). Tables: customers, orders, order_items; no secondary indexes yet.
-- Use EXPLAIN QUERY PLAN <query>; before and after each change and note SCAN vs SEARCH.

-- Task 1. Show the plan for: all orders of customer 42. Create an index so it becomes a SEARCH. Show the new plan.



-- Task 2. Orders with status='paid' and created_at >= '2024-06-01'. Create a composite index
-- with the right column order. Then check whether a query filtering ONLY on created_at can use it
-- (leftmost-prefix rule). Explain what you see in a comment.



-- Task 3. SUM(total_cents) for customer 42. Make the plan say COVERING INDEX.



-- Task 4. Find the customer whose lower(email) = 'user7@example.com'. Show SCAN, then fix it with a functional index.



-- Task 5. Orders with status='pending' and created_at > '2024-12-01'. Create a PARTIAL index
-- that serves exactly this. (Hint: drop other orders indexes if the planner prefers them.)



-- Task 6. Show the plan for customers WHERE email LIKE '%99@example.com'. Why can't a B-tree help? Answer in a comment.



-- Task 7. Per US customer (country='US'): total spent = SUM(qty*price_cents) over order_items.
-- Check the join plan with no secondary indexes; add the indexes needed on both FK columns; compare plans. Note which table is scanned first.



-- Task 8. N+1: in a comment write the two-step loop you would see in an ORM for "order id and item count for customer 42".
-- Then write ONE query that gives the same result.



-- Task 9. Top 10 newest orders (ORDER BY created_at DESC LIMIT 10). Find USE TEMP B-TREE in the plan, then remove it with an index.



-- Task 10. Keyset pagination: write the "next page" query after the last row seen was (created_at='2024-06-01', id=3000),
-- ordered newest first with id as tie-breaker, 10 rows.



-- Task 11. Rewrite so an index on created_at can be used: WHERE strftime('%Y-%m', created_at) = '2024-06'.



-- Task 12. Run ANALYZE; then SELECT * FROM sqlite_stat1; In a comment explain what the two numbers in "stat" mean for one of your indexes.



-- Task 13 (reading, Postgres/MySQL, no DB needed). In a comment answer: a Postgres plan node says
-- "rows=10 ... actual rows=95000 loops=1". What are two likely causes and two fixes?



-- Task 14 (design). In a comment: which index type would you pick in Postgres for (a) JSONB containment queries,
-- (b) a 2 TB append-only log table filtered by timestamp range, (c) LIKE '%foo%' search? One sentence each.

