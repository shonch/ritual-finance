# models/transaction.py

from datetime import datetime, date
from emotional_budget_tracker.prompts.emotion_tag_prompt import select_emotion_tag
from emotional_budget_tracker.prompts.symbolic_time_prompt import select_symbolic_time
from emotional_budget_tracker.utils.uuid_generator import generate_uuid
from emotional_budget_tracker.utils.mongo_client import select_rows, insert_row

# Import Phoenix tag bridge
from backend.modules.symbolic_tag import normalize_tag, create_tag


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

    # Normalize tags (CLI version leaves empty, but we can extend later)
    final_tags = []

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": amount,
        "type": transaction_type,
        "category": category,
        "date": str(date.today()),
        "description": description,
        "tags": final_tags,
        "source": source,
        "due_date": due_date,
        "emotional_weight": emotional_weight,
        "reconciliation_id": None,
        "mode": mode
    }

    result = insert_row("transactions", transaction)
    return f"Transaction logged with ID {transaction['transaction_id']}"


# --- NEW FUNCTION — for API use ---
def log_transaction_from_api(user_id, transaction_data):
    # Normalize tags
    raw_tags = transaction_data.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    final_tags = [normalize_tag(tag) for tag in raw_tags]

    # Create tags in Phoenix
    for tag in final_tags:
        create_tag({"tag_name": tag, "description": "Auto-inserted from Valhalla transaction"})

    # Build Markdown overlay
    md_content = f"""### 💸 Transaction Logged

**Category**: {transaction_data.get("category")}  
**Amount**: {transaction_data.get("amount")}  
**Mode**: {transaction_data.get("mode", "structured")}  
**Tags**: {", ".join(final_tags) if final_tags else "none"}  
**Date**: {transaction_data.get("date")}  
**Source**: {transaction_data.get("source")}  
**Due Date**: {transaction_data.get("due_date") or "N/A"}  
**Emotional Weight**: {transaction_data.get("emotional_weight", "medium")}  

---

{transaction_data.get("description", "No description")}
"""

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": transaction_data.get("amount"),
        "type": transaction_data.get("type"),
        "category": transaction_data.get("category"),
        "date": transaction_data.get("date"),
        "description": transaction_data.get("description", "No description"),
        "tags": final_tags,
        "source": transaction_data.get("source"),
        "due_date": transaction_data.get("due_date"),
        "emotional_weight": transaction_data.get("emotional_weight", "medium"),
        "reconciliation_id": None,
        "mode": transaction_data.get("mode", "structured"),
        "content": md_content,  # <-- Markdown overlay
    }

    result = insert_row("transactions", transaction)
    return {
        "message": "Transaction logged",
        "transaction_id": transaction["transaction_id"],
        "content": md_content
    }
