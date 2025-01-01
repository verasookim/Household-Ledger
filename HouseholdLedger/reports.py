# reports.py
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from database import Session, Transaction

session = Session()

def weekly_report(year=None):
    """
    Show transactions grouped by calendar week, category, and type for the given year.
    If no year is provided, default to the current year.
    """
    if year is None:
        year = datetime.now().year

    # Group by week number (extract('week', ...)), category, type
    weekly_data = (
        session.query(
            extract('week', Transaction.date).label("week_"),
            Transaction.category.label("category_"),
            Transaction.type.label("type_"),  # e.g., 'Income'/'Expense'
            func.sum(Transaction.amount).label("total_amount")
        )
        .filter(extract('year', Transaction.date) == year)
        .group_by(
            extract('week', Transaction.date),
            Transaction.category,
            Transaction.type
        )
        .order_by(
            extract('week', Transaction.date),
            Transaction.category
        )
        .all()
    )

    # Convert query results to a list of dicts
    results = []
    for row in weekly_data:
        results.append({
            "week": int(row.week_),
            "category": row.category_,
            "type": row.type_,
            "total_amount": row.total_amount
        })

    return results


def monthly_report(year=None):
    """
    Show transactions grouped by month, category, and type for the given year.
    If no year is provided, defaults to the current year.
    """
    if year is None:
        year = datetime.now().year

    monthly_data = (
        session.query(
            extract('month', Transaction.date).label("month_"),
            Transaction.category.label("category_"),
            Transaction.type.label("type_"),
            func.sum(Transaction.amount).label("total_amount")
        )
        .filter(extract('year', Transaction.date) == year)
        .group_by(
            extract('month', Transaction.date),
            Transaction.category,
            Transaction.type
        )
        .order_by(
            extract('month', Transaction.date),
            Transaction.category
        )
        .all()
    )

    results = []
    for row in monthly_data:
        results.append({
            "month": int(row.month_),
            "category": row.category_,
            "type": row.type_,
            "total_amount": row.total_amount
        })

    return results


def annual_report(year=None):
    """
    Show transactions grouped by category and type for the specified year.
    If no year is provided, defaults to the current year.
    """
    if year is None:
        year = datetime.now().year

    annual_data = (
        session.query(
            Transaction.category.label("category_"),
            Transaction.type.label("type_"),
            func.sum(Transaction.amount).label("total_amount")
        )
        .filter(extract('year', Transaction.date) == year)
        .group_by(Transaction.category, Transaction.type)
        .order_by(Transaction.category)
        .all()
    )

    results = []
    for row in annual_data:
        results.append({
            "category": row.category_,
            "type": row.type_,
            "total_amount": row.total_amount
        })

    return results
