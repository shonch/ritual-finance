# emotional_budget_tracker/rituals/core/setup_service.py

from emotional_budget_tracker.utils.mongo_client import insert_row, update_row, select_rows
from emotional_budget_tracker.utils.uuid_generator import generate_uuid
from emotional_budget_tracker.rituals.core.setup_utils import (
    format_currency,
    generate_due_dates,
    validate_frequency,
    total_components,
    advance_due_date_if_needed
)

def create_ritual_setup(user_id: str, name: str, category: str, amount: float,
                        frequency: str, due_date: str, archetype: str,
                        symbolic_tag: str, components: list = None,
                        principal: float = 0.0, interest_rate: float = 0.0,
                        recurrence: str = "none", arc_enabled: bool = False,
                        emotion_tag_id: str = None, start_date: str = None,
                        end_date: str = None, symbolic_time: str = None):
    setup_item = {
        "setup_id": generate_uuid(),
        "user_id": user_id,
        "name": name,
        "category": category,
        "amount": amount,
        "frequency": validate_frequency(frequency),
        "recurrence": recurrence,
        "is_one_time": recurrence == "none",
        "principal": principal,
        "interest_rate": interest_rate,
        "includes_interest": True,
        "due_date": due_date,
        "emotion_tag_id": emotion_tag_id,
        "archetype": archetype,
        "symbolic_tag": symbolic_tag,
        "arc_enabled": arc_enabled,
        "symbolic_time": symbolic_time,
        "start_date": start_date,
        "end_date": end_date,
        "active": True,
        "components": components or []
    }
    result = insert_row("setup_items", setup_item)
    return {"success": bool(result.inserted_id), "item": setup_item}

def edit_ritual_setup(user_id: str, setup_id: str, updates: dict):
    result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, updates)
    return {"success": result.modified_count == 1, "updates": updates}

def archive_ritual_setup(user_id: str, setup_id: str):
    result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, {"active": False})
    return {"success": result.modified_count == 1}

def view_ritual_setups(user_id: str):
    items = select_rows("setup_items", {"user_id": user_id, "active": True})
    # Optionally enrich with monthly equivalents and component totals
    enriched = []
    for item in items:
        monthly_estimate = item.get("amount", 0)
        enriched.append({
            **item,
            "monthly_equivalent": monthly_estimate,
            "total_components": total_components(item.get("components", []))
        })
    return {"active_items": enriched}
