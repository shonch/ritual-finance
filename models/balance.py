# models/balance.py

from datetime import date, datetime, timedelta
from calendar import monthrange
from emotional_budget_tracker.utils.mongo_client import insert_row, select_rows
from emotional_budget_tracker.rituals.core.setup_utils import (
    step_recurrence, add_months, total_components
)


def insert_balance_snapshot(user_id, balance, source="manual", note=None):
    snapshot = {
        "user_id": user_id,
        "balance": balance,
        "source": source,
        "note": note
    }

    result = insert_row("account_balance", snapshot)

    if result.inserted_id:
        print(f"💾 Balance snapshot saved: ${balance:.2f} ({source})")
    else:
        print("⚠️ Failed to save balance snapshot.")


def _is_landed(t):
    """
    Landed means status == "posted". For transactions predating the status
    field (no status at all), fall back to date: today or past = landed,
    future-dated = foretold — rather than blindly assuming posted.
    Uses UTC explicitly rather than the server's local clock, since every
    other date in this system (transactions, Phoenix fragments) is UTC-based.
    """
    status = t.get("status")
    if status is not None:
        return status == "posted"

    t_date_str = t.get("date")
    if not t_date_str:
        return True  # no date at all — nothing to judge by, assume landed

    try:
        t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
    except ValueError:
        return True

    return t_date <= datetime.utcnow().date()


def calculate_balance(user_id, start_date=None, end_date=None, mode=None, category=None, include_scheduled=False):
    """
    Core balance calculation. Defaults to landed (posted) transactions only —
    what's actually in the bank, not what's foretold. Pass include_scheduled=True
    to also count scheduled/foretold transactions within the date range, for
    reporting views that explicitly want that broader picture.
    """
    query = {"user_id": user_id}

    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    if mode:
        query["mode"] = {"$regex": f"^{mode.strip()}$", "$options": "i"}
    if category:
        query["category"] = {"$regex": f"^{category.strip()}$", "$options": "i"}

    transactions = select_rows("transactions", query)

    if not include_scheduled:
        transactions = [t for t in transactions if _is_landed(t)]

    income_total = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
    expense_total = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
    adjustment_total = sum(t.get("amount", 0) for t in transactions if t.get("type") == "adjustment")
    balance = income_total - expense_total + adjustment_total

    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": balance,
        "transaction_count": len(transactions)
    }


def calculate_available_balance(user_id):
    """Real, spendable balance — landed transactions only, ignores anything foretold."""
    return calculate_balance(user_id)


def _parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _burden_occurrences(user_id, today, through_date):
    """
    Every payment the user's active Burdens are expected to make from today
    through `through_date`, as a list of
    {"date", "name", "amount", "overdue", "setup_id"}.

    The stored due_date is the truth — only a real payment advances it. So:
      - Occurrences start at the stored due_date and step forward by the
        Burden's recurrence (one-time Burdens have just the one).
      - Any occurrence dated before today is overdue: as far as Valhalla
        knows it hasn't been paid, so it's counted as due today (one entry
        per missed cycle) and flagged. The Ragnarök gap review is where
        "that one actually got paid" gets recorded.
      - payments_remaining and end_date, when set, cap how many occur.

    Read-only; nothing is written.
    """
    occurrences = []

    for item in select_rows("setup_items", {"user_id": user_id, "active": True}):
        current = _parse_date(item.get("due_date"))
        if current is None:
            continue

        recurrence = item.get("recurrence") or "none"
        recurring = recurrence != "none" and not item.get("is_one_time", False)
        remaining = item.get("payments_remaining")
        end_date = _parse_date(item.get("end_date"))
        amount = (item.get("amount") or 0) + total_components(item.get("components") or [])

        count = 0
        while count < 1000:  # safety cap against pathologically stale data
            if remaining is not None and count >= remaining:
                break
            if end_date is not None and current > end_date:
                break
            if current > through_date:
                break

            overdue = current < today
            occurrences.append({
                "date": today if overdue else current,
                "name": item.get("name"),
                "amount": amount,
                "overdue": overdue,
                "setup_id": item.get("setup_id"),
            })
            count += 1

            if not recurring:
                break
            current = step_recurrence(current, recurrence)

    return occurrences


