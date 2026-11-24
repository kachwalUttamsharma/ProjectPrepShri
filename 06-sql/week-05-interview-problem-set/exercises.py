"""Week 5: classic SQL interview problems. Replace each `...` with `return "<your SQL>"`.

Tables are described at the top of schema.py. Tests compare rows AND column names.
Row order matters only where the docstring says "ordered by".
Many of these are famous (LeetCode / interview-bank) problems: solve them without
looking things up first, then compare with the patterns in lesson.md.
Time yourself: an interview slot is ~15-20 minutes per problem.
"""


# ---------------------------------------------------------------- Easy / warm-up
def second_highest_salary():
    """Second highest DISTINCT salary in employees (ties count once).
    Columns: second_highest
    """
    ...


def duplicate_emails():
    """Emails that appear more than once in people, with how many times.
    Columns: email, cnt
    """
    ...


def duplicate_ids_to_delete():
    """People rows you would DELETE to keep only the lowest id per email.
    (Return a SELECT of the ids to delete; do not delete anything.)
    Columns: id
    """
    ...


def earn_more_than_manager():
    """Employees who earn more than their manager.
    Columns: name
    """
    ...


def managers_with_three_reports():
    """Managers with at least 3 direct reports.
    Columns: name
    """
    ...


def customers_bought_every_category():
    """Customers who bought from EVERY category that appears in purchases (relational division).
    Columns: customer
    """
    ...


# ------------------------------------------------------- Top-N / ranking / medians
def department_top_earners():
    """In every department, the employee(s) with the highest salary (ties all returned).
    Columns: dept, employee, salary          (dept = department name)
    """
    ...


def top2_products_per_category():
    """For each category, the 2 products with the highest total revenue (sum of amount).
    Columns: category, product, revenue      (ordered by category ASC, revenue DESC)
    """
    ...


def median_salary_per_dept():
    """Median salary per department (average of the two middle values when the count is even).
    SQLite has no MEDIAN: use ROW_NUMBER and COUNT window functions.
    Columns: dept, median                    (dept = department name)
    """
    ...


def first_order_per_customer():
    """Each customer's first order (earliest order_date).
    Columns: customer, order_date, amount
    """
    ...


def best_customer_each_month():
    """For each month ('YYYY-MM') the customer with the highest total amount that month.
    Columns: month, customer, total          (ordered by month ASC)
    """
    ...


# ------------------------------------------------ Gaps and islands / consecutive
def consecutive_login_users():
    """Users who logged in on at least 3 consecutive calendar days (duplicate rows for the same
    day must not count twice).
    Columns: user_id
    """
    ...


def longest_login_streak():
    """Longest run of consecutive login days per user (distinct days).
    Columns: user_id, longest_streak
    """
    ...


def id_islands():
    """Collapse log_ids into islands of consecutive integers.
    Columns: start_id, end_id                (ordered by start_id ASC)
    """
    ...


def missing_id_ranges():
    """The gaps: ranges of integers missing between the smallest and largest log_ids.
    Columns: gap_start, gap_end              (ordered by gap_start ASC)
    """
    ...


def sessions_per_user():
    """Sessionization: a new session starts when the gap since the user's previous event is
    MORE than 30 minutes (exactly 30 minutes stays in the same session).
    Hint: strftime('%s', ts) gives integer seconds; LAG + SUM/COUNT of 'new session' flags.
    Columns: user_id, sessions
    """
    ...


# ------------------------------------------------- Time series / growth / running
def running_balance():
    """Running balance per account ordered by pay_date.
    Columns: id, account, amount, balance    (ordered by account ASC, pay_date ASC)
    """
    ...


def rolling_7day_average():
    """7-day rolling average of revenue (current day + 6 previous days), rounded to 2 decimals,
    only for days that have a FULL 7-day window.
    Columns: day, avg7                       (ordered by day ASC)
    """
    ...


def month_over_month_growth():
    """Monthly revenue from product_sales (month 'YYYY-MM') with growth % versus the previous
    month, rounded to 1 decimal; NULL for the first month.
    Columns: month, revenue, growth_pct      (ordered by month ASC)
    """
    ...


def avg_days_between_orders():
    """For customers with at least 2 orders: average number of days between consecutive orders,
    rounded to 2 decimals.
    Columns: customer, avg_gap_days
    """
    ...


# ---------------------------------------------------------- Product analytics
def day1_retention():
    """Day-1 retention per signup cohort: users who were active EXACTLY one day after signing up.
    retention_pct = retained / users * 100, rounded to 1 decimal.
    Columns: cohort, users, retained, retention_pct   (ordered by cohort ASC)
    """
    ...


def purchase_funnel():
    """Funnel: distinct users reaching each step, and that as a % of users at 'view' (1 decimal).
    Columns: step, users, pct_of_first        (ordered view, cart, purchase)
    """
    ...


# --------------------------------------------------- Reshaping / reporting / misc
def pivot_quarterly_sales():
    """Pivot: one row per category, one column per quarter of 2024 (q1 = Jan-Mar, q2 = Apr-Jun,
    q3 = Jul-Sep) with the summed amount.
    Columns: category, q1, q2, q3
    """
    ...


def revenue_share_pct():
    """Each product's share of total revenue as a percentage, rounded to 1 decimal.
    Columns: product, revenue, pct
    Hint: SUM(SUM(amount)) OVER () or a scalar subquery.
    """
    ...


def swap_adjacent_seats():
    """Swap the students of seats (1,2), (3,4), ...; if the number of seats is odd the last
    seat keeps its student. (Famous 'exchange seats' problem.)
    Columns: id, student                      (ordered by id ASC)
    """
    ...


def salary_histogram():
    """Count employees per salary band: '<60k' (< 60000), '60-80k' (60000-79999),
    '80-100k' (80000-99999), '100k+' (>= 100000).
    Columns: band, n
    """
    ...
