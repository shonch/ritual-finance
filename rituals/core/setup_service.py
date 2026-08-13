# emotional_budget_tracker/rituals/core/setup_service.py

from emotional_budget_tracker.utils.mongo_client import insert_row, update_row, select_rows
from datetime import timedelta, datetime
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

def apply_burden_payment(user_id: str, setup_id: str, payment_amount: float):
    """
    Apply a real payment against a burden's current_balance, using the same
    interest-then-principal split as the dashboard's projection math.
    Any payment amount is accepted — this isn't limited to the burden's
    nominal monthly amount.
    """
    items = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id, "active": True})
    if not items:
        return {"success": False, "error": "Burden not found."}

    item = items[0]
    current_balance = item.get("current_balance")
    interest_rate = item.get("interest_rate") or 0.0

    if current_balance is None:
        return {"success": False, "error": "This burden has no current balance to pay against."}

    interest_this_payment = current_balance * (interest_rate / 12)
    principal_this_payment = payment_amount - interest_this_payment
    new_balance = current_balance - principal_this_payment

    updates = {"current_balance": max(new_balance, 0)}
    if new_balance <= 0:
        updates["active"] = False  # paid off

    result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, updates)

    return {
        "success": result.modified_count == 1,
        "interest_applied": interest_this_payment,
        "principal_applied": principal_this_payment,
        "new_balance": updates["current_balance"],
        "paid_off": new_balance <= 0
    }

def apply_burden_payment(user_id: str, setup_id: str, payment_amount: float):
    """
    Apply a real payment against a burden. Handles three shapes:
    - Has current_balance: real interest/principal split, reduce balance,
      deactivate when paid off.
    - No current_balance, recurring: nothing to reduce — payment just
      advances due_date to the next cycle.
    - No current_balance, one-time (recurrence "none"): payment finishes
      it — mark inactive.
    """
    items = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id, "active": True})
    if not items:
        return {"success": False, "error": "Burden not found."}

    item = items[0]
    current_balance = item.get("current_balance")
    interest_rate = item.get("interest_rate") or 0.0
    recurrence = item.get("recurrence", "none")
    due_str = item.get("due_date")

    updates = {}
    interest_this_payment = None
    principal_this_payment = None
    new_balance = None
    paid_off = False

    if current_balance is not None:
        interest_this_payment = current_balance * (interest_rate / 12)
        principal_this_payment = payment_amount - interest_this_payment
        new_balance = current_balance - principal_this_payment
        updates["current_balance"] = max(new_balance, 0)
        if new_balance <= 0:
            paid_off = True

    if recurrence != "none" and due_str:
        delta_map = {
            "weekly": timedelta(weeks=1),
            "biweekly": timedelta(weeks=2),
            "monthly": timedelta(days=30),
            "quarterly": timedelta(days=90),
            "annually": timedelta(days=365)
        }
        delta = delta_map.get(recurrence.lower(), timedelta(days=30))
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d")
            updates["due_date"] = (due_date + delta).strftime("%Y-%m-%d")
        except ValueError:
            pass
    elif current_balance is None:
        # One-time burden, no balance to track — a payment simply finishes it
        updates["active"] = False
        paid_off = True

    if current_balance is not None and paid_off:
        updates["active"] = False

    result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, updates)

    return {
        "success": result.modified_count == 1,
        "interest_applied": interest_this_payment,
        "principal_applied": principal_this_payment,
        "new_balance": updates.get("current_balance"),
        "new_due_date": updates.get("due_date"),
        "paid_off": paid_off
    }
