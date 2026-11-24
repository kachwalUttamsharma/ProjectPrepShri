-- Part 01 practice. Setup first:  sqlite3 mydb.db < setup.sql
-- Then write your answer under each task and run:  sqlite3 mydb.db < practice.sql
-- (Tasks build on each other; if you wreck the data, rerun setup.sql, it drops and recreates the tables.)
-- Run in a transaction when experimenting: BEGIN; ... ROLLBACK;
.headers on
.mode column

-- T1. Create table instructors(id integer primary key, name text not null,
--     email text unique, rating real constrained to 0..5 inclusive).


-- T2. Add a nullable column instructor_id to courses that references instructors(id).


-- T3. Insert two instructors in ONE statement: (1,'Dr. Rao','rao@example.com',4.5)
--     and (2,'Ms. Kim','kim@example.com', no rating).


-- T4. Assign instructor 1 to the courses with codes DB101 and PY101 (single UPDATE).


-- T5. Add 5 points to every grade in course 1, but leave NULL grades alone.
--     Then SELECT the enrollments to check (no student should exceed 100; think about whether you need a guard).


-- T6. Upsert: a student with email 'asha@example.com' now lives in 'Mumbai' and is named 'Asha R. Rao'.
--     Use INSERT ... ON CONFLICT so that no new row appears. SELECT * afterwards.


-- T7. Try to insert a duplicate email 'ben@example.com' so that it is silently skipped.
--     Verify the student count did not change.


-- T8. Predict first, then run: INSERT INTO enrollments VALUES (1,1,50);  What error and why?
--     Write your prediction as a comment here:


-- T9. Predict first, then run: DELETE FROM courses WHERE id = 1;  Why does it fail?
--     Which FK clause causes this? What would change if it were CASCADE?


-- T10. Delete student 3 and see what was deleted using RETURNING. Then count enrollments:
--      explain in a comment why the count dropped.


-- T11. In a transaction: delete ALL enrollments, count them, ROLLBACK, count again.


-- T12. Insert a new student (email only + name) and use RETURNING to get the generated id and joined_on default.


-- T13. Write (as comments, you cannot run them in SQLite) the Postgres, MySQL and SQL Server versions of:
--      "id column that auto-generates a bigint primary key".
-- Postgres:
-- MySQL:
-- SQL Server:


-- T14. Write (comment) a Postgres 15+ MERGE that syncs students from a table staging_students (email, full_name, city):
--      update when matched and name differs, insert when not matched.


-- T15. Using a safe habit: write the SELECT that previews which rows UPDATE students SET city = 'Unknown' WHERE city IS NULL
--      would change, then do the UPDATE inside BEGIN/ROLLBACK and print the row count with changes().
