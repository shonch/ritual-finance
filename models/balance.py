from datetime import date, datetime, timedelta
from calendar import monthrange
from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.utils.mongo_client import select_rows


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


def calculate_balance(user_id, start_date=None, end_date=None, mode=None, category=None):
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


def _is_landed(t):
    """Missing status = pre-existing transaction, treated as landed by default."""
    return t.get("status", "posted") == "posted"


def _signed_amount(t):
    amt = t.get("amount", 0)
    ttype = t.get("type")
    if ttype == "expense":
        return -amt
    return amt  # income and adjustment both add


def calculate_available_balance(user_id):
    """Real, spendable balance — landed transactions only, ignores anything foretold."""
    transactions = select_rows("transactions", {"user_id": user_id})
    landed = [t for t in transactions if _is_landed(t)]

    income_total = sum(t.get("amount", 0) for t in landed if t.get("type") == "income")
    expense_total = sum(t.get("amount", 0) for t in landed if t.get("type") == "expense")
    adjustment_total = sum(t.get("amount", 0) for t in landed if t.get("type") == "adjustment")
    balance = income_total - expense_total + adjustment_total

    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": balance,
        "transaction_count": len(landed)
    }


def calculate_daily_projection(user_id, through_date=None):
    """
    Walks forward day by day from today, starting at the current available
    (landed-only) balance, applying each foretold transaction on its scheduled
    date. Returns a list of {date, balance, income_amount, expense_amount}
    covering every day through `through_date` (defaults to end of current month).
    Days with nothing foretold simply carry the balance forward unchanged.
    """
    today = date.today()

    if through_date is None:
        last_day = monthrange(today.year, today.month)[1]
        through_date = date(today.year, today.month, last_day)
    elif isinstance(through_date, str):
        through_date = datetime.strptime(through_date, "%Y-%m-%d").date()

    available = calculate_available_balance(user_id)
    running_balance = available["balance"]

    transactions = select_rows("transactions", {"user_id": user_id})

    # Only foretold (scheduled) transactions matter for the walk forward —
    # landed ones are already baked into the starting balance.
    foretold = [t for t in transactions if not _is_landed(t)]

    # Group foretold amounts by date, tracking income and expense separately
    # so the calendar can show what kind of thing is landing that day.
    by_date = {}
    for t in foretold:
        t_date_str = t.get("date")
        if not t_date_str:
            continue
        try:
            t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        entry = by_date.setdefault(t_date, {"income": 0, "expense": 0})
        amt = t.get("amount", 0)
        if t.get("type") == "expense":
            entry["expense"] += amt
        elif t.get("type") == "income":
            entry["income"] += amt
        # adjustments affect the running balance but aren't shown as a
        # gold/ash mark, since they're corrections rather than real
        # incoming/outgoing money

    daily = []
    current = today
    while current <= through_date:
        day_entry = by_date.get(current, {"income": 0, "expense": 0})

        # Apply the day's net effect to the running balance.
        # (adjustments, if any landed this day, still shift the balance
        # even though they're not surfaced as income/expense marks)
        adjustment_total = sum(
            t.get("amount", 0)
            for t in foretold
            if t.get("date") == str(current) and t.get("type") == "adjustment"
        )
        running_balance += day_entry["income"] - day_entry["expense"] + adjustment_total

        daily.append({
            "date": str(current),
            "balance": running_balance,
            "income_amount": day_entry["income"],
            "expense_amount": day_entry["expense"]
        })
        current += timedelta(days=1)

    return daily

def calculate_end_of_month_projection(user_id):
    """Single number: projected balance at the end of the current month."""
    daily = calculate_daily_projection(user_id)
    if not daily:
        return calculate_available_balance(user_id)["balance"]
    return daily[-1]["balance"]



def _is_landed(t):
    """
    Landed means status == "posted". For transactions predating the status
    field (no status at all), fall back to date: today or past = landed,
    future-dated = foretold — rather than blindly assuming posted.
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

    return t_date <= date.today()
