# utils/emotion_tags.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PHOENIX_API_URL = os.getenv("PHOENIX_API_URL", "http://localhost:8000")
PHOENIX_LOGIN_EMAIL = os.getenv("PHOENIX_LOGIN_EMAIL", "service@phoenix")
PHOENIX_LOGIN_PASSWORD = os.getenv("PHOENIX_LOGIN_PASSWORD", "change_me")

def get_phoenix_token():
    data = {"username": PHOENIX_LOGIN_EMAIL, "password": PHOENIX_LOGIN_PASSWORD}
    r = requests.post(f"{PHOENIX_API_URL}/token", data=data)
    r.raise_for_status()
    return r.json()["access_token"]

def get_or_create_emotion_tag(label, user_id="shon001", emoji="🌀", category="custom"):
    # Try to obtain a Phoenix JWT
    try:
        token = get_phoenix_token()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Phoenix token unavailable: {e}")
        # Fallback: allow the transaction to proceed with the plain label
        return label

    payload = {
        "tag_name": label,
        "user_id": user_id,
        "emoji": emoji,
        "category": category,
        "description": f"User-defined tag: {label}",
        "archetype": "emergent",
        "visibility": "private",
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.post(f"{PHOENIX_API_URL}/tags/", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data.get("tag_id", label)
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach Phoenix /tags: {e}")
        return label

def get_tags(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{PHOENIX_API_URL}/tags/", headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Failed to fetch tags: {r.text}")
