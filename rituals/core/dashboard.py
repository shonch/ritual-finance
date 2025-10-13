from utils.mongo_client import select_rows
from datetime import datetime, timedelta
from rituals.core.setup_utils import format_currency, total_components


def view_dashboard(user_id):
    print("\n📊 Valhalla Dashboard Engine")
    print("Choose your projection window:")
    print("1. 1 Week")
    print("2. 2 Weeks")
    print("3. 1 Month")
    print("4. 3 Months")
    print("5. Custom Range")

    choice = input("Select an option: ").strip()
    today = datetime.today()

    if choice == "1":
        end_date = today + timedelta(days=7)
    elif choice == "2":
        end_date = today + timedelta(days=14)
    elif choice == "3":
        end_date = today + timedelta(days=30)
    elif choice == "4":
        end_date = today + timedelta(days=90)
    elif choice == "5":
        start_input = input("Start Date (YYYY-MM-DD): ").strip()
        end_input = input("End Date (YYYY-MM-DD): ").strip()
        try:
            today = datetime.strptime(start_input, "%Y-%m-%d")
            end_date = datetime.strptime(end_input, "%Y-%m-%d")
        except ValueError:
            print("⚠️ Invalid date format. Defaulting to 1 month.")
            end_date = today + timedelta(days=30)
    else:
        print("⚠️ Invalid choice. Defaulting to 1 month.")
        end_date = today + timedelta(days=30)

    print(f"\n🪞 Projection Window: {today.date()} to {end_date.date()}")

    # Fetch active setup items
    items = select_rows("setup_items", {"user_id": user_id, "active": True})
    recurring_total = 0.0

    print("\n🔁 Recurring Commitments:")
    for item in items:
        start = item.get("start_date", "N/A")
        end = item.get("end_date", None)
        due = item.get("due_date", "N/A")
        recurrence = item.get("recurrence", "none")

        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d") if start != "N/A" else today
            end_dt = datetime.strptime(end, "%Y-%m-%d") if end else end_date
            due_dt = datetime.strptime(due, "%Y-%m-%d") if due != "N/A" else None
        except ValueError:
            continue

    # Include if due_date is within window OR recurrence is active
        if (due_dt and today <= due_dt <= end_date) or (
            recurrence != "none" and start_dt <= end_date and end_dt >= today
        ):
            # Calculate total
            component_total = total_components(item.get("components", []))

            # 🛡️ Override interest if arc is enabled (payment already includes it)
            if item.get("category") == "Debt" and item.get("arc_enabled", False):
                total = item.get("amount", 0) + component_total
            else:
                monthly_interest = item.get("principal", 0) * item.get("interest_rate", 0) / 12
                total = item.get("amount", 0) + monthly_interest + component_total


            recurring_total += total

            print(
                f"• {item['name']}: {format_currency(total)} ({item['archetype']}, {item['symbolic_tag']})"
            )
    print(f"\n💸 Total Recurring Outflow: {format_currency(recurring_total)}")

    # Placeholder for buffer and fluid expenses
    print("🧪 Fluid Expenses and Buffer logic coming next...")
