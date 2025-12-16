# prompts/emotion_tag_prompt.py

from emotional_budget_tracker.utils.emotion_tags import get_or_create_emotion_tag

def select_emotion_tag(user_id):
    print("\n🧠 Choose an Emotion Tag:")
    choice = input("Enter a tag label (or type a new one): ")

    # Always call Phoenix to ensure tag exists
    tag_id = get_or_create_emotion_tag(choice, user_id=user_id)

    return tag_id
