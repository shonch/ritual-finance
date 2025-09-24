from utils.supabase_client import get_supabase_client
from utils.uuid_generator import generate_uuid

def get_or_create_emotion_tag(label, emoji=None, category=None, archetype=None, intensity=None):
    supabase = get_supabase_client()

    # Check if tag exists
    response = supabase.table("emotion_tags").select("tag_id").eq("label", label).single().execute()
    if response.data:
        return response.data["tag_id"]

    # Insert new tag with defaults
    new_tag = {
        "tag_id": generate_uuid(),
        "label": label,
        "emoji": emoji or "🌀",
        "category": category or "undefined",
        "description": "Created during ritual",
        "archetype": archetype or "Seeker",
        "user_defined": "Y",
        "related_tags": "",
        "intensity": intensity or "medium",
        "temporal_context": "unspecified",
        "visibility": "public",
        "times_used": 1,
        "last_used": "now()"  # Supabase can auto-handle this
    }

    insert_response = supabase.table("emotion_tags").insert(new_tag).execute()
    return insert_response.data[0]["tag_id"]
