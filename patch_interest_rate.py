from utils.mongo_client import update_row

setup_id = "bf6054fb-5603-4169-b722-85cbe8b4e2cf"

update_row(
    "setup_items",
    {"setup_id": setup_id},
    {
        "interest_rate": 0.1599,
        "arc_enabled": True
    }
)

print("✅ Interest rate updated to 15.99%. Arc simulation now enabled.")
