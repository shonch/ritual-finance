# rituals/reconciliation.py

from datetime import datetime
from emotional_budget_tracker.utils.mongo_client import select_rows, insert_row, update_row
from emotional_budget_tracker.prompts.emotion_tag_prompt import select_emotion_tag
from emotional_budget_tracker.prompts.symbolic_time_prompt import select_symbolic_time
from emotional_budget_tracker.models.balance import insert_balance_snapshot
from emotional_budget_tracker.utils.uuid_generator import generate_uuid

def run_reconciliation(user_id: str):
    # Step 1: Fetch last known balance
    balances = select_rows("account_balance", {"user_id": user_id})
    balances.sort(key=lambda b: b.get("date", ""), reverse=True)
    previous_balance = balances[0]["balance"] if balances else 0.0

    # Step 2: Fetch unreconciled transactions
    transactions = select_rows("transactions", {
        "user_id": user_id,
        "reconciliation_id": None
    })

    income = sum(tx["amount"] for tx in transactions if tx["type"] == "income")
    expenses = sum(tx["amount"] for tx in transactions if tx["type"] == "expense")
    net_change = income - expenses
    calculated_balance = previous_balance + net_change

    # Step 3: Manual adjustment (skip interactive input, default to 0)
    manual_adjustment = 0.0
    updated_balance = calculated_balance + manual_adjustment

    # Step 4: Emotional context
    emotional_tag = select_emotion_tag(user_id)
    symbolic_note = "API reconciliation"  # placeholder instead of input()
    symbolic_time = select_symbolic_time()

    # Step 5: Insert reconciliation event
    event_id = generate_uuid()
    insert_row("reconciliation_events", {
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
    })

    # Step 6: Update account balance
    insert_balance_snapshot(user_id, updated_balance, source="reckoning", note=symbolic_note)

    # Step 7: Tag transactions with reconciliation_id
    for tx in transactions:
        update_row("transactions", {"transaction_id": tx["transaction_id"]}, {
            "reconciliation_id": event_id
        })

    # Return structured JSON instead of prints
    return {
        "status": "ok",
        "event_id": event_id,
        "previous_balance": previous_balance,
        "income": income,
        "expenses": expenses,
        "calculated_balance": calculated_balance,
        "manual_adjustment": manual_adjustment,
        "updated_balance": updated_balance,
        "emotional_tag": emotional_tag,
        "symbolic_note": symbolic_note,
        "symbolic_time": symbolic_time,
        "transactions_reconciled": len(transactions)
    }
