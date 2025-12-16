import requests
import jwt
import datetime

# Phoenix base URL
PHOENIX_URL = "http://127.0.0.1:8000"

# Step 1: Login to Phoenix to get JWT
login_payload = {
    "username": "service@phoenix",   # not "email"
    "password": "valhalla_bridge_2025!"
}
resp = requests.post(f"{PHOENIX_URL}/token", data=login_payload)
resp = requests.post(f"{PHOENIX_URL}/token", data=login_payload)
resp.raise_for_status()
token = resp.json()["access_token"]

print("Got JWT:", token)

# Step 2: Decode JWT locally (optional, just to see the sub/exp)
decoded = jwt.decode(token, options={"verify_signature": False})
print("Decoded JWT:", decoded)
print("Expires:", datetime.datetime.fromtimestamp(decoded["exp"]))

# Step 3: Use JWT to call /tags
headers = {"Authorization": f"Bearer {token}"}
tag_payload = {
    "tag_name": "valhalla_test_tag",
    "user_id": decoded["sub"],
    "description": "Testing Valhalla bridge to Phoenix"
}
resp = requests.post(f"{PHOENIX_URL}/tags/", json=tag_payload, headers=headers)
print("Tag creation response:", resp.status_code, resp.json())

