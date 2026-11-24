-- Part 05 setup. Run: sqlite3 bank.db < setup.sql   (or sqlite3 :memory: then .read setup.sql)
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS oncall;

CREATE TABLE accounts (
  id      INTEGER PRIMARY KEY,
  owner   TEXT NOT NULL,
  balance INTEGER NOT NULL CHECK (balance >= 0),
  version INTEGER NOT NULL DEFAULT 1
);
INSERT INTO accounts (id, owner, balance) VALUES
  (1, 'alice', 100), (2, 'bob', 50), (3, 'carol', 0);

CREATE TABLE jobs (
  id         INTEGER PRIMARY KEY,
  payload    TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'queued',   -- queued / running / done
  claimed_by TEXT
);
INSERT INTO jobs (payload) VALUES ('a'), ('b'), ('c'), ('d');

-- write-skew playground: at least one doctor must stay on call
CREATE TABLE oncall (doctor TEXT PRIMARY KEY, on_call INTEGER NOT NULL);
INSERT INTO oncall VALUES ('dr_a', 1), ('dr_b', 1);
