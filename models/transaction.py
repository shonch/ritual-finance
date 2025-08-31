
# models/transaction.py

from datetime import datetime
from supabase_client import insert_row
from prompts.emotion_tag_prompt import select_emotion_tag
from prompts.symbolic_time_prompt import select_symbolic_time
from utils.uuid_generator import generate_uuid

def log_transaction(user_id, entry_type):
    try:
        amount = float(input("💸 Amount: "))
    except ValueError:
        print("⚠️ Invalid amount. Try again.")
        return

    category = input("📂 Category (e.g. Lyft, Groceries, Studio Rent): ")
    source = input("🔗 Source (e.g. Lyft, Venmo, Cash): ")
    symbolic_time = select_symbolic_time()
    emotion_tag_id = select_emotion_tag(user_id)

    description = input("📝 Symbolic Note (e.g. 'Paid this to honor a promise'): ")
    due_date_input = input("📅 Due Date (YYYY-MM-DD, optional): ")
    due_date = due_date_input if due_date_input else None
    emotional_weight = input("⚖️ Emotional Weight (low, medium, high): ")

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": amount,
        "type": entry_type.lower(),
        "category": category,
        "date": datetime.now().isoformat(),
        "description": description,
        "tags": "",  # Optional: comma-separated emotional tags
        "source": source,
        "due_date": due_date,
        "emotional_weight": emotional_weight
    }

    insert_row("transactions", transaction)
    print(f"\n✅ Logged {entry_type}: ${amount:.2f} — {category} ({symbolic_time})")
