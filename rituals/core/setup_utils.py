# 🧰 core/setup_utils.py — Shared Ritual Tools

from datetime import datetime, timedelta

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
