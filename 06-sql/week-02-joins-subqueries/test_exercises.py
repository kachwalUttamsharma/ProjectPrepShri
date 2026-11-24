import pytest

from exercises import *
from schema import assert_result, make_db


@pytest.fixture
def db():
    return make_db()


def test_inner_join_employee_dept(db):
    assert_result(db, inner_join_employee_dept(), ["employee", "department"], [
        ("Ava", "Engineering"), ("Ben", "Engineering"), ("Cara", "Engineering"),
        ("Jo", "Engineering"), ("Dan", "Sales"), ("Eli", "Sales"), ("Fay", "Sales"),
        ("Gus", "HR"), ("Hana", "HR")])


def test_all_employees_with_dept(db):
    assert_result(db, all_employees_with_dept(), ["employee", "department"], [
        ("Ava", "Engineering"), ("Ben", "Engineering"), ("Cara", "Engineering"),
        ("Jo", "Engineering"), ("Dan", "Sales"), ("Eli", "Sales"), ("Fay", "Sales"),
        ("Gus", "HR"), ("Hana", "HR"), ("Ian", None)])


def test_empty_departments(db):
    assert_result(db, empty_departments(), ["name"], [("Legal",)])


def test_unassigned_employees(db):
    assert_result(db, unassigned_employees(), ["name"], [("Fay",), ("Gus",), ("Hana",)])


def test_employee_manager_pairs(db):
    assert_result(db, employee_manager_pairs(), ["employee", "manager"], [
        ("Ben", "Ava"), ("Cara", "Ben"), ("Dan", "Ava"), ("Eli", "Dan"),
        ("Fay", "Dan"), ("Gus", "Ava"), ("Hana", "Gus"), ("Ian", "Ava"), ("Jo", "Ben")])


def test_earn_more_than_manager(db):
    assert_result(db, earn_more_than_manager(), ["name"], [("Cara",), ("Eli",)])


def test_department_headcounts(db):
    assert_result(db, department_headcounts(), ["department", "headcount"], [
        ("Engineering", 4), ("Sales", 3), ("HR", 2), ("Legal", 0)])


def test_customer_order_stats(db):
    assert_result(db, customer_order_stats(), ["name", "order_count", "total_spent"], [
        ("Acme", 3, 500.0), ("Globex", 2, 380.0), ("Initech", 2, 525.0), ("Umbrella", 1, 220.0)])


def test_customers_without_orders(db):
    assert_result(db, customers_without_orders(), ["name"], [("Hooli",), ("Stark",)])


def test_all_customer_totals(db):
    assert_result(db, all_customer_totals(), ["name", "total_spent"], [
        ("Initech", 525.0), ("Acme", 500.0), ("Globex", 380.0), ("Umbrella", 220.0),
        ("Hooli", 0), ("Stark", 0)], ordered=True)


def test_assignment_report(db):
    assert_result(db, assignment_report(), ["employee", "project", "hours"], [
        ("Cara", "Atlas", 150), ("Ben", "Atlas", 100), ("Eli", "Compass", 90),
        ("Cara", "Beacon", 80), ("Dan", "Compass", 60), ("Jo", "Beacon", 40),
        ("Ian", "Delta", 30), ("Ava", "Atlas", 10)], ordered=True)


def test_colleague_pairs(db):
    assert_result(db, colleague_pairs(), ["emp1", "emp2"], [
        ("Ava", "Ben"), ("Ava", "Cara"), ("Ava", "Jo"), ("Ben", "Cara"), ("Ben", "Jo"),
        ("Cara", "Jo"), ("Dan", "Eli"), ("Dan", "Fay"), ("Eli", "Fay"), ("Gus", "Hana")])


def test_department_quarter_grid(db):
    exp = [(d, q) for d in ["Engineering", "Sales", "HR", "Legal"] for q in ["Q1", "Q2"]]
    assert_result(db, department_quarter_grid(), ["department", "quarter"], exp)


def test_above_company_average(db):
    assert_result(db, above_company_average(), ["name", "salary"], [
        ("Ava", 200000), ("Ben", 150000), ("Cara", 160000), ("Jo", 120000)])


def test_above_department_average(db):
    assert_result(db, above_department_average(), ["name", "salary"], [
        ("Ava", 200000), ("Cara", 160000), ("Dan", 90000), ("Eli", 95000), ("Gus", 65000)])


def test_top_paid_in_department(db):
    assert_result(db, top_paid_in_department(), ["name", "salary"], [
        ("Ava", 200000), ("Eli", 95000), ("Gus", 65000)])


def test_people_managers(db):
    assert_result(db, people_managers(), ["name"], [("Ava",), ("Ben",), ("Dan",), ("Gus",)])


def test_engineering_project_staff(db):
    assert_result(db, engineering_project_staff(), ["name"],
                  [("Ava",), ("Ben",), ("Cara",), ("Jo",)])


def test_latest_order_per_customer(db):
    assert_result(db, latest_order_per_customer(), ["name", "last_order"], [
        ("Acme", "2024-03-20"), ("Globex", "2024-03-15"),
        ("Initech", "2024-03-01"), ("Umbrella", "2024-03-09")])


def test_big_payroll_departments(db):
    assert_result(db, big_payroll_departments(), ["department", "total_salary"], [
        ("Engineering", 630000), ("Sales", 255000)])


def test_orders_above_average(db):
    assert_result(db, orders_above_average(), ["id", "total"], [
        (1, 250.0), (3, 300.0), (5, 400.0), (6, 220.0)])
