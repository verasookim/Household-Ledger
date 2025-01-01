# actions.py

from database import Session, Transaction, Budget
from sqlalchemy.sql import cast
from sqlalchemy import Column, Date
import datetime
import csv
from sqlalchemy import func, extract
import calendar

session = Session()

def view_transactions(category=None, start_date=None, end_date=None):
    """
    View all transactions or filter them by category, start_date, and end_date.
    If no filters are provided, all transactions are returned.
    """
    query = session.query(Transaction)

    # Handle category filter
    if category:
        query = query.filter(Transaction.category == category)

    # Handle date range filters
    # User can input only start date or end date
    if start_date:
        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date >= start_date_obj)

    if end_date:
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(Transaction.date <= end_date_obj)

    query = query.order_by(Transaction.date.desc()) # newest first

    transactions = query.all()

    if not transactions:
        print("No transactions found!")
        return

    for t in transactions:
        print(f"Date: {t.date}, Category: {t.category}, "
              f"Amount: {t.amount}, Type: {t.type}, "
              f"Description: {t.description}")
        
    return transactions

def add_transaction(category, amount, type_, description=None, date_str=None):
    """
    Add a new transaction to the database.
    :param category: Transaction category
    :param amount: Transaction amount
    :param type_: 'Income' or 'Expense'
    :param description: Optional string for transaction details
    :param date_str: Optional string (e.g., 'YYYY-MM-DD'). If None, use today's date.
    """
    if date_str:
        # Convert the string to a date object
        transaction_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        # If no date provided, use today's date
        transaction_date = datetime.now().date()

    transaction = Transaction(
        category=category,
        amount=amount,
        type=type_,
        description=description,
        date=transaction_date
    )
    session.add(transaction)
    session.commit()
    print("Transaction added!")


def export_transactions_to_csv(filename="transactions.csv"):
    transactions = session.query(Transaction).all()
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Category", "Amount", "Type", "Description"])
        for t in transactions:
            writer.writerow([t.date, t.category, t.amount, t.type, t.description])
    print(f"Transactions exported to {filename} successfully!")


def get_spending_by_category():
    """
    Returns a dict: {CategoryName: SumOfAmounts, ...} 
    For example: {'Food': 120.0, 'Bills': 200.0}
    """
    session = Session()

    # Example: Summing *all* transaction amounts by category:
    rows = (
        session.query(
            Transaction.category,
            func.sum(Transaction.amount)
        )
        .group_by(Transaction.category)
        .all()
    )

    # Convert list of tuples -> dict
    # [('Food', 120.0), ('Bills', 200.0)] => {'Food': 120.0, 'Bills': 200.0}
    return {row[0]: float(row[1]) for row in rows}



def add_or_update_budget(category, timeframe, amount):
    """
    Create or update a budget record for the given category and timeframe.
    """
    # Check if a budget already exists for this category and timeframe
    existing = session.query(Budget).filter_by(category=category, timeframe=timeframe).first()
    if existing:
        existing.amount = amount
        print(f"Updated budget for {category}-{timeframe} to {amount}")
    else:
        new_budget = Budget(category=category, timeframe=timeframe, amount=amount)
        session.add(new_budget)
        print(f"Created new budget for {category}-{timeframe} with amount {amount}")
    session.commit()

def get_all_budgets():
    """
    Return a list of all budgets in the DB.
    """
    return session.query(Budget).all()

def get_spending_for_period(category, timeframe):
    """
    Return the total 'Expense' spending for the given category within the current timeframe (weekly or monthly).
    For simplicity, we define:
        - 'weekly': from Monday of the current week to Sunday of the current week
        - 'monthly': from the 1st of the current month to the end of the current month
    """
    today = datetime.datetime.today()
    if timeframe == 'weekly':
        # Monday = weekday 0, Sunday = weekday 6
        start_of_week = today
        while start_of_week.weekday() != 0:  # 0 = Monday
            start_of_week = start_of_week.replace(day=start_of_week.day - 1)
        end_of_week = start_of_week.replace(day=start_of_week.day + 6)
        start_date, end_date = start_of_week, end_of_week

    elif timeframe == 'monthly':
        # First day of current month
        start_of_month = today.replace(day=1)
        # Last day of current month
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = today.replace(day=last_day)
        start_date, end_date = start_of_month, end_of_month

    else:
        # Fallback: no timeframe recognized, return 0
        return 0

    # Query total spending for the specified category, within date range, for 'Expense' only
    total = (session.query(func.sum(Transaction.amount))
                   .filter(Transaction.category == category)
                   .filter(Transaction.type == 'Expense')
                   .filter(Transaction.date >= start_date)
                   .filter(Transaction.date <= end_date)
                   .scalar())
    return total if total else 0  # convert None -> 0

