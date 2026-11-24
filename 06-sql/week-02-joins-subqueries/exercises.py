"""Week 2 SQL exercises: joins and subqueries. Replace each `...` with `return "<your SQL>"`.

Tables (see schema.py):
  departments(id, name, location)
  employees(id, name, dept_id, manager_id, salary)   -- Ian has NULL dept, Ava has NULL manager
  projects(id, name, dept_id)
  assignments(emp_id, project_id, hours)
  customers(id, name, country)
  orders(id, customer_id, order_date, total)

The tests compare rows AND column names/aliases. Order matters only where stated.
"""


def inner_join_employee_dept():
    """Each employee together with their department name (employees without a department are dropped).
    Columns: employee, department
    """
    ...


def all_employees_with_dept():
    """Every employee with their department name; department is NULL if they have none.
    Columns: employee, department
    """
    ...


def empty_departments():
    """Departments that have no employees (anti-join).
    Columns: name
    """
    ...


def unassigned_employees():
    """Employees who are not assigned to any project. Use NOT EXISTS (or LEFT JOIN ... IS NULL).
    Columns: name
    """
    ...


def employee_manager_pairs():
    """Each employee with the name of their manager (self-join). The CEO has no manager: leave her out.
    Columns: employee, manager
    """
    ...


def earn_more_than_manager():
    """Employees who earn strictly more than their direct manager.
    Columns: name
    """
    ...


def department_headcounts():
    """Headcount of every department, including departments with 0 employees.
    Columns: department, headcount
    Hint: LEFT JOIN, then COUNT(e.id) (not COUNT(*), which would count the NULL-extended row as 1).
    """
    ...


def customer_order_stats():
    """For customers that have placed orders: number of orders and total spent.
    Columns: name, order_count, total_spent
    """
    ...


def customers_without_orders():
    """Customers that never ordered.
    Columns: name
    """
    ...


def all_customer_totals():
    """Every customer with total spent; 0 if they never ordered.
    Columns: name, total_spent     (ordered by total_spent DESC, name ASC)
    """
    ...


def assignment_report():
    """Three-table join: employee name, project name and hours for every assignment.
    Columns: employee, project, hours     (ordered by hours DESC)
    """
    ...


def colleague_pairs():
    """All unordered pairs of different employees in the same department, each pair once
    (self-join with e1.id < e2.id). Employees without a department never pair up.
    Columns: emp1, emp2
    """
    ...


def department_quarter_grid():
    """A reporting skeleton: every department paired with each of the quarters 'Q1' and 'Q2'
    (CROSS JOIN). Build the quarters inline with SELECT ... UNION ALL SELECT ... 
    Columns: department, quarter
    """
    ...


def above_company_average():
    """Employees paid more than the company-wide average salary (scalar subquery).
    Columns: name, salary
    """
    ...


def above_department_average():
    """Employees paid more than the average salary of THEIR department (correlated subquery).
    Employees without a department are not compared with anyone, so they are excluded.
    Columns: name, salary
    """
    ...


def top_paid_in_department():
    """The best-paid employee of each department (correlated subquery on MAX; no ties in this data).
    Employees without a department are excluded.
    Columns: name, salary
    """
    ...


def people_managers():
    """Employees who manage at least one other employee (use EXISTS).
    Columns: name
    """
    ...


def engineering_project_staff():
    """Distinct employees assigned to at least one project owned by the 'Engineering' department
    (use IN with a subquery, or EXISTS).
    Columns: name
    """
    ...


def latest_order_per_customer():
    """For every customer that has orders: the date of their most recent order.
    Columns: name, last_order
    """
    ...


def big_payroll_departments():
    """Departments whose total salary exceeds 200000, with that total.
    Columns: department, total_salary
    """
    ...


def orders_above_average():
    """Orders whose total is above the average order total.
    Columns: id, total
    """
    ...
