import pytest

from exercises import *
from schema import assert_result, make_db


@pytest.fixture
def db():
    return make_db()


# ---------------------------------------------------------------- warm-up
def test_second_highest_salary(db):
    assert_result(db, second_highest_salary(), ["second_highest"], [(95000,)])


def test_duplicate_emails(db):
    assert_result(db, duplicate_emails(), ["email", "cnt"], [("a@x.com", 3), ("b@x.com", 2)])


def test_duplicate_ids_to_delete(db):
    assert_result(db, duplicate_ids_to_delete(), ["id"], [(3,), (5,), (6,)])


def test_earn_more_than_manager(db):
    assert_result(db, earn_more_than_manager(), ["name"], [("Eve",), ("Hal",), ("Ivy",), ("Jon",)])


def test_managers_with_three_reports(db):
    assert_result(db, managers_with_three_reports(), ["name"], [("Ann",), ("Dev",)])


def test_customers_bought_every_category(db):
    assert_result(db, customers_bought_every_category(), ["customer"], [("ann",)])


# ------------------------------------------------------------- top-N etc.
def test_department_top_earners(db):
    assert_result(db, department_top_earners(), ["dept", "employee", "salary"], [
        ("Eng", "Jon", 100000), ("Sales", "Eve", 95000), ("Ops", "Hal", 85000), ("Ops", "Ivy", 85000)])


def test_top2_products_per_category(db):
    assert_result(db, top2_products_per_category(), ["category", "product", "revenue"], [
        ("Furniture", "Desk", 500), ("Furniture", "Chair", 250),
        ("Stationery", "Book", 160), ("Stationery", "Pen", 75)], ordered=True)


def test_median_salary_per_dept(db):
    assert_result(db, median_salary_per_dept(), ["dept", "median"],
                  [("Eng", 85000.0), ("Sales", 65000.0), ("Ops", 85000.0)])


def test_first_order_per_customer(db):
    assert_result(db, first_order_per_customer(), ["customer", "order_date", "amount"], [
        ("ann", "2024-01-05", 50), ("bob", "2024-01-10", 80), ("cy", "2024-02-01", 20)])


def test_best_customer_each_month(db):
    assert_result(db, best_customer_each_month(), ["month", "customer", "total"], [
        ("2024-01", "ann", 120), ("2024-02", "bob", 120), ("2024-03", "ann", 100)], ordered=True)


# ----------------------------------------------------- gaps and islands etc.
def test_consecutive_login_users(db):
    assert_result(db, consecutive_login_users(), ["user_id"], [(1,), (3,)])


def test_longest_login_streak(db):
    assert_result(db, longest_login_streak(), ["user_id", "longest_streak"],
                  [(1, 3), (2, 1), (3, 5), (4, 2)])


def test_id_islands(db):
    assert_result(db, id_islands(), ["start_id", "end_id"],
                  [(1, 3), (7, 8), (10, 10), (15, 17)], ordered=True)


def test_missing_id_ranges(db):
    assert_result(db, missing_id_ranges(), ["gap_start", "gap_end"],
                  [(4, 6), (9, 9), (11, 14)], ordered=True)


def test_sessions_per_user(db):
    assert_result(db, sessions_per_user(), ["user_id", "sessions"], [(1, 3), (2, 2), (3, 1)])


# ------------------------------------------------------------- time series
def test_running_balance(db):
    assert_result(db, running_balance(), ["id", "account", "amount", "balance"], [
        (1, "A", 100, 100), (2, "A", -30, 70), (4, "A", 20, 90),
        (3, "B", 50, 50), (5, "B", -10, 40), (6, "B", 70, 110)], ordered=True)


def test_rolling_7day_average(db):
    assert_result(db, rolling_7day_average(), ["day", "avg7"], [
        ("2024-03-07", 40.0), ("2024-03-08", 51.43), ("2024-03-09", 58.57),
        ("2024-03-10", 70.0)], ordered=True)


def test_month_over_month_growth(db):
    assert_result(db, month_over_month_growth(), ["month", "revenue", "growth_pct"], [
        ("2024-01", 120, None), ("2024-02", 30, -75.0), ("2024-03", 450, 1400.0),
        ("2024-04", 90, -80.0), ("2024-05", 60, -33.3), ("2024-06", 200, 233.3),
        ("2024-07", 25, -87.5), ("2024-08", 100, 300.0), ("2024-09", 80, -20.0)], ordered=True)


def test_avg_days_between_orders(db):
    assert_result(db, avg_days_between_orders(), ["customer", "avg_gap_days"],
                  [("ann", 21.67), ("bob", 27.5), ("cy", 19.0)])


# ------------------------------------------------------ product analytics
def test_day1_retention(db):
    assert_result(db, day1_retention(), ["cohort", "users", "retained", "retention_pct"], [
        ("2024-03-01", 3, 2, 66.7), ("2024-03-02", 2, 1, 50.0)], ordered=True)


def test_purchase_funnel(db):
    assert_result(db, purchase_funnel(), ["step", "users", "pct_of_first"], [
        ("view", 6, 100.0), ("cart", 4, 66.7), ("purchase", 2, 33.3)], ordered=True)


# ------------------------------------------------------------- reshaping
def test_pivot_quarterly_sales(db):
    assert_result(db, pivot_quarterly_sales(), ["category", "q1", "q2", "q3"], [
        ("Stationery", 150, 100, 25), ("Furniture", 450, 250, 180)])


def test_revenue_share_pct(db):
    assert_result(db, revenue_share_pct(), ["product", "revenue", "pct"], [
        ("Pen", 75, 6.5), ("Book", 160, 13.9), ("Desk", 500, 43.3),
        ("Chair", 250, 21.6), ("Lamp", 130, 11.3), ("Ink", 40, 3.5)])


def test_swap_adjacent_seats(db):
    assert_result(db, swap_adjacent_seats(), ["id", "student"], [
        (1, "Doris"), (2, "Abbot"), (3, "Green"), (4, "Emerson"), (5, "Jeames")], ordered=True)


def test_salary_histogram(db):
    assert_result(db, salary_histogram(), ["band", "n"],
                  [("<60k", 1), ("60-80k", 3), ("80-100k", 6), ("100k+", 1)])
