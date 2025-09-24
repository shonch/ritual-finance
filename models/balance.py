from utils.supabase_client import get_supabase_client

def insert_balance_snapshot(user_id, balance, source="manual", note=None):
    """
    Inserts a balance snapshot into the account_balance table.

    Parameters:
    - user_id (str): The user's ID (must match users.user_id)
    - balance (float): The current balance to log
    - source (str): 'manual' or 'calculated'
    - note (str): Optional symbolic or emotional note
    """
    supabase = get_supabase_client()

    response = supabase.table("account_balance").insert({
        "user_id": user_id,
        "balance": balance,
        "source": source,
        "note": note
    }).execute()

    if response.status_code == 201:
        print(f"💾 Balance snapshot saved: ${balance:.2f} ({source})")
    else:
        print("⚠️ Failed to save balance snapshot:", response.status_code, response.data)