def calculate_daily_projection(user_id, through_date=None):
    """
    Walks forward day by day from today, starting at the current available
    (landed-only) balance, applying each foretold transaction on its scheduled
    date and each Burden payment on its due date. Returns a list of
    {date, balance, income_amount, expense_amount, burden_amount, burdens}
    covering every day through `through_date` (defaults to end of current
    month). Days with nothing landing carry the balance forward unchanged.

    Foretold transactions dated before today are ignored (same as always —
    they were never landed, and a Ragnarök reset supersedes them). Burdens
    are different: an overdue one stays owed until acknowledged, so it lands
    on today's entry.
    """
    today = datetime.utcnow().date()

    if through_date is None:
        last_day = monthrange(today.year, today.month)[1]
        through_date = date(today.year, today.month, last_day)
    elif isinstance(through_date, str):
        through_date = datetime.strptime(through_date, "%Y-%m-%d").date()
    elif isinstance(through_date, datetime):
        through_date = through_date.date()

    running_balance = calculate_available_balance(user_id)["balance"]

    # Foretold transactions, grouped by date. Landed ones are already baked
    # into the starting balance. Adjustments move the balance but aren't
    # shown as real incoming/outgoing money — they're corrections.
    by_date = {}
    for t in select_rows("transactions", {"user_id": user_id}):
        if _is_landed(t):
            continue
        t_date = _parse_date(t.get("date"))
        if t_date is None:
            continue

        entry = by_date.setdefault(t_date, {"income": 0, "expense": 0, "adjustment": 0})
        amt = t.get("amount", 0)
        if t.get("type") == "expense":
            entry["expense"] += amt
        elif t.get("type") == "income":
            entry["income"] += amt
        elif t.get("type") == "adjustment":
            entry["adjustment"] += amt

    burdens_by_date = {}
    for occ in _burden_occurrences(user_id, today, through_date):
        burdens_by_date.setdefault(occ["date"], []).append(occ)

    empty = {"income": 0, "expense": 0, "adjustment": 0}
    daily = []
    current = today
    while current <= through_date:
        entry = by_date.get(current, empty)
        day_burdens = burdens_by_date.get(current, [])
        burden_total = sum(b["amount"] for b in day_burdens)

        running_balance += entry["income"] - entry["expense"] + entry["adjustment"] - burden_total

        daily.append({
            "date": str(current),
            "balance": running_balance,
            "income_amount": entry["income"],
            "expense_amount": entry["expense"],
            "burden_amount": burden_total,
            "burdens": [
                {"name": b["name"], "amount": b["amount"], "overdue": b["overdue"]}
                for b in day_burdens
            ],
        })
        current += timedelta(days=1)

    return daily


def calculate_end_of_month_projection(user_id):
    """Single number: projected balance at the end of the current month."""
    daily = calculate_daily_projection(user_id)
    if not daily:
        return calculate_available_balance(user_id)["balance"]
    return daily[-1]["balance"]


def calculate_cashflow_outlook(user_id, horizons_months=(1, 3, 6), floor=0.0):
    """
    The "will I have enough?" answer. Projects day by day out to the longest
    horizon, then for each horizon (in calendar months from today) reports the
    ending balance, the lowest point reached and the date it happens, and
    whether the balance dips below `floor` (default $0 — later this is where
    a minimum-balance goal plugs in) and when it first does.

    Also reports how much of what's owed is overdue Burden payments, so the
    dashboard can say so instead of folding it silently into the totals.
    """
    today = datetime.utcnow().date()
    horizons = sorted(set(horizons_months))

    daily = calculate_daily_projection(user_id, through_date=add_months(today, horizons[-1]))
    starting_balance = calculate_available_balance(user_id)["balance"]
    overdue_total = sum(b["amount"] for d in daily for b in d["burdens"] if b["overdue"])

    results = []
    for months in horizons:
        through = str(add_months(today, months))
        window = [d for d in daily if d["date"] <= through]

        lowest = min(window, key=lambda d: d["balance"])
        first_breach = next((d for d in window if d["balance"] < floor), None)

        results.append({
            "months": months,
            "through": through,
            "ending_balance": window[-1]["balance"],
            "lowest_balance": lowest["balance"],
            "lowest_date": lowest["date"],
            "breaches_floor": first_breach is not None,
            "first_breach_date": first_breach["date"] if first_breach else None,
        })

    return {
        "as_of": str(today),
        "starting_balance": starting_balance,
        "floor": floor,
        "overdue_burden_total": overdue_total,
        "horizons": results,
    }
