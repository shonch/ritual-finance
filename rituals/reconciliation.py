# rituals/reconciliation.py

from datetime import datetime
from utils.supabase_client import get_supabase_client
from prompts.emotion_tag_prompt import select_emotion_tag
from prompts.symbolic_time_prompt import select_symbolic_time
from models.balance import insert_balance_snapshot
from utils.uuid_generator import generate_uuid

def perform_reckoning(user_id):
    supabase = get_supabase_client()

    print("\n🔮 Summoning Valhalla Reckoning...")

    # Step 1: Fetch last known balance
    balance_response = supabase.table("account_balance").select("balance").eq("user_id", user_id).order("date", desc=True).limit(1).execute()
    previous_balance = balance_response.data[0]["balance"] if balance_response.data else 0.0

    # Step 2: Fetch unreconciled transactions
    tx_response = supabase.table("transactions").select("*").eq("user_id", user_id).eq("reconciliation_id", None).execute()
    transactions = tx_response.data

    income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    net_change = income - expenses
    calculated_balance = previous_balance + net_change

    print(f"\n📊 Previous Balance: ${previous_balance:.2f}")
    print(f"➕ Income: ${income:.2f}")
    print(f"➖ Expenses: ${expenses:.2f}")
    print(f"📈 Calculated Balance: ${calculated_balance:.2f}")

    # Step 3: Manual adjustment
    try:
        manual_adjustment = float(input("🩹 Manual Adjustment (if any): "))
    except ValueError:
        manual_adjustment = 0.0

    updated_balance = calculated_balance + manual_adjustment

    # Step 4: Emotional context
    emotional_tag = select_emotion_tag(user_id)
    symbolic_note = input("📝 Symbolic Note for this reckoning: ")
    symbolic_time = select_symbolic_time()

    # Step 5: Insert reconciliation event
    event_id = generate_uuid()
    supabase.table("reconciliation_events").insert({
        "event_id": event_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "previous_balance": previous_balance,
        "calculated_balance": calculated_balance,
        "manual_adjustment": manual_adjustment,
        "emotional_tag": emotional_tag,
        "symbolic_note": symbolic_note,
        "discrepancy_flag": manual_adjustment != 0.0,
        "updated_balance": updated_balance,
        "performed_by": user_id
    }).execute()

    # Step 6: Update account balance
    insert_balance_snapshot(user_id, updated_balance, source="reckoning", note=symbolic_note)

    # Step 7: Tag transactions with reconciliation_id
    for tx in transactions:
        supabase.table("transactions").update({
            "reconciliation_id": event_id
        }).eq("transaction_id", tx["transaction_id"]).execute()

    print(f"\n🌕 Reckoning complete. Updated balance: ${updated_balance:.2f}")
    print("🧘 May clarity guide your next step.")
