from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "your-mongodb-uri-here")
client = MongoClient(MONGO_URI)
db = client["valhallabank"]
users_collection = db["users"]

def add_user(user_id, name=None, email=None, note=None):
    user_data = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "note": note
    }
    users_collection.insert_one(user_data)
    print(f"👤 User added: {user_id}")

def user_exists(user_id):
    return users_collection.count_documents({"user_id": user_id}) > 0

def get_user(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user and "_id" in user:
        user["_id"] = str(user["_id"])
    return user
