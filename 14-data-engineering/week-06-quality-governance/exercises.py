"""Week 6 exercises: data quality and governance, stdlib + sqlite3.

Replace each `...` with your code. Run the tests with:
    ../../.venv/bin/pytest -q
Rows are lists of dicts, e.g. [{"id": 1, "email": "a@x.com"}, ...].
"""
import hashlib
import sqlite3
from collections import namedtuple
from datetime import datetime, timedelta  # noqa: F401  (handy for freshness)
import statistics  # noqa: F401  (handy for volume anomaly)
import math  # noqa: F401  (handy for PSI)
import re  # noqa: F401  (handy for masking)

# Result of one data-quality check: provided for you.
#   name: str, passed: bool, details: dict
CheckResult = namedtuple("CheckResult", ["name", "passed", "details"])


# Exercise 1a ------------------------------------------------------------
def check_not_null(rows, column, max_null_ratio=0.0):
    """Completeness check.

    A value is "null" if it is None or a str that is empty/whitespace-only.
    A missing key counts as null too (use row.get).
    Return CheckResult(name=f"not_null:{column}", passed=null_ratio <=
    max_null_ratio, details={"null_count": n, "total": len(rows),
    "null_ratio": ratio}). Empty `rows` -> passed True, ratio 0.0.
    """
    ...


# Exercise 1b ------------------------------------------------------------
def check_range(rows, column, min_value=None, max_value=None):
    """Validity check: values must lie in [min_value, max_value] (inclusive;
    a bound of None is not enforced). None values are skipped (completeness
    is a different check).
    Return CheckResult(name=f"range:{column}", passed=no violations,
    details={"violations": [row indexes that are out of range]}).
    """
    ...


# Exercise 1c ------------------------------------------------------------
def run_checks(checks):
    """Run a list of zero-arg callables, each returning a CheckResult.

    A check that RAISES must not crash the run: record it as a failed result
    with name=getattr(check, "__name__", "unknown") and
    details={"error": str(exc)}.
    Return {"passed": all passed, "results": [CheckResult...] in order,
    "failed": [names of failed checks]}.
    Hint: functools.partial / lambda is how callers bind rows and columns.
    """
    ...


# Exercise 2 -------------------------------------------------------------
def find_duplicate_keys(rows, key_columns):
    """Uniqueness check on a (composite) key.

    Return {key_tuple: [row indexes]} containing ONLY keys that occur more
    than once. key_tuple is a tuple of the values of key_columns, in order.
    >>> find_duplicate_keys([{"id": 1}, {"id": 2}, {"id": 1}], ["id"])
    {(1,): [0, 2]}
    """
    ...


# Exercise 3 -------------------------------------------------------------
def check_schema_compat(old, new, mode):
    """Schema evolution compatibility (Avro-like, simplified).

    A schema is {field_name: {"type": "int"|"string"|..., "default": <opt>}}.
    A field WITHOUT a "default" key is required (no default).
    Modes:
      "backward": consumers using `new` must read data written with `old`.
          Violations: a field added in new without a default;
                      a field whose type changed.
      "forward": consumers using `old` must read data written with `new`.
          Violations: a field removed in new that had no default in old;
                      a field whose type changed.
      "full": both sets of rules.
    Return a sorted list of human-readable violation strings, each containing
    the offending field name. [] means compatible. Unknown mode -> ValueError.
    Hint: compare set(old) and set(new); "default" in spec checks presence
    (a default of None still counts as a default).
    """
    ...


# Exercise 4 -------------------------------------------------------------
def check_freshness(last_updated, now, max_age):
    """Timeliness check. `last_updated` and `now` are datetimes, `max_age` a
    timedelta. Passed iff now - last_updated <= max_age.
    A last_updated of None means the table never loaded: failed.
    Return CheckResult(name="freshness", passed, details={"age_seconds":
    float or None, "max_age_seconds": float}).
    A future last_updated (clock skew) has negative age and passes.
    """
    ...


