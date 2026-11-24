import pytest

from exercises import *
from schema import assert_result, make_db


@pytest.fixture
def db():
    return make_db()


def test_above_average_payroll_depts(db):
    assert_result(db, above_average_payroll_depts(), ["dept", "payroll"],
                  [("Eng", 520000), ("Sales", 310000)])


def test_subordinates_of_ben(db):
    assert_result(db, subordinates_of_ben(), ["name", "level"],
                  [("Cara", 1), ("Dan", 1), ("Eli", 2)], ordered=True)


def test_date_series(db):
    days = [(f"2024-01-0{i}",) for i in range(1, 8)]
    assert_result(db, date_series(), ["day"], days, ordered=True)


def test_chain_to_ceo(db):
    assert_result(db, chain_to_ceo(), ["name", "depth"],
                  [("Eli", 0), ("Cara", 1), ("Ben", 2), ("Ava", 3)], ordered=True)


def test_dept_salary_rownumber(db):
    assert_result(db, dept_salary_rownumber(), ["name", "dept", "rn"], [
        ("Ben", "Eng", 1), ("Cara", "Eng", 2), ("Dan", "Eng", 3), ("Eli", "Eng", 4),
        ("Ava", "Exec", 1), ("Jo", "HR", 1), ("Kim", "HR", 2),
        ("Fay", "Sales", 1), ("Gus", "Sales", 2), ("Hana", "Sales", 3), ("Ian", "Sales", 4)],
        ordered=True)


def test_company_rank_dense(db):
    assert_result(db, company_rank_dense(), ["name", "salary", "rnk", "drnk"], [
        ("Ava", 200000, 1, 1), ("Ben", 150000, 2, 2), ("Cara", 150000, 2, 2),
        ("Dan", 120000, 4, 3), ("Eli", 100000, 5, 4), ("Fay", 90000, 6, 5),
        ("Gus", 90000, 6, 5), ("Jo", 80000, 8, 6), ("Hana", 70000, 9, 7),
        ("Kim", 65000, 10, 8), ("Ian", 60000, 11, 9)], ordered=True)


def test_top_two_salaries_per_dept(db):
    assert_result(db, top_two_salaries_per_dept(), ["name", "dept", "salary"], [
        ("Ben", "Eng", 150000), ("Cara", "Eng", 150000), ("Dan", "Eng", 120000),
        ("Ava", "Exec", 200000), ("Jo", "HR", 80000), ("Kim", "HR", 65000),
        ("Fay", "Sales", 90000), ("Gus", "Sales", 90000), ("Hana", "Sales", 70000)])


def test_running_sales_total(db):
    assert_result(db, running_sales_total(), ["id", "sale_date", "amount", "running_total"], [
        (1, "2024-01-03", 100, 100), (2, "2024-01-15", 200, 300), (3, "2024-01-28", 150, 450),
        (4, "2024-02-02", 120, 570), (5, "2024-02-14", 300, 870), (6, "2024-02-20", 80, 950),
        (7, "2024-03-05", 250, 1200), (8, "2024-03-18", 400, 1600), (9, "2024-03-25", 50, 1650)],
        ordered=True)


def test_running_total_by_region(db):
    assert_result(db, running_total_by_region(), ["id", "region", "amount", "region_running"], [
        (1, "East", 100, 100), (3, "East", 150, 250), (5, "East", 300, 550),
        (7, "East", 250, 800), (9, "East", 50, 850),
        (2, "West", 200, 200), (4, "West", 120, 320), (6, "West", 80, 400), (8, "West", 400, 800)],
        ordered=True)


def test_month_over_month(db):
    assert_result(db, month_over_month(), ["month", "revenue", "prev_revenue", "change"], [
        ("2024-01", 450, None, None), ("2024-02", 500, 450, 50), ("2024-03", 700, 500, 200)],
        ordered=True)


def test_days_to_next_sale(db):
    assert_result(db, days_to_next_sale(), ["id", "region", "days_to_next"], [
        (1, "East", 25), (3, "East", 17), (5, "East", 20), (7, "East", 20), (9, "East", None),
        (2, "West", 18), (4, "West", 18), (6, "West", 27), (8, "West", None)])


def test_moving_average_3(db):
    assert_result(db, moving_average_3(), ["id", "avg3"], [
        (1, 100.0), (2, 150.0), (3, 150.0), (4, 156.67), (5, 190.0),
        (6, 166.67), (7, 210.0), (8, 243.33), (9, 233.33)], ordered=True)


def test_pct_of_region(db):
    assert_result(db, pct_of_region(), ["id", "region", "amount", "pct"], [
        (1, "East", 100, 11.8), (3, "East", 150, 17.6), (5, "East", 300, 35.3),
        (7, "East", 250, 29.4), (9, "East", 50, 5.9),
        (2, "West", 200, 25.0), (4, "West", 120, 15.0), (6, "West", 80, 10.0),
        (8, "West", 400, 50.0)])


def test_salary_band(db):
    assert_result(db, salary_band(), ["name", "band"], [
        ("Ava", "High"), ("Ben", "High"), ("Cara", "High"), ("Dan", "Mid"), ("Eli", "Mid"),
        ("Fay", "Mid"), ("Gus", "Mid"), ("Hana", "Low"), ("Ian", "Low"), ("Jo", "Low"),
        ("Kim", "Low")])


def test_pivot_monthly_by_region(db):
    assert_result(db, pivot_monthly_by_region(), ["month", "east", "west"], [
        ("2024-01", 250, 200), ("2024-02", 300, 200), ("2024-03", 300, 400)], ordered=True)


def test_high_earner_counts(db):
    assert_result(db, high_earner_counts(), ["dept", "high_paid", "total"], [
        ("Eng", 4, 4), ("Exec", 1, 1), ("HR", 0, 2), ("Sales", 0, 4)])


def test_first_hire_in_dept(db):
    assert_result(db, first_hire_in_dept(), ["name", "dept", "first_hire"], [
        ("Ava", "Exec", "Ava"), ("Ben", "Eng", "Ben"), ("Cara", "Eng", "Ben"),
        ("Dan", "Eng", "Ben"), ("Eli", "Eng", "Ben"), ("Fay", "Sales", "Fay"),
        ("Gus", "Sales", "Fay"), ("Hana", "Sales", "Fay"), ("Ian", "Sales", "Fay"),
        ("Jo", "HR", "Jo"), ("Kim", "HR", "Jo")])


def test_diff_from_dept_avg(db):
    assert_result(db, diff_from_dept_avg(), ["name", "dept", "diff"], [
        ("Ava", "Exec", 0.0), ("Ben", "Eng", 20000.0), ("Cara", "Eng", 20000.0),
        ("Dan", "Eng", -10000.0), ("Eli", "Eng", -30000.0), ("Fay", "Sales", 12500.0),
        ("Gus", "Sales", 12500.0), ("Hana", "Sales", -7500.0), ("Ian", "Sales", -17500.0),
        ("Jo", "HR", 7500.0), ("Kim", "HR", -7500.0)])


def test_ticket_resolution_hours(db):
    assert_result(db, ticket_resolution_hours(), ["id", "hours"],
                  [(1, 8.5), (2, 48.0), (4, 1.5), (5, 168.0)], ordered=True)


def test_tickets_per_month(db):
    assert_result(db, tickets_per_month(), ["month", "opened", "still_open"],
                  [("2024-03", 4, 1), ("2024-04", 2, 1)], ordered=True)


def test_stale_open_tickets(db):
    assert_result(db, stale_open_tickets(), ["id", "days_open"], [(3, 47)])
