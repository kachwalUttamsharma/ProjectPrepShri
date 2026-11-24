-- Part 01 sample schema + data. Runs in: sqlite3 :memory: < setup.sql   (or  sqlite3 mydb.db < setup.sql)
PRAGMA foreign_keys = ON;   -- SQLite only: FK enforcement is OFF by default and per-connection

DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
    id      INTEGER PRIMARY KEY,
    code    TEXT NOT NULL UNIQUE,
    title   TEXT NOT NULL,
    credits INTEGER NOT NULL DEFAULT 3 CHECK (credits BETWEEN 1 AND 10)
);

CREATE TABLE students (
    id        INTEGER PRIMARY KEY,
    email     TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    city      TEXT,
    joined_on TEXT NOT NULL DEFAULT '2024-01-01'
);

CREATE TABLE enrollments (
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id  INTEGER NOT NULL REFERENCES courses(id)  ON DELETE RESTRICT,
    grade      INTEGER CHECK (grade BETWEEN 0 AND 100),
    PRIMARY KEY (student_id, course_id)
);

INSERT INTO courses (id, code, title, credits) VALUES
 (1, 'DB101',  'Intro to Databases', 4),
 (2, 'PY101',  'Python Basics',      3),
 (3, 'ML201',  'Machine Learning',   5);

INSERT INTO students (id, email, full_name, city, joined_on) VALUES
 (1, 'asha@example.com',  'Asha Rao',   'Pune',   '2024-02-10'),
 (2, 'ben@example.com',   'Ben Carter', 'Austin', '2024-03-05'),
 (3, 'chen@example.com',  'Chen Li',    NULL,     '2024-03-20'),
 (4, 'dina@example.com',  'Dina Ortiz', 'Austin', '2024-04-01');

INSERT INTO enrollments (student_id, course_id, grade) VALUES
 (1, 1, 91), (1, 2, 85), (2, 1, 70), (3, 3, NULL), (4, 2, 60);
