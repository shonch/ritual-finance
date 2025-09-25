from utils.supabase_client import get_supabase_client

def get_or_create_emotion_tag(label):
    supabase = get_supabase_client()
    
    # Check if tag already exists
    response = supabase.table("emotion_tags").select("tag_id").eq("label", label).execute()
    data = response.data

    if data:
        return data[0]["tag_id"]
    else:
        # Create new tag with default metadata
        new_tag = {
            "tag_id": label,
            "label": label,
            "emoji": "🌀",  # default placeholder
            "category": "custom",
            "description": f"User-defined tag: {label}",
            "archetype": "emergent",
            "user_defined": "Y",
            "visibility": "private",
            "times_used": 1
        }
        supabase.table("emotion_tags").insert(new_tag).execute()
        return label
