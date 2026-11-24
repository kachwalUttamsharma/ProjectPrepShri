import pytest

from exercises import *
from schema import assert_result, make_db


@pytest.fixture
def db():
    return make_db()


def test_nyc_employees(db):
    assert_result(db, nyc_employees(), ["name", "salary"], [
        ("Alice", 120000), ("Carol", 105000), ("Frank", 82000),
        ("Heidi", 72000), ("Mallory", 68000)])


def test_high_earners(db):
    assert_result(db, high_earners(), ["name", "salary"], [
        ("Alice", 120000), ("Carol", 105000), ("Bob", 95000), ("Ivan", 95000)],
        ordered=True)


def test_top3_paid(db):
    assert_result(db, top3_paid(), ["name", "salary"], [
        ("Alice", 120000), ("Carol", 105000), ("Bob", 95000)], ordered=True)


def test_page_two(db):
    assert_result(db, page_two(), ["id", "name"], [
        (5, "Eve"), (6, "Frank"), (7, "Grace"), (8, "Heidi")], ordered=True)


def test_hired_2019_2020(db):
    assert_result(db, hired_2019_2020(), ["name", "hire_date"], [
        ("Alice", "2019-03-15"), ("Heidi", "2019-06-25"),
        ("Bob", "2020-07-01"), ("Grace", "2020-11-12")], ordered=True)


def test_names_ending_in_e(db):
    assert_result(db, names_ending_in_e(), ["name"],
                  [("Alice",), ("Dave",), ("Eve",), ("Grace",)])


def test_no_bonus_recorded(db):
    assert_result(db, no_bonus_recorded(), ["name"],
                  [("Bob",), ("Eve",), ("Grace",), ("Judy",), ("Niaj",), ("Oleg",)])


def test_total_compensation(db):
    assert_result(db, total_compensation(), ["name", "total_comp"], [
        ("Alice", 125000), ("Carol", 113000), ("Ivan", 96000), ("Bob", 95000),
        ("Frank", 88000), ("Heidi", 74000), ("Dave", 73000), ("Judy", 68000),
        ("Mallory", 68000), ("Eve", 65000), ("Grace", 60000), ("Oleg", 50000)], ordered=True)


def test_not_in_hr(db):
    names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Ivan",
             "Judy", "Mallory", "Niaj", "Oleg"]
    assert_result(db, not_in_hr(), ["name"], [(n,) for n in names])


def test_distinct_cities(db):
    assert_result(db, distinct_cities(), ["city"], [("NYC",), ("SF",), ("Austin",)])


def test_null_aware_counts(db):
    assert_result(db, null_aware_counts(),
                  ["total_rows", "salary_count", "bonus_count"], [(13, 12, 7)])


def test_avg_salary_by_dept(db):
    assert_result(db, avg_salary_by_dept(), ["dept", "headcount", "avg_salary"], [
        ("Engineering", 4, 103750.0), ("Sales", 4, 72333.33),
        ("HR", 2, 66000.0), ("Marketing", 2, 68000.0)])


def test_big_departments(db):
    assert_result(db, big_departments(), ["dept", "headcount"],
                  [("Engineering", 4), ("Sales", 4)])


def test_revenue_by_status(db):
    assert_result(db, revenue_by_status(), ["status", "order_count", "total_amount"], [
        ("shipped", 7, 1545.0), ("cancelled", 2, 95.5), ("pending", 3, 140.0)])


def test_monthly_shipped_revenue(db):
    assert_result(db, monthly_shipped_revenue(), ["month", "revenue"], [
        ("2024-01", 350.0), ("2024-02", 425.0), ("2024-03", 770.0)], ordered=True)


def test_big_customers(db):
    assert_result(db, big_customers(), ["customer", "total"], [
        ("acme", 750.0), ("globex", 300.0), ("hooli", 240.0)], ordered=True)


def test_distinct_city_count(db):
    assert_result(db, distinct_city_count(), ["cities"], [(3,)])


def test_small_or_unknown_orders(db):
    assert_result(db, small_or_unknown_orders(), ["id"],
                  [(2,), (3,), (5,), (8,), (10,), (11,)])
