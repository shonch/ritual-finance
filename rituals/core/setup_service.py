# emotional_budget_tracker/rituals/core/setup_service.py

from emotional_budget_tracker.utils.mongo_client import insert_row, update_row, select_rows
from datetime import datetime
from emotional_budget_tracker.utils.uuid_generator import generate_uuid
from emotional_budget_tracker.rituals.core.setup_utils import (
    format_currency,
    validate_frequency,
    total_components,
    step_recurrence,
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

def apply_burden_payment(user_id: str, setup_id: str, payment_amount: float = None):
    """
    Marks one cycle of a Burden as paid.

    - Recurring Burdens: advances due_date forward by one real calendar
      cycle (via step_recurrence), and decrements payments_remaining if a
      total_payments count was set. Hitting zero deactivates the Burden —
      it's fully paid off, nothing left to schedule.
    - One-time Burdens (recurrence == "none"): a payment simply finishes
      it — mark inactive.

    payment_amount is accepted but no longer used for any balance math —
    Valhalla doesn't model principal/interest splits (that's proprietary
    to each servicer and effectively unknowable from outside). Kept as a
    parameter only so existing callers don't need to change their request
    shape.
    """
    items = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id, "active": True})
    if not items:
        return {"success": False, "error": "Burden not found."}

    item = items[0]
    recurrence = item.get("recurrence", "none")
    due_str = item.get("due_date")

    updates = {}
    paid_off = False

    if recurrence != "none" and due_str:
        try:
            current_due = datetime.strptime(due_str, "%Y-%m-%d").date()
            updates["due_date"] = step_recurrence(current_due, recurrence).strftime("%Y-%m-%d")
        except ValueError:
            pass

        payments_remaining = item.get("payments_remaining")
        if payments_remaining is not None:
            payments_remaining = max(payments_remaining - 1, 0)
            updates["payments_remaining"] = payments_remaining
            if payments_remaining == 0:
                updates["active"] = False
                paid_off = True
    else:
        updates["active"] = False
        paid_off = True

    result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, updates)

    return {
        "success": result.modified_count == 1,
        "new_due_date": updates.get("due_date"),
        "payments_remaining": updates.get("payments_remaining"),
        "paid_off": paid_off
    }
