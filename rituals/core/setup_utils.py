# 🧰 core/setup_utils.py — Shared Ritual Tools

from datetime import datetime, timedelta
from emotional_budget_tracker.utils.mongo_client import update_row
def format_currency(amount):
    """Formats a float as currency string."""
    return f"${amount:,.2f}"

def total_components(components):
    """Returns the total amount from all components."""
    return sum(comp.get("amount", 0) for comp in components)




def generate_due_dates(start_date, frequency, count=6):
    """Generates a list of future due dates based on frequency."""
    delta_map = {
        "weekly": timedelta(weeks=1),
        "biweekly": timedelta(weeks=2),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annually": timedelta(days=365)
    }
    delta = delta_map.get(frequency.lower(), timedelta(days=30))
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [(start + i * delta).strftime("%Y-%m-%d") for i in range(count)]

def prompt_principal_and_interest(category):
    """Prompts for principal and interest only if category is 'debt'."""
    if category.lower() == "debt":
        principal_input = input("Principal Amount: ").strip()
        principal = float(principal_input) if principal_input else 0.0
        if not principal_input:
            print("⚠️ No principal entered. Defaulting to $0.00 — symbolic or one-time payment.")

        interest_input = input("Interest Rate (%): ").strip()
        interest_rate = float(interest_input) / 100 if interest_input else 0.0
        if not interest_input:
            print("⚠️ No interest rate entered. Defaulting to 0% — symbolic or one-time payment.")
    else:
        principal = 0.0
        interest_rate = 0.0
        print("🕊️ No principal or interest required. This is a symbolic or legacy fragment.")
    return principal, interest_rate

def validate_frequency(frequency):
    """Validates and normalizes frequency input."""
    valid = ["weekly", "biweekly", "monthly", "quarterly", "annually"]
    return frequency.lower() if frequency.lower() in valid else "monthly"

def get_emotion_tag():
    """Prompts user to select or enter an emotion tag."""
    tags = [
        "🌀 Momentum",
        "🌉 Threshold Tension",
        "🪡 Thread of Trust",
        "🧮 Algorithmic Grip",
        "🌌 Wandering Debt"
    ]
    print("\n🧠 Choose an Emotion Tag:")
    for i, tag in enumerate(tags, 1):
        print(f"{i}. {tag}")
    choice = input("Enter number or type a new tag: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(tags):
        return tags[int(choice) - 1]
    return choice or "🌀 Momentum"



def advance_due_date_if_needed(item, today=None, update_db=False):
    if today is None:
        today = datetime.today()

    recurrence = item.get("recurrence", "none")
    due_str = item.get("due_date", "N/A")

    if recurrence == "none" or due_str == "N/A":
        return item

    try:
        due_date = datetime.strptime(due_str, "%Y-%m-%d")
    except ValueError:
        return item

    delta_map = {
        "weekly": timedelta(weeks=1),
        "biweekly": timedelta(weeks=2),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annually": timedelta(days=365)
    }
    delta = delta_map.get(recurrence.lower(), timedelta(days=30))

    original_due = due_date
    while due_date < today:
        due_date += delta

    if due_date != original_due:
        item["due_date"] = due_date.strftime("%Y-%m-%d")
        if update_db:
            update_row(
                "setup_items",
                {"setup_id": item["setup_id"], "user_id": item["user_id"]},
                {"due_date": item["due_date"]}
            )

    return item
