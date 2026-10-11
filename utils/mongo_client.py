# utils/mongo_client.py

from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

# Load MongoDB URI and database name from environment variables
MONGO_URI = os.getenv("VALHALLA_MONGO_URI")
print("🔍 VALHALLA_MONGO_URI in use:", MONGO_URI)
DB_NAME = os.getenv("VALHALLA_DB_NAME", "valhalla_ledger")

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


def update_row(collection_name, match_dict, update_dict):
    """Updates a document in the specified collection."""
    return get_collection(collection_name).update_one(match_dict, {"$set": update_dict})

def delete_row(collection_name, match_dict):
    """Deletes a document from the specified collection."""
    return get_collection(collection_name).delete_one(match_dict)

def select_rows(collection_name, filters=None, sort=None, limit=None, skip=None, projection=None):
    """
    Retrieves documents from the specified collection.
    sort: optional list of (field, direction) tuples, e.g. [("date", -1)]
    limit: optional int, max documents to return
    skip: optional int, number of matching documents to skip (for paging)
    projection: optional dict of fields to include/exclude, e.g. {"content": 0}
    """
    if filters is None:
        filters = {}
    cursor = get_collection(collection_name).find(filters, projection)
    if sort:
        cursor = cursor.sort(sort)
    if skip:
        cursor = cursor.skip(skip)
    if limit:
        cursor = cursor.limit(limit)
    return list(cursor)


def count_rows(collection_name, filters=None):
    """Returns how many documents in the collection match the filters."""
    return get_collection(collection_name).count_documents(filters or {})
