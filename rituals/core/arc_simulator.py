from emotional_budget_tracker.utils.mongo_client import select_rows
from datetime import datetime, timedelta

def simulate_payoff_arc(item: dict):
    # 🕯️ Skip simulation for one-time items
    if item.get("recurrence") == "none" or item.get("is_one_time", False):
        return {
            "status": "skipped",
            "reason": "One-time ritual, arc simulation not applicable",
            "label": item.get("label")
        }

    # Validate required fields
    if not item.get("principal") or not item.get("interest_rate"):
        return {
            "status": "error",
            "reason": "Missing principal or interest rate",
            "label": item.get("label")
        }

    principal = float(item["principal"])
    interest_rate = float(item["interest_rate"]) / 100 / 12  # monthly rate
    monthly_payment = float(item["amount"])

    includes_interest = item.get("includes_interest", True)
    balance = principal
    months = 0
    total_interest = 0

    while balance > 0:
        interest = balance * interest_rate
        if includes_interest:
            principal_payment = monthly_payment - interest
            if principal_payment <= 0:
                return {
                    "status": "error",
                    "reason": "Monthly payment too low to reduce principal",
                    "label": item.get("label")
                }
            balance -= principal_payment
        else:
            balance += interest
            balance -= monthly_payment
        total_interest += interest
        months += 1

    payoff_date = datetime.today() + timedelta(days=months * 30)

    return {
        "status": "ok",
        "label": item.get("label"),
        "months_to_payoff": months,
        "total_interest_paid": round(total_interest, 2),
        "estimated_payoff_date": str(payoff_date.date()),
        "symbolic_tag": item.get("symbolic_tag"),
        "emotion_tag_id": item.get("emotion_tag_id")
    }

def run_arc_simulation(user_id: str):
    # Pull active setup items for this user
    items = select_rows("setup_items", {"user_id": user_id, "active": True})
    results = []
    for item in items:
        results.append(simulate_payoff_arc(item))
    return {"user_id": user_id, "arc_simulations": results}
