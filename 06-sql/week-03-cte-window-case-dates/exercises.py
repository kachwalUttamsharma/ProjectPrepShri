"""Week 3 SQL exercises: CTEs, window functions, CASE, dates. Replace `...` with `return "<SQL>"`.

Tables (see schema.py):
  employees(id, name, dept, salary, manager_id, hire_date)
  sales(id, sale_date, region, amount)
  tickets(id, opened_at, closed_at, priority)   -- 'YYYY-MM-DD HH:MM:SS', closed_at NULL = open

Tests compare rows and column names. Order matters only when "ordered by" is stated.
SQLite date tools: date(x, '+1 day'), strftime('%Y-%m', x), julianday(x).
"""


def above_average_payroll_depts():
    """Departments whose total salary is above the average of all departments' totals.
    Use a CTE that computes payroll per dept first.
    Columns: dept, payroll
    """
    ...


def subordinates_of_ben():
    """Everyone who reports to Ben (id 2), directly or indirectly (recursive CTE).
    level = 1 for direct reports, 2 for their reports, ...
    Columns: name, level            (ordered by level ASC, name ASC)
    """
    ...


def date_series():
    """Generate every date from 2024-01-01 to 2024-01-07 inclusive with a recursive CTE.
    Columns: day                    (ordered by day ASC)
    """
    ...


def chain_to_ceo():
    """Walk UP the hierarchy from Eli (id 5) to the top. depth 0 = Eli, 1 = his manager, ...
    Columns: name, depth            (ordered by depth ASC)
    """
    ...


def dept_salary_rownumber():
    """Number employees inside each department by salary DESC (ties broken by name ASC)
    using ROW_NUMBER().
    Columns: name, dept, rn         (ordered by dept ASC, rn ASC)
    """
    ...


def company_rank_dense():
    """Rank every employee by salary DESC across the whole company with BOTH RANK() and DENSE_RANK().
    Columns: name, salary, rnk, drnk    (ordered by salary DESC, name ASC)
    """
    ...


def top_two_salaries_per_dept():
    """Employees whose salary is among the top 2 DISTINCT salary values of their department
    (so ties are all included). Use DENSE_RANK in a subquery/CTE.
    Columns: name, dept, salary
    """
    ...


def running_sales_total():
    """Running total of amount over all sales ordered by sale_date (tie-break id).
    Columns: id, sale_date, amount, running_total     (ordered by sale_date ASC, id ASC)
    """
    ...


def running_total_by_region():
    """Running total of amount restarting for each region (PARTITION BY), ordered by sale_date.
    Columns: id, region, amount, region_running       (ordered by region ASC, sale_date ASC)
    """
    ...


def month_over_month():
    """Monthly revenue with the previous month's revenue and the change (LAG).
    First month has NULL prev_revenue and NULL change.
    Columns: month, revenue, prev_revenue, change     (ordered by month ASC; month like '2024-01')
    """
    ...


def days_to_next_sale():
    """For each sale: number of days until the NEXT sale in the same region (LEAD); NULL for the last.
    Hint: julianday(next_date) - julianday(sale_date). Result should be integers/whole numbers.
    Columns: id, region, days_to_next
    """
    ...


def moving_average_3():
    """3-sale moving average of amount (current + 2 preceding sales) ordered by sale_date, id.
    Round to 2 decimals. Hint: ROWS BETWEEN 2 PRECEDING AND CURRENT ROW.
    Columns: id, avg3               (ordered by sale_date ASC, id ASC)
    """
    ...


def pct_of_region():
    """Each sale's share of its region's total, as a percentage rounded to 1 decimal.
    Columns: id, region, amount, pct
    Hint: amount * 100.0 / SUM(amount) OVER (PARTITION BY region)
    """
    ...


def salary_band():
    """CASE: salary >= 150000 -> 'High'; >= 90000 -> 'Mid'; otherwise 'Low'.
    Columns: name, band
    """
    ...


def pivot_monthly_by_region():
    """Pivot with conditional aggregation: one row per month, one column per region.
    Columns: month, east, west      (ordered by month ASC)
    """
    ...


def high_earner_counts():
    """Per department: employees with salary >= 100000 and the department's total headcount.
    Use SUM(CASE ...) (conditional aggregation).
    Columns: dept, high_paid, total
    """
    ...


def first_hire_in_dept():
    """For each employee, the name of the earliest-hired person in the same department
    (FIRST_VALUE over PARTITION BY dept ORDER BY hire_date).
    Columns: name, dept, first_hire
    """
    ...


def diff_from_dept_avg():
    """Salary minus the average salary of the employee's department (window AVG), rounded to 2 decimals.
    Columns: name, dept, diff
    """
    ...


def ticket_resolution_hours():
    """Hours between opened_at and closed_at for CLOSED tickets, rounded to 1 decimal.
    Columns: id, hours              (ordered by id ASC)
    """
    ...


def tickets_per_month():
    """For each month (by opened_at, 'YYYY-MM'): tickets opened and how many are still open (closed_at NULL).
    Columns: month, opened, still_open    (ordered by month ASC)
    """
    ...


def stale_open_tickets():
    """Tickets still open that were opened MORE than 7 days before '2024-04-20' (compare dates, ignore time).
    days_open = whole days between date(opened_at) and '2024-04-20'.
    Columns: id, days_open
    """
    ...
