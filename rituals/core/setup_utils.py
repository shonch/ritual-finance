# 🧰 core/setup_utils.py — Shared Ritual Tools

from datetime import date, datetime, timedelta
from calendar import monthrange
from emotional_budget_tracker.utils.mongo_client import update_row


def format_currency(amount):
    """Formats a float as currency string."""
    return f"${amount:,.2f}"


def total_components(components):
    """Returns the total amount from all components."""
    return sum(comp.get("amount", 0) for comp in components)


def _add_months(d: date, months: int) -> date:
    """
    Adds `months` calendar months to date `d`, preserving the day-of-month
    where valid and clamping to the target month's last valid day otherwise
    (e.g. Jan 31 + 1 month -> Feb 28 or Feb 29, not Mar 3).
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)

def add_months(d: date, months: int) -> date:
    """Public version of _add_months for callers outside this module."""
    return _add_months(d, months)

def step_recurrence(d: date, recurrence: str) -> date:
    """
    Steps a date forward by exactly one cycle of `recurrence`, using real
    calendar units instead of flat day counts. This is the single source
    of truth for recurrence math in Valhalla — we had three independent,
    identically-wrong "+30 days for monthly" implementations before this;
    everything should call this instead of keeping its own delta table.

    - weekly: +7 days
    - biweekly: +14 days
    - monthly: same day next calendar month (clamped for short months)
    - quarterly: same day, 3 calendar months forward (clamped)
    - annually: same month/day next year (clamped for Feb 29)
    - anything else/unrecognized: falls back to monthly stepping
    """
    r = (recurrence or "").lower()
    if r == "weekly":
        return d + timedelta(weeks=1)
    if r == "biweekly":
        return d + timedelta(weeks=2)
    if r == "quarterly":
        return _add_months(d, 3)
    if r == "annually":
        return _add_months(d, 12)
    return _add_months(d, 1)


def generate_due_dates(start_date: str, recurrence: str, count: int = 6) -> list:
    """
    Returns the next `count` occurrence dates (as "YYYY-MM-DD" strings),
    starting from and including `start_date`, stepped with step_recurrence.
    Read-only — doesn't touch the database.
    """
    try:
        current = datetime.strptime(start_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return []

    dates = [current.strftime("%Y-%m-%d")]
    for _ in range(count - 1):
        current = step_recurrence(current, recurrence)
        dates.append(current.strftime("%Y-%m-%d"))
    return dates


def next_occurrence_on_or_after(due_date_str: str, recurrence: str, reference_date: date = None) -> date:
    """
    Given a Burden's stored due_date and recurrence, returns the next
    occurrence date on or after `reference_date` (defaults to today),
    stepping forward with step_recurrence as many times as needed.

    This is read-only — it never writes to the database. It replaces the
    old advance_due_date_if_needed, which silently rewrote a Burden's
    due_date to "today" just because the dashboard was viewed, with no
    payment ever having happened. Only apply_burden_payment should ever
    persist a new due_date, and only when a real payment happens.

    One-time Burdens (recurrence == "none") or missing due dates are
    returned as-is / parsed, since there's nothing to step forward.
    """
    if reference_date is None:
        reference_date = datetime.utcnow().date()

    try:
        current = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return reference_date

    if not recurrence or recurrence == "none":
        return current

    for _ in range(1000):  # safety cap against pathologically stale data
        if current >= reference_date:
            return current
        current = step_recurrence(current, recurrence)

    return current


def validate_frequency(frequency):
    """Validates and normalizes frequency input."""
    valid = ["weekly", "biweekly", "monthly", "quarterly", "annually"]
    return frequency.lower() if frequency.lower() in valid else "monthly"


def get_emotion_tag():
    """Prompts user to select or enter an emotion tag. (CLI-only helper.)"""
    tags = [
        "🌀 Momentum",
        "🌉 Threshold Tension",
        "🪡 Thread of Trust",
        "🧮 Algorithmic Grip",
        "🌌 Wandering Debt"
    ]
    print("\n🧠 Choose an Emotion Tag:")
    for i, tag in enumerate(tags, 1):
        print(f"{i}. {tag}")
    choice = input("Enter number or type a new tag: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(tags):
        return tags[int(choice) - 1]
    return choice or "🌀 Momentum"


def effective_due_date(due_date_str: str, reference_date: date = None):
    """
    The date a Burden should be treated as due, for display and totals.

    The stored due_date is the truth — only a real payment (apply_burden_payment)
    ever advances it. If it's already in the past, the Burden is overdue and is
    treated as due on reference_date (today); it is never stepped forward, since
    that would quietly hide the fact that it's late.

    Returns (date, is_overdue), or (None, False) if the stored date is unusable.
    """
    if reference_date is None:
        reference_date = datetime.utcnow().date()

    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None, False

    if due < reference_date:
        return reference_date, True
    return due, False
