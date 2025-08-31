# main.py

from models.transaction import log_transaction
# from rituals.batch_log import batch_log  # placeholder for future modules

USER_ID = "shon-001"

def choose_mode():
    print("\n🧭 Choose your budgeting mode:")
    print("1. Flow Mode (freelance, daily rhythm)")
    print("2. Monthly Mode (structured, salary-based)")
    mode = input("Enter 1 or 2: ")
    return "flow" if mode == "1" else "monthly"

def run_flow_mode():
    while True:
        print("\n🌊 Flow Mode Menu:")
        print("1. Log Income")
        print("2. Log Expense")
        print("3. Exit Flow Mode")
        choice = input("Choose an option: ")

        if choice == "1":
            log_transaction(USER_ID, "Income")
        elif choice == "2":
            log_transaction(USER_ID, "Expense")
        elif choice == "3":
            print("🌌 Exiting Flow Mode.")
            break
        else:
            print("⚠️ Invalid choice.")

def run_monthly_mode():
    while True:
        print("\n🧱 Monthly Mode Menu:")
        print("1. Log Income")
        print("2. Log Expense")
        print("3. Monthly Setup (placeholder)")
        print("4. Exit Monthly Mode")
        choice = input("Choose an option: ")

        if choice == "1":
            log_transaction(USER_ID, "Income")
        elif choice == "2":
            log_transaction(USER_ID, "Expense")
        elif choice == "3":
            print("📅 Monthly setup not yet implemented.")
        elif choice == "4":
            print("🌌 Exiting Monthly Mode.")
            break
        else:
            print("⚠️ Invalid choice.")

def main():
    mode = choose_mode()
    if mode == "flow":
        run_flow_mode()
    else:
        run_monthly_mode()

if __name__ == "__main__":
    main()
