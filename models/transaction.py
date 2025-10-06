
# models/transaction.py

from datetime import datetime

from prompts.emotion_tag_prompt import select_emotion_tag
from prompts.symbolic_time_prompt import select_symbolic_time
from utils.uuid_generator import generate_uuid

from utils.mongo_client import select_rows, insert_row
from utils.uuid_generator import generate_uuid
from datetime import date

def log_transaction(user_id, transaction_type):

    print(f"\n🧾 Logging a {transaction_type} transaction")

    amount = float(input("Enter amount: ").strip())
    category = input("Enter category (e.g. rent, groceries, Lyft): ").strip()
    description = input("Enter description (optional): ").strip() or "No description"
    source = input("Enter source (e.g. employer, Lyft, Venmo): ").strip()
    due_date_input = input("Enter due date (optional, YYYY-MM-DD): ").strip()
    due_date = due_date_input if due_date_input else None
    emotional_weight = input("Enter emotional weight (low, medium, high): ").strip().lower()

    # 🧠 Suggest mode based on past transactions
    similar_entries = select_rows("transactions", {
    "user_id": user_id,
    "source": source,
    "category": category
    })
    flow_count = sum(1 for t in similar_entries if t.get("mode") == "flow")
    structured_count = sum(1 for t in similar_entries if t.get("mode") == "structured")

    if flow_count > structured_count:
        suggested_mode = "flow"
    elif structured_count > flow_count:
        suggested_mode = "structured"
    else:
        suggested_mode = None

    if suggested_mode:
        print(f"\n🧭 Based on past entries, this looks like a {suggested_mode} transaction.")
        override = input("Would you like to change it? (y/N): ").strip().lower()
        mode = input("Enter 'flow' or 'structured': ").strip().lower() if override == "y" else suggested_mode
    else:
        mode = input("No clear pattern found. Enter 'flow' or 'structured': ").strip().lower()

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": amount,
        "type": transaction_type,
        "category": category,
        "date": str(date.today()),
        "description": description,
        "tags": "",  # You can add emotional tags later
        "source": source,
        "due_date": due_date,
        "emotional_weight": emotional_weight,
        "reconciliation_id": None,
        "mode": mode
    }

    result = insert_row("transactions", transaction)
    return f"Transaction logged with ID {transaction['transaction_id']}"