# Exercise 5 -------------------------------------------------------------
def detect_volume_anomaly(history, today, threshold=3.5):
    """Detect an abnormal daily row count with a robust (median/MAD) score.

    modified_z = 0.6745 * (today - median) / MAD, where MAD is the median of
    |x - median| over `history`. Anomaly iff |modified_z| > threshold.
    Edge cases: MAD == 0 -> anomaly iff today != median.
    Fewer than 3 history points -> return False (not enough evidence).
    Return a bool. (Median/MAD beats mean/stdev because past outages in the
    history don't inflate the baseline.)
    """
    ...


# Exercise 6 -------------------------------------------------------------
def find_orphans(conn, child_table, child_col, parent_table, parent_col):
    """Referential integrity via SQL.

    Return a sorted list of DISTINCT non-NULL values of child_table.child_col
    that have no matching parent_table.parent_col. Use a single SQL query
    (LEFT JOIN ... IS NULL or NOT EXISTS), not a Python loop over rows.
    Table/column names are trusted identifiers here (in production validate
    them against a whitelist: identifiers cannot be bound as parameters).
    """
    ...


# Exercise 7a ------------------------------------------------------------
def mask_email(email):
    """Mask an email for non-privileged users: keep the first character of the
    local part and the whole domain, replace the remaining local-part chars
    with '*'.
    "alice@example.com" -> "a****@example.com"
    "b@x.org" -> "b@x.org" (single char: nothing to mask)
    A value without exactly one '@' -> "***".
    """
    ...


# Exercise 7b ------------------------------------------------------------
def mask_phone(phone):
    """Replace every digit with '*' EXCEPT the last 4 digits; keep all other
    characters (+, spaces, dashes, parentheses) as they are.
    "+1 (415) 555-0134" -> "+* (***) ***-0134"
    Fewer than 4 digits: leave unchanged.
    Hint: count digits first, then rebuild char by char (or re.sub with a
    function).
    """
    ...


# Exercise 8 -------------------------------------------------------------
def reconcile_tables(conn, table_a, table_b, key, columns):
    """Reconcile two tables (e.g. source vs warehouse copy) after a load or
    backfill.

    Compare on `key` plus the `columns` list. Return a dict:
      "count_a", "count_b": row counts
      "only_in_a", "only_in_b": sorted lists of keys present on one side only
      "mismatched": sorted list of keys present in both whose `columns`
          values differ
      "checksum_match": True iff both tables have the same multiset of rows
          over [key] + columns (an order-independent checksum, e.g. sum of
          per-row hash ints, or compare sorted rows)
      "ok": True iff no only_in_*, no mismatches and counts equal
    Table/column names are trusted identifiers. Keys are unique.
    """
    ...


# Exercise 9 -------------------------------------------------------------
def population_stability_index(expected, actual, bins=5):
    """Distribution drift: PSI between a baseline sample and a new sample.

    1. Build `bins` equal-width bins over [min(expected), max(expected)];
       values of `actual` outside that range are clamped into the first/last
       bin.
    2. e_i, a_i = share of each sample in bin i; replace any share of 0 by
       1e-4 (avoid log(0)).
    3. PSI = sum((a_i - e_i) * ln(a_i / e_i)).
    Rule of thumb: <0.1 stable, 0.1-0.25 moderate drift, >0.25 major.
    If all `expected` values are equal, use a single bin (PSI then 0.0 unless
    you choose otherwise: return 0.0).
    """
    ...


# Exercise 10 ------------------------------------------------------------
def erase_subject(conn, table, id_column, subject_id, pii_columns):
    """Right-to-erasure by anonymization.

    UPDATE every row of `table` where id_column = subject_id, setting each of
    pii_columns to NULL (keep the row and non-PII columns so aggregates and
    foreign keys survive). Use a bound parameter for subject_id.
    Return the number of rows updated. Commit the change.
    Raise ValueError if pii_columns is empty.
    """
    ...
