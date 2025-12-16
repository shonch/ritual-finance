
from emotional_budget_tracker.utils.mongo_client import update_row





def update_interest_rate(setup_id: str, rate: float, arc_enabled: bool = True):
    update_row(
        "setup_items",
        {"setup_id": setup_id},
        {
            "interest_rate": rate,
            "arc_enabled": arc_enabled
        }
    )
    return {
        "message": f"✅ Interest rate updated to {rate * 100:.2f}%. Arc simulation {'enabled' if arc_enabled else 'disabled'}."
    }`
