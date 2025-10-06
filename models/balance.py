from utils.mongo_client import insert_row

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
