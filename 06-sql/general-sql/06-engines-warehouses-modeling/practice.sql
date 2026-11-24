-- Part 06 practice. Run:  sqlite3 :memory: ".read setup.sql" ".read practice.sql"
-- Write each query under its task. Compare with your own reasoning first; reference
-- solutions are kept outside the repo (/tmp/ref-generalsql/06/solutions.sql).
.headers on
.mode column

-- T1. Total revenue (SUM of amount) per product category. Highest first.


-- T2. Revenue per year-quarter-month: show month and total, ordered by month.
--     (Join the date dimension.)


-- T3. Which customers (name) have never bought anything? Dimension-side anti-join.


-- T4. Revenue by customer region, with a RANK() over total revenue (highest = 1).


-- T5. Share of revenue that happened on weekends, as a percentage rounded to 1 decimal.


-- T6. For each category, the single best-selling product by revenue (ties: lowest product name).
--     Hint: window function or correlated subquery.


-- T7. Running total of revenue by date_key across the whole fact table (one row per date).


-- T8. (SCD2) Apply stg_customer to dim_customer_scd2 with the two-step close-then-insert pattern.
--     Use '2024-09-01' as the change date. Wrap in BEGIN; ... COMMIT;


-- T9. (SCD2) After T8: list each customer's city as of '2024-02-01' (half-open range).


-- T10. (SCD2) How many versions does each customer have? Show only customers with more than one.


-- T11. (SCD2 trap) Explain in a comment why joining a fact to dim_customer_scd2 by customer_id
--      alone double counts, and write the join condition that fixes it given a sale date column sale_date.
--      (No query to run; answer in comments.)


-- T12. Thought questions (answer in comments, no SQL):
--   a) State the grain of fact_sales.
--   b) Which of quantity, amount, and an average_price column are additive?
--   c) Where would partitioning help if fact_sales had 5 billion rows? On which column?
--   d) Why might SELECT * be a bad idea on BigQuery but harmless on SQLite?
