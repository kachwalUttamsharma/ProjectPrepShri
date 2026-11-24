"""Week 1 SQL exercises. Replace each `...` with `return "<your SQL>"`.

Each function must RETURN a SQL string (a single SELECT statement).
The tests run your SQL against the sample DB from schema.py and compare the
result rows AND the column names/aliases. Read schema.py for the tables:

  employees(id, name, dept, salary, hire_date, city, bonus)   -- NULLs exist!
  orders(id, customer, amount, status, order_date)            -- amount can be NULL

Row order only matters where the task says "ordered by".
Tip: try your SQL in a REPL first:  db = make_db(); db.execute(sql).fetchall()
"""


def nyc_employees():
    """Employees who live in 'NYC'.
    Columns: name, salary
    """
    ...


def high_earners():
    """Employees with salary >= 90000, highest salary first; ties by name A-Z.
    Columns: name, salary          (ordered by salary DESC, name ASC)
    """
    ...


def top3_paid():
    """The 3 best-paid employees (ties broken by name A-Z). NULL salaries must not appear.
    Columns: name, salary          (ordered by salary DESC, name ASC)
    Hint: ORDER BY ... LIMIT. Where do NULLs sort in SQLite? Filter them out.
    """
    ...


def page_two():
    """Pagination: employees ordered by id, page size 4, return page 2 (ids 5-8).
    Columns: id, name              (ordered by id)
    Hint: LIMIT ... OFFSET ...
    """
    ...


def hired_2019_2020():
    """Employees hired between 2019-01-01 and 2020-12-31 inclusive (dates are ISO text).
    Columns: name, hire_date       (ordered by hire_date ASC)
    """
    ...


def names_ending_in_e():
    """Employees whose name ends with the letter 'e' (LIKE is case-insensitive for ASCII in SQLite).
    Columns: name
    """
    ...


def no_bonus_recorded():
    """Employees whose bonus is NULL (unknown). A bonus of 0 does NOT count.
    Columns: name
    """
    ...


def total_compensation():
    """Salary + bonus (treat a NULL bonus as 0) for employees that have a salary.
    Columns: name, total_comp      (ordered by total_comp DESC, name ASC)
    Hint: COALESCE
    """
    ...


def not_in_hr():
    """Employees who are NOT in the 'HR' department. Employees with NO department
    (NULL) are also not in HR, so they must be included.
    Columns: name
    Hint: `dept <> 'HR'` alone silently drops NULL rows (NULL <> 'HR' is NULL).
    """
    ...


def distinct_cities():
    """Each city where at least one employee lives, once; ignore NULL cities.
    Columns: city
    """
    ...


def null_aware_counts():
    """One row with: total rows, how many have a salary, how many have a bonus.
    Columns: total_rows, salary_count, bonus_count
    Hint: COUNT(*) counts rows, COUNT(col) skips NULLs.
    """
    ...


def avg_salary_by_dept():
    """Per department (ignore employees with NULL dept): headcount (all rows in the
    dept, even with NULL salary) and average salary rounded to 2 decimals
    (AVG ignores NULL salaries).
    Columns: dept, headcount, avg_salary
    """
    ...


def big_departments():
    """Departments with MORE than 2 employees (ignore NULL dept).
    Columns: dept, headcount
    Hint: HAVING, not WHERE, filters on aggregates.
    """
    ...


def revenue_by_status():
    """For every order status: number of orders and the SUM of amount (NULL amounts are skipped).
    Columns: status, order_count, total_amount
    """
    ...


def monthly_shipped_revenue():
    """Revenue of *shipped* orders per month, labelled 'YYYY-MM'.
    Columns: month, revenue        (ordered by month ASC)
    Hint: substr(order_date, 1, 7) or strftime('%Y-%m', order_date)
    """
    ...


def big_customers():
    """Customers whose total amount over NON-cancelled orders is >= 240.
    Columns: customer, total       (ordered by total DESC)
    """
    ...


def distinct_city_count():
    """How many different (non-NULL) cities do employees live in? One row.
    Columns: cities
    """
    ...


def small_or_unknown_orders():
    """Orders whose amount is NOT greater than 100, including orders with an unknown (NULL) amount.
    Columns: id
    """
    ...
