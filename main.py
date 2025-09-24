from dotenv import load_dotenv
load_dotenv()

from models.user import add_user, user_exists, get_user
from rituals.reconciliation import perform_reckoning
from models.transaction import log_transaction
from inspiration.quotes import fetch_quote
from rituals.core.setup import run_setup_module  # new module for setup rituals
# from rituals.batch_log import batch_log  # future module
# from review.summary import generate_emotional_summary  # future emotional review

# 💡 You can exit the program anytime with Ctrl + C


def startup_ritual():
    print("\n🕯️ Opening Ritual")
    print(fetch_quote())
    print("-" * 50)


def prompt_for_user():
    print("\n🧬 User Initialization")
    user_id = input("Enter your unique user ID: ").strip()

    if user_exists(user_id):
        user_data = get_user(user_id)
        name = user_data.get("name")
        email = user_data.get("email")
        note = user_data.get("note")
        print(f"🔁 Welcome back, {name or user_id}. Your identity is already known.")
    else:
        name = input("Enter your name (optional): ").strip() or None
        email = input("Enter your email (optional): ").strip() or None
        note = input("Enter a symbolic note (optional): ").strip() or "Initiated during sacred startup ritual"
        add_user(user_id, name=name, email=email, note=note)
        print(f"👤 Welcome, {name or user_id}. Your presence is now etched into the ledger.")

    return user_id


print("\n🧭 You are in Hybrid Mode — structure and flow are both honored.")



def run_hybrid_mode(user_id):
    while True:
        print("\n🌀 Hybrid Mode Menu:")
        print("1. Log Income")
        print("2. Log Expense")
        print("3. Log Symbolic Payment")
        print("4. Setup Rituals 🛠️")
        print("5. Perform Reckoning 🔮")
        print("6. Exit Valhalla")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            message = log_transaction(user_id, "Income")
            print(f"✅ {message} — Rhythm honored.")
        elif choice == "2":
            message = log_transaction(user_id, "Expense")
            print(f"💸 {message} — Weight released.")
        elif choice == "3":
            message = log_transaction(user_id, "Symbolic")
            print(f"🌠 {message} — Symbolic transaction logged.")
        elif choice == "4":
            run_setup_module(user_id)
        elif choice == "5":
            perform_reckoning(user_id)
        elif choice == "6":
            print("🌌 Exiting Valhalla. May your legacy echo.")
            break
        else:
            print("⚠️ Invalid choice. Try again.")


def main():
    print("\n🌀 Welcome to ValhallaBank — Emotional Budget Tracker")
    startup_ritual()
    user_id = prompt_for_user()
    print("\n🧭 You are in Hybrid Mode — structure and flow are both honored.")
    run_hybrid_mode(user_id)

if __name__ == "__main__":
    main()
