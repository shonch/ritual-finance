from utils.supabase_client import get_supabase_client

supabase = get_supabase_client()
setup_id = "bf6054fb-5603-4169-b722-85cbe8b4e2cf"

supabase.table("setup_items").update({
    "interest_rate": 0.1599,
    "arc_enabled": True
}).eq("setup_id", setup_id).execute()

print("✅ Interest rate updated to 15.99%. Arc simulation now enabled.")
