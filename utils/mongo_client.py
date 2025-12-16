# utils/mongo_client.py

from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

# Load MongoDB URI and database name from environment variables
MONGO_URI = os.getenv("MONGO_URI")
print("🔍 MONGO_URI in use:", MONGO_URI)
DB_NAME = os.getenv("DB_NAME")

def get_mongo_client():
    """Returns a MongoClient instance connected to the specified URI."""
    return MongoClient(MONGO_URI)

def get_database():
    """Returns the database object."""
    client = get_mongo_client()
    return client[DB_NAME]

def get_collection(name):
    """Returns a collection object from the database."""
    db = get_database()
    return db[name]

def insert_row(collection_name, data):
    """Inserts a document into the specified collection."""
    return get_collection(collection_name).insert_one(data)

def select_rows(collection_name, filters=None):
    """Retrieves documents from the specified collection."""
    if filters is None:
        filters = {}
    return list(get_collection(collection_name).find(filters))

def update_row(collection_name, match_dict, update_dict):
    """Updates a document in the specified collection."""
    return get_collection(collection_name).update_one(match_dict, {"$set": update_dict})

def delete_row(collection_name, match_dict):
    """Deletes a document from the specified collection."""
    return get_collection(collection_name).delete_one(match_dict)