def delete_budget(budget_id):
    """
    Delete a budget record by its ID.
    """
    budget = session.query(Budget).filter_by(id=budget_id).first()
    if budget:
        session.delete(budget)
        session.commit()
        print(f"Deleted budget with ID {budget_id}")
        return True
    else:
        print(f"No budget found with ID {budget_id}")
        return False

def get_spending_by_category_distribution():
    """
    Returns a dictionary of total expense amounts per category.
    Example output: {'Food': 120.0, 'Bills': 200.0, 'Entertainment': 80.0}
    """
    session = Session()
    rows = (
        session.query(Transaction.category, func.sum(Transaction.amount))
        .filter(Transaction.type == 'Expense')
        .group_by(Transaction.category)
        .all()
    )
    # rows might look like: [('Food', 120.0), ('Bills', 200.0), ...]

    # Convert to a dict
    category_distribution = {row[0]: float(row[1]) for row in rows}
    return category_distribution

def get_monthly_income_expenses(year=None):
    """
    Returns a dictionary with structure:
    {
      "months": ["Jan","Feb","Mar","Apr"],
      "income": [3000,3100,2800,5000],
      "expense": [2000,2500,1800,4000]
    }
    By default, if `year` is None, use the current year.
    """
    session = Session()
    if not year:
        year = datetime.datetime.today().year

    # We'll gather each month (1-12) for the given year
    months_list = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_income = [0]*12
    monthly_expense = [0]*12

    # Query incomes grouped by month
    income_rows = (
        session.query(
            extract('month', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total_income')
        )
        .filter(Transaction.type == 'Income')
        .filter(func.extract('year', Transaction.date) == year)
        .group_by(extract('month', Transaction.date))
        .all()
    )
    # income_rows could look like: [(1, 3000.0), (2, 3100.0), ...]

    for row in income_rows:
        month_index = int(row[0]) - 1  # e.g. if row[0] = 1 => January => index 0
        monthly_income[month_index] = float(row[1])

    # Query expenses grouped by month
    expense_rows = (
        session.query(
            extract('month', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total_expense')
        )
        .filter(Transaction.type == 'Expense')
        .filter(func.extract('year', Transaction.date) == year)
        .group_by(extract('month', Transaction.date))
        .all()
    )

    for row in expense_rows:
        month_index = int(row[0]) - 1
        monthly_expense[month_index] = float(row[1])

    # We'll only return months up to 12, but you could also limit to current month
    data = {
        "months": months_list,        # all 12 month labels
        "income": monthly_income,     # list of 12 values
        "expense": monthly_expense    # list of 12 values
    }
    return data

def get_daily_spending_trend(days_back=30):
    """
    Returns a dictionary:
    {
      "dates": ["2023-10-01", "2023-10-02", ...],
      "values": [50, 80, 120, ...]
    }
    Summing up total expenses for each date.
    By default, last 30 days.
    """
    session = Session()

    # Calculate the start date
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=days_back)

    # Query daily expenses
    rows = (
        session.query(
            Transaction.date,
            func.sum(Transaction.amount)
        )
        .filter(Transaction.type == 'Expense')
        .filter(Transaction.date >= start_date)
        .group_by(Transaction.date)
        .order_by(Transaction.date.asc())
        .all()
    )
    # Example rows: [(datetime.date(2023,10,1), 50.0), (datetime.date(2023,10,2), 80.0), ...]

    dates = []
    values = []
    # We can fill in the gap for days that have no transactions if desired.
    # For simplicity, we'll just convert the rows we do have.
    for row in rows:
        date_obj = row[0]
        total_amount = float(row[1])
        dates.append(date_obj.isoformat())  # e.g. "2023-10-01"
        values.append(total_amount)

    data = {
        "dates": dates,
        "values": values
    }
    return data


def delete_transaction(transaction_id):
    txn = session.query(Transaction).get(transaction_id)
    if txn:
        session.delete(txn)
        session.commit()
        print(f"Deleted transaction {transaction_id}.")
    else:
        print(f"No transaction found with ID {transaction_id}.")

def delete_multiple_transactions(ids_list):
    if not ids_list:
        return
    session.query(Transaction).filter(Transaction.id.in_(ids_list)).delete(synchronize_session=False)
    session.commit()



def get_all_categories():
    rows = session.query(Transaction.category).distinct().all()
    # rows might look like: [('Food',), ('Bills',), ('Clothes',)]
    return [r[0] for r in rows]