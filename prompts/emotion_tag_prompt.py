
# prompts/emotion_tag_prompt.py

from supabase_client import select_rows, insert_row
from utils.uuid_generator import generate_uuid

def select_emotion_tag(user_id):
    response = select_rows("emotion_tags", {"user_id": user_id})
    tags = response.data

    print("\n🧠 Choose an Emotion Tag:")
    for i, tag in enumerate(tags):
        emoji = tag.get("emoji", "")
        label = tag.get("label", "")
        print(f"{i+1}. {emoji} {label}")

    choice = input("Enter number or type a new tag: ")

    if choice.isdigit():
        selected = tags[int(choice)-1]
        return selected["tag_id"]
    else:
        new_tag = {
            "tag_id": generate_uuid(),
            "label": choice,
            "emoji": input("Emoji for this tag: "),
            "category": input("Category (e.g. grief, joy, closure): "),
            "description": input("Description: "),
            "archetype": input("Archetype (e.g. healer, rebel, seeker): "),
            "user_defined": "Y",
            "user_id": user_id,
            "visibility": "private",
            "intensity": input("Intensity (low, medium, high): "),
            "times_used": 1
        }
        insert_row("emotion_tags", new_tag)
        return new_tag["tag_id"]
