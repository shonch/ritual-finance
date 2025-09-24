# models/user.py

from utils.supabase_client import get_supabase_client

def add_user(user_id, name=None, email=None, note=None):
    """
    Adds a new user to the users table.

    Parameters:
    - user_id (str): Unique identifier for the user
    - name (str): Optional name
    - email (str): Optional email
    - note (str): Optional symbolic or emotional note
    """
    supabase = get_supabase_client()

    response = supabase.table("users").insert({
        "user_id": user_id,
        "name": name,
        "email": email,
        "note": note
    }).execute()

    if response.error:
        print("⚠️ Failed to add user:", response.error)
    else:
        print(f"👤 User added: {user_id}")

def user_exists(user_id):
    """
    Checks if a user already exists in the users table.

    Parameters:
    - user_id (str): Unique identifier for the user

    Returns:
    - bool: True if user exists, False otherwise
    """
    supabase = get_supabase_client()
    response = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
    return bool(response.data)

def get_user(user_id):
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("user_id", user_id).single().execute()
    return response.data

