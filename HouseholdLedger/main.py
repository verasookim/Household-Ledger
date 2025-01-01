# main.py

from datetime import datetime
from database import init_db
from actions import add_transaction, view_transactions
from reports import weekly_report, monthly_report, annual_report

def main():
    while True:
        print("\nWelcome to the Household Ledger!")
        print("1. Add a Transaction")
        print("2. View Transactions (with optional filters)")
        print("3. Reports")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            category = input("Enter category (e.g., Food, Bills): ")
            amount = float(input("Enter amount: "))
            type_ = input("Enter type (Income/Expense): ")
            description = input("Enter description (optional): ")
            if not description.strip():
                description = None

            # Prompt for date
            date_input = input("Enter transaction date (YYYY-MM-DD) or leave blank for today: ")
            if not date_input.strip():
                date_input = None  # This will default to 'today' in add_transaction()

            add_transaction(category, amount, type_, description, date_input)

        elif choice == '2':
            print("\n-- Optional Filters --")
            category = input("Enter category to filter (leave blank for all): ")
            start_date = input("Enter start date (YYYY-MM-DD) or leave blank: ")
            end_date = input("Enter end date (YYYY-MM-DD) or leave blank: ")

            view_transactions(
                category=category if category.strip() else None,
                start_date=start_date if start_date.strip() else None,
                end_date=end_date if end_date.strip() else None
            )

        elif choice == '3':
            print("\nChoose a report type:")
            print("1. Weekly Report")
            print("2. Monthly Report")
            print("3. Annual Report")
            sub_choice = input("Enter your choice: ")

            if sub_choice == '1':
                weekly_report()
            elif sub_choice == '2':
                year_input = input("Enter a year (leave blank for current year): ")
                if year_input.strip():
                    monthly_report(year=int(year_input))
                else:
                    monthly_report()  # default to current year
            elif sub_choice == '3':
                year_input = input("Enter a year (leave blank for current year): ")
                if year_input.strip():
                    annual_report(year=int(year_input))
                else:
                    annual_report()  # default to current year
            else:
                print("Invalid report choice!")

        elif choice == '4':
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    init_db()  # Ensure the database is initialized
    main()
