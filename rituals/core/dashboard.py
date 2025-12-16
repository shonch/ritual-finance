from emotional_budget_tracker.utils.mongo_client import select_rows
from datetime import datetime, timedelta
from emotional_budget_tracker.rituals.core.setup_utils import (
    format_currency, total_components, advance_due_date_if_needed
)

def generate_dashboard(user_id: str, start_date=None, end_date=None):
    today = datetime.today()
    if not start_date:
        start_date = today
    if not end_date:
        end_date = today + timedelta(days=30)

    items = select_rows("setup_items", {"user_id": user_id, "active": True})
    recurring_total = 0.0
    commitments = []

    for item in items:
        item = advance_due_date_if_needed(item, today, update_db=True)
        component_total = total_components(item.get("components", []))
        amount = item.get("amount", 0)

        if item.get("includes_interest", True):
            total = amount + component_total
        else:
            monthly_interest = item.get("principal", 0) * item.get("interest_rate", 0) / 12
            total = amount + monthly_interest + component_total

        recurring_total += total
        commitments.append({
            "name": item.get("name"),
            "symbolic_tag": item.get("symbolic_tag"),
            "archetype": item.get("archetype"),
            "amount": total,
            "due_date": item.get("due_date"),
            "recurrence": item.get("recurrence"),
            "is_one_time": item.get("is_one_time", False)
        })

    return {
        "projection_window": {
            "start": str(start_date.date()),
            "end": str(end_date.date())
        },
        "commitments": commitments,
        "total_outflow": format_currency(recurring_total)
    }
