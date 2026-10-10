from emotional_budget_tracker.utils.mongo_client import select_rows
from datetime import datetime, timedelta
from emotional_budget_tracker.rituals.core.setup_utils import (
    format_currency, total_components, effective_due_date
)


def generate_dashboard(user_id: str, start_date=None, end_date=None):
    """
    Active Burdens due within the window (default: today through 30 days out),
    plus the total outflow for just that window. Overdue Burdens are always
    included, treated as due today.

    Read-only. Nothing here ever rewrites a Burden's due_date.
    Note: each Burden is counted once per window; multiple occurrences of a
    weekly/biweekly Burden inside one window come with the projection overlay.
    """
    today = datetime.utcnow().date()
    if start_date is None:
        start_date = today
    elif isinstance(start_date, datetime):
        start_date = start_date.date()

    if end_date is None:
        end_date = today + timedelta(days=30)
    elif isinstance(end_date, datetime):
        end_date = end_date.date()

    items = select_rows("setup_items", {"user_id": user_id, "active": True})
    recurring_total = 0.0
    commitments = []

    for item in items:
        effective, overdue = effective_due_date(item.get("due_date"), today)
        if effective is None:
            continue
        if not overdue and not (start_date <= effective <= end_date):
            continue

        total = item.get("amount", 0) + total_components(item.get("components", []))
        recurring_total += total

        commitments.append({
            "setup_id": item.get("setup_id"),
            "name": item.get("name"),
            "plan_name": item.get("plan_name"),
            "symbolic_tag": item.get("symbolic_tag"),
            "archetype": item.get("archetype"),
            "amount": total,
            "due_date": item.get("due_date"),
            "overdue": overdue,
            "recurrence": item.get("recurrence"),
            "is_one_time": item.get("is_one_time", False),
            "payments_remaining": item.get("payments_remaining"),
        })

    return {
        "projection_window": {"start": str(start_date), "end": str(end_date)},
        "commitments": commitments,
        "total_outflow": format_currency(recurring_total)
    }
