# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db
from actions import add_transaction, view_transactions, get_spending_by_category_distribution, get_daily_spending_trend, get_monthly_income_expenses, add_or_update_budget, get_all_budgets, get_spending_for_period, get_all_categories, delete_budget
from reports import weekly_report, monthly_report, annual_report



app = Flask(__name__)
app.secret_key = "ledger"  # Needed for flash messages

# Initialize the database when the app starts
init_db()

@app.route("/")
def home():
    """
    Render the homepage/dashboard with dynamic financial data.
    """
    # 1. Gather Chart Data
    category_distribution = get_spending_by_category_distribution()
    monthly_income_expenses = get_monthly_income_expenses()  # Optionally pass a year
    daily_trend = get_daily_spending_trend(30)  # Last 30 days

    data = {
        "categoryDistribution": category_distribution,
        "incomeExpenses": monthly_income_expenses,
        "dailyTrend": daily_trend
    }


    return render_template(
        "index.html",
        data=data
    )

@app.route("/add_transaction", methods=["GET", "POST"])
def add_transaction_route():
    if request.method == "POST":
        category = request.form.get('category')
        amount = float(request.form.get('amount'))
        transaction_type = request.form.get('type')
        description = request.form.get('description')
        date_str = request.form.get('date', '')  # e.g. '2024-10-05' or '' if blank

        # If the user left the date field blank, pass None so the function defaults to today
        if not date_str:
            date_str = None

        # Now call your add_transaction function
        add_transaction(
            category=category,
            amount=amount,
            type_=transaction_type,
            description=description,
            date_str=date_str
        )

        # Redirect somewhere—maybe back to a list of transactions
        return redirect(url_for('view_transactions_route'))


    # If GET request, just show the form
    return render_template("add_transaction.html")




@app.route("/view_transactions", methods=["GET"])
def view_transactions_route():
    # 1) Get distinct categories
    all_categories = get_all_categories()

    # 2) Decide whether to fetch transactions or not
    category = request.args.get("category", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if category or start_date or end_date:
        transactions = view_transactions(category, start_date, end_date)
    else:
        transactions = []

    return render_template(
        "view_transactions.html",
        transactions=transactions,
        all_categories=all_categories,
        selected_category=category
    )





@app.route("/reports")
def reports_route():
    """
    Page with links or forms to generate weekly, monthly, or annual reports.
    """
    return render_template("reports.html")

@app.route("/reports/weekly")
def weekly_route():
    year_str = request.args.get("year", None)
    if year_str and year_str.isdigit():
        data = weekly_report(year=int(year_str))  # grouping by calendar week
        year_int = int(year_str)
    else:
        data = weekly_report()  # or last 7 days approach
        year_int = None

    return render_template("report_weekly.html", data=data, year=year_int)


@app.route("/reports/monthly")
def monthly_route():
    year_str = request.args.get("year", None)
    if year_str and year_str.isdigit():
        data = monthly_report(year=int(year_str))
        year_int = int(year_str)
    else:
        data = monthly_report()
        year_int = None

    return render_template("report_monthly.html", data=data, year=year_int)


@app.route("/reports/annual")
def annual_route():
    year_str = request.args.get("year", None)
    if year_str and year_str.isdigit():
        data = annual_report(year=int(year_str))
        year_int = int(year_str)
    else:
        data = annual_report()
        year_int = None

    return render_template("report_annual.html", data=data, year=year_int)



# budget
@app.route('/budgets', methods=['GET', 'POST'])
def budgets_route():
    if request.method == 'POST':
        # Grab data from form
        category = request.form.get('category')
        timeframe = request.form.get('timeframe')
        amount = request.form.get('amount')

        # Validation
        if not category or not timeframe or not amount:
            flash("All fields (Category, Timeframe, Amount) are required!", "warning")
        else:
            try:
                amount_float = float(amount)
                add_or_update_budget(category, timeframe, amount_float)
                flash("Budget saved successfully!", "success")
            except ValueError:
                flash("Invalid amount. Please enter a number.", "danger")

        return redirect(url_for('budgets_route'))

    # For GET: show the list of budgets
    budgets = get_all_budgets()

    # Build a list of budget status info
    # We'll compute how much spent so far in the timeframe and pass it to the template
    budget_status_list = []
    for b in budgets:
        spent = get_spending_for_period(b.category, b.timeframe)
        remaining = b.amount - spent
        percentage = (spent / b.amount) * 100 if b.amount else 0
        budget_status_list.append({
            'id': b.id,
            'category': b.category,
            'timeframe': b.timeframe,
            'budget_amount': b.amount,
            'spent': spent,
            'remaining': remaining,
            'percentage': percentage
        })

    return render_template('budgets.html', budget_status_list=budget_status_list)


@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget_route(budget_id):
    success = delete_budget(budget_id)
    if success:
        flash("Budget deleted successfully!", "success")
    else:
        flash("Budget not found. Deletion failed.", "danger")
    return redirect(url_for('budgets_route'))


@app.route("/delete_transaction/<int:transaction_id>", methods=["POST"])
def delete_transaction_route(transaction_id):
    from actions import delete_transaction  # or define it in this file
    delete_transaction(transaction_id)      # a function that removes one record
    flash(f"Transaction {transaction_id} deleted!", "success")
    return redirect(url_for('view_transactions_route'))


@app.route("/delete_transactions", methods=["POST"])
def bulk_delete_route():
    from actions import delete_multiple_transactions  # or define it
    selected_ids = request.form.getlist('selected_ids')  # checkboxes

    if selected_ids:
        int_ids = [int(x) for x in selected_ids]
        delete_multiple_transactions(int_ids)  # Bulk delete logic
        flash(f"Deleted {len(int_ids)} transactions!", "success")
    else:
        flash("No transactions selected to delete.", "warning")

    return redirect(url_for('view_transactions_route'))




if __name__ == "__main__":
    init_db()
    app.run(debug=True)


