-- Part 05 practice. Load schema: sqlite3 bank.db < setup.sql
-- Tasks 1-4 and 10-11 are two-session scenarios: open two terminals.
--   SQLite:   sqlite3 bank.db   in both terminals (single writer; observe SQLITE_BUSY "database is locked").
--   Postgres: two psql sessions (not run here, verify; Docker one-liner in ../README.md). Adapt setup.sql types if needed.
-- Write your answers/notes in the blank spaces.

-- TASK 1 (SQLite, two terminals): In A run BEGIN IMMEDIATE; UPDATE accounts SET balance = balance - 10 WHERE id = 1;
-- In B run BEGIN IMMEDIATE;  What happens? Then try a plain SELECT in B. Write what you saw and why.



-- TASK 2 (SQLite): Repeat Task 1 after PRAGMA journal_mode=WAL; in both. What changes for B's SELECT? Why?



-- TASK 3 (Postgres, two sessions): Demonstrate a non-repeatable read at READ COMMITTED.
-- Write the exact statements for session A and session B, in order, as comments + SQL.



-- TASK 4 (Postgres, two sessions): Repeat Task 3 at REPEATABLE READ. Then make both sessions
-- UPDATE the same row; which one errors and with what message?



-- TASK 5: Optimistic locking. Reader R1 read account 1 with version = 1.
-- Write the UPDATE that subtracts 30 only if the version is unchanged, bumps the version, then
-- the statement that tells you whether it worked.



-- TASK 6: A second reader R2 also read version = 1 earlier and now subtracts 10 the same way. Write it,
-- and say what the "rows affected" value is and what R2 must do next.



-- TASK 7: Lost update. Write the single statement that adds 5 to bob's balance without reading it first.
-- Explain in a comment why this cannot lose updates.



-- TASK 8: Job queue. Write a single statement that claims the lowest-id queued job for worker 'w1' and
-- returns its id and payload (SQLite 3.35+ supports RETURNING).



-- TASK 9: Write a transaction that tries to take 500 from bob (balance 50). What stops it?
-- Show BEGIN ... ROLLBACK. Then say what you would check in application code.



-- TASK 10 (Postgres, not run here, verify): Rewrite Task 8 for many concurrent workers using FOR UPDATE SKIP LOCKED.
-- Why does plain "SELECT ... LIMIT 1" followed by UPDATE hand the same job to two workers?



-- TASK 11 (Postgres, two sessions): Write skew. Table oncall(dr_a=1, dr_b=1). Each session checks
-- "SELECT COUNT(*) FROM oncall WHERE on_call = 1" > 1 then sets its own doctor to 0.
-- (a) Show the interleaving that leaves nobody on call under REPEATABLE READ.
-- (b) Give two different fixes.



-- TASK 12: Deadlock design. Two transfers: 1->2 and 2->1 run concurrently, each updating its source row first.
-- Explain the cycle, then rewrite the transfer so it cannot deadlock (hint: order of locking).



-- TASK 13 (reading): Write a 5-step expand/contract plan for renaming accounts.owner to accounts.owner_name
-- on a live system with zero downtime.



-- TASK 14 (reading): Your company needs RPO 5 minutes, RTO 30 minutes on Postgres. Which backup + log
-- archiving + replica setup would you propose, and what do you test monthly?

