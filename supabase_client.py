# supabase_client.py

from supabase import create_client, Client
import os

# Load from environment or fallback
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-or-service-role-key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_table(table_name):
    return supabase.table(table_name)

def insert_row(table_name, data):
    return supabase.table(table_name).insert(data).execute()

def select_rows(table_name, filters=None):
    query = supabase.table(table_name).select("*")
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    return query.execute()

def update_row(table_name, match_dict, update_dict):
    return supabase.table(table_name).update(update_dict).match(match_dict).execute()

def delete_row(table_name, match_dict):
    return supabase.table(table_name).delete().match(match_dict).execute()
