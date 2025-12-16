from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.utils.mongo_client import select_rows

def insert_balance_snapshot(user_id, balance, source="manual", note=None):
    snapshot = {
        "user_id": user_id,
        "balance": balance,
        "source": source,
        "note": note
    }

    result = insert_row("account_balance", snapshot)

    if result.inserted_id:
        print(f"💾 Balance snapshot saved: ${balance:.2f} ({source})")
    else:
        print("⚠️ Failed to save balance snapshot.")

def calculate_balance(user_id, start_date=None, end_date=None, mode=None, category=None):
    query = {"user_id": user_id}

    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    if mode:
        query["mode"] = {"$regex": f"^{mode.strip()}$", "$options": "i"}
    if category:
        query["category"] = {"$regex": f"^{category.strip()}$", "$options": "i"}

    transactions = select_rows("transactions", query)

    income_total = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
    expense_total = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
    balance = income_total - expense_total

    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": balance,
        "transaction_count": len(transactions)
    }
