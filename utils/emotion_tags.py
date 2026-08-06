# utils/emotion_tags.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PHOENIX_API_URL = os.getenv("PHOENIX_API_URL", "http://localhost:8000")
PHOENIX_LOGIN_EMAIL = os.getenv("PHOENIX_LOGIN_EMAIL", "service@phoenix")
PHOENIX_LOGIN_PASSWORD = os.getenv("PHOENIX_LOGIN_PASSWORD", "change_me")

def get_phoenix_token():
    data = {"email": PHOENIX_LOGIN_EMAIL, "password": PHOENIX_LOGIN_PASSWORD}
    r = requests.post(f"{PHOENIX_API_URL}/auth/login", json=data)
    r.raise_for_status()
    return r.json()["token"]

def get_or_create_emotion_tag(label, token, category="custom"):
    payload = {
        "name": label,
        "category": category,
        "description": f"User-defined tag: {label}",
        "archetype": "emergent",
        "visibility": "private",
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.post(f"{PHOENIX_API_URL}/tags/create", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data.get("tag_id", label)
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach Phoenix /tags/create: {e}")
        return label

def get_tags(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{PHOENIX_API_URL}/tags/", headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Failed to fetch tags: {r.text}")
