# models/user.py

from utils.mongo_client import insert_row, select_rows

def add_user(user_id, name=None, email=None, note=None):
    user_data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "note": note
    }
    insert_row("users", user_data)
    print(f"👤 User added: {user_id}")

def user_exists(user_id):
    users = select_rows("users", {"user_id": user_id})
    return len(users) > 0

def get_user(user_id):
    users = select_rows("users", {"user_id": user_id})
    return users[0] if users else None
