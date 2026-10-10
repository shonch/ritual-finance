from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timedelta
from emotional_budget_tracker.rituals.core.setup_service import apply_burden_payment
from emotional_budget_tracker.rituals.core.dashboard import generate_dashboard
from emotional_budget_tracker.rituals.core.setup_utils import effective_due_date
from emotional_budget_tracker.utils.mongo_client import insert_row


load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(prefix="/setup", tags=["setup"])


def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

VALID_RECURRENCES = {"none", "weekly", "biweekly", "monthly", "quarterly", "annually"}

VALID_RECURRENCES = {"none", "weekly", "biweekly", "monthly", "quarterly", "annually"}


def _parse_date(value, field_name, required=False):
    """Validates a YYYY-MM-DD string. Returns the string, or None if blank and optional."""
    if value in (None, ""):
        if required:
            raise HTTPException(status_code=400, detail=f"{field_name} is required.")
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a date in YYYY-MM-DD format.")
    return value


def _parse_positive_int(value, field_name):
    """Returns a whole number >= 1, or None if the field was left blank."""
    if value in (None, ""):
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field_name} must be a whole number.")
    if n < 1:
        raise HTTPException(status_code=400, detail=f"{field_name} must be at least 1.")
    return n


@router.post("/create")
def create_setup_item_route(payload: dict, user_id: str = Depends(verify_jwt)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="A Burden needs a name.")

    try:
        amount = float(payload.get("amount"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Amount must be a number.")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero.")

    recurrence = (payload.get("recurrence") or "none").lower()
    if recurrence not in VALID_RECURRENCES:
        raise HTTPException(status_code=400, detail=f"Recurrence must be one of: {', '.join(sorted(VALID_RECURRENCES))}.")
    is_one_time = recurrence == "none"
    frequency = "one-time" if is_one_time else recurrence

    due_date = _parse_date(payload.get("due_date"), "due_date", required=True)
    start_date = _parse_date(payload.get("start_date"), "start_date") or due_date
    end_date = _parse_date(payload.get("end_date"), "end_date")

    # Payment countdown. A one-time Burden is a single occurrence by definition,
    # so it never carries a count. For recurring ones, entering either number
    # fills in the other; if both are given, remaining can't exceed total.
    total_payments = _parse_positive_int(payload.get("total_payments"), "total_payments")
    payments_remaining = _parse_positive_int(payload.get("payments_remaining"), "payments_remaining")

    if is_one_time:
        total_payments = None
        payments_remaining = None
    else:
        if total_payments is not None and payments_remaining is None:
            payments_remaining = total_payments
        elif payments_remaining is not None and total_payments is None:
            total_payments = payments_remaining
        if payments_remaining is not None and payments_remaining > total_payments:
            raise HTTPException(status_code=400, detail="Payments remaining can't exceed total payments.")

    current_balance = payload.get("current_balance")
    if current_balance in (None, ""):
        current_balance = None
    else:
        try:
            current_balance = float(current_balance)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Current balance must be a number.")

    setup_item = {
        "setup_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": name,
        "plan_name": (payload.get("plan_name") or "").strip() or None,
        "category": payload.get("category"),
        "amount": amount,
        "frequency": frequency,
        "recurrence": recurrence,
        "is_one_time": is_one_time,
        "due_date": due_date,
        "start_date": start_date,
        "end_date": end_date,
        "total_payments": total_payments,
        "payments_remaining": payments_remaining,
        "current_balance": current_balance,
        "emotion_tag_id": payload.get("emotion_tag_id"),
        "archetype": payload.get("archetype") or "Unassigned",
        "symbolic_tag": payload.get("symbolic_tag") or "Untitled",
        "symbolic_time": payload.get("symbolic_time"),
        "components": payload.get("components") or [],
        "active": True,
    }

    result = insert_row("setup_items", setup_item)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to place setup item.")

    return {"message": f"'{setup_item['name']}' placed in the ritual field.", "setup_id": setup_item["setup_id"]}

@router.get("/dashboard")
def view_setup_dashboard(user_id: str = Depends(verify_jwt)):
    return generate_dashboard(user_id)

@router.get("/list")
def list_burdens(user_id: str = Depends(verify_jwt)):
    """
    Every active Burden, soonest due first. For the Burdens management page and
    any picker that needs the full set — unlike /dashboard, this isn't
    window-limited.
    """
    from emotional_budget_tracker.utils.mongo_client import select_rows
    today = datetime.utcnow().date()

    burdens = []
    for item in select_rows("setup_items", {"user_id": user_id, "active": True}):
        _, overdue = effective_due_date(item.get("due_date"), today)
        burdens.append({
            "setup_id": item.get("setup_id"),
            "name": item.get("name"),
            "plan_name": item.get("plan_name"),
            "category": item.get("category"),
            "amount": item.get("amount"),
            "recurrence": item.get("recurrence"),
            "is_one_time": item.get("is_one_time", False),
            "due_date": item.get("due_date"),
            "start_date": item.get("start_date"),
            "end_date": item.get("end_date"),
            "overdue": overdue,
            "payments_remaining": item.get("payments_remaining"),
            "total_payments": item.get("total_payments"),
            "current_balance": item.get("current_balance"),
            "archetype": item.get("archetype"),
            "symbolic_tag": item.get("symbolic_tag"),
            "symbolic_time": item.get("symbolic_time"),
        })

    burdens.sort(key=lambda b: b["due_date"] or "9999-12-31")
    return {"burdens": burdens}

@router.post("/mark-agreed")
def mark_agreed(user_id: str = Depends(verify_jwt)):
    insert_row("reckoning_log", {"user_id": user_id, "date": datetime.utcnow().isoformat()})
    return {"message": "Marked agreed."}


@router.get("/last-reckoned")
def last_reckoned(user_id: str = Depends(verify_jwt)):
    from emotional_budget_tracker.utils.mongo_client import select_rows
    logs = select_rows("reckoning_log", {"user_id": user_id}, sort=[("date", -1)], limit=1)
    if not logs:
        return {"last_reckoned_date": None}
    return {"last_reckoned_date": logs[0]["date"]}

@router.post("/{setup_id}/pay")
def pay_burden(setup_id: str, payload: dict, user_id: str = Depends(verify_jwt)):
    payment_amount = payload.get("amount")
    if payment_amount is None:
        raise HTTPException(status_code=400, detail="Payment amount is required.")
    return apply_burden_payment(user_id, setup_id, payment_amount)


@router.patch("/{setup_id}")
def edit_setup_item(setup_id: str, payload: dict, user_id: str = Depends(verify_jwt)):
    """
    Partial edit of one Burden. Only fields present in the payload change.
    Does not advance the schedule — only a payment does that.
    """
    from emotional_budget_tracker.utils.mongo_client import select_rows, update_row

    items = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id, "active": True})
    if not items:
        raise HTTPException(status_code=404, detail="Burden not found.")
    item = items[0]

    updates = {}

    if "name" in payload:
        name = (payload.get("name") or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="A Burden needs a name.")
        updates["name"] = name

    if "plan_name" in payload:
        updates["plan_name"] = (payload.get("plan_name") or "").strip() or None

    if "category" in payload:
        updates["category"] = payload.get("category")

    if "amount" in payload:
        try:
            amount = float(payload.get("amount"))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Amount must be a number.")
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than zero.")
        updates["amount"] = round(amount, 2)

    recurrence = item.get("recurrence") or "none"
    if "recurrence" in payload:
        recurrence = (payload.get("recurrence") or "none").lower()
        if recurrence not in VALID_RECURRENCES:
            raise HTTPException(
                status_code=400,
                detail=f"Recurrence must be one of: {', '.join(sorted(VALID_RECURRENCES))}.",
            )
        updates["recurrence"] = recurrence
        updates["is_one_time"] = recurrence == "none"
        updates["frequency"] = "one-time" if recurrence == "none" else recurrence

    if "due_date" in payload:
        updates["due_date"] = _parse_date(payload.get("due_date"), "due_date", required=True)
    if "start_date" in payload:
        updates["start_date"] = _parse_date(payload.get("start_date"), "start_date")
    if "end_date" in payload:
        updates["end_date"] = _parse_date(payload.get("end_date"), "end_date")

    # Payment countdown
    counts_in_payload = "total_payments" in payload or "payments_remaining" in payload
    if recurrence == "none":
        # A one-time Burden is a single occurrence; it never carries a count.
        if counts_in_payload or "recurrence" in payload:
            updates["total_payments"] = None
            updates["payments_remaining"] = None
    elif counts_in_payload:
        total = item.get("total_payments")
        remaining = item.get("payments_remaining")
        if "total_payments" in payload:
            total = _parse_positive_int(payload.get("total_payments"), "total_payments")
        if "payments_remaining" in payload:
            remaining = _parse_positive_int(payload.get("payments_remaining"), "payments_remaining")
        if remaining is not None and total is None:
            total = remaining
        elif total is not None and remaining is None and "payments_remaining" not in payload:
            remaining = total
        if remaining is not None and remaining > total:
            raise HTTPException(status_code=400, detail="Payments remaining can't exceed total payments.")
        updates["total_payments"] = total
        updates["payments_remaining"] = remaining

    if "current_balance" in payload:
        value = payload.get("current_balance")
        if value in (None, ""):
            updates["current_balance"] = None
        else:
            try:
                updates["current_balance"] = float(value)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="Current balance must be a number.")

    if "archetype" in payload:
        updates["archetype"] = payload.get("archetype") or "Unassigned"
    if "symbolic_tag" in payload:
        updates["symbolic_tag"] = payload.get("symbolic_tag") or "Untitled"
    if "symbolic_time" in payload:
        updates["symbolic_time"] = payload.get("symbolic_time") or None

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to change.")

    update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, updates)

    return {
        "message": f"'{updates.get('name', item.get('name'))}' updated.",
        "setup_id": setup_id,
        "updated_fields": sorted(updates.keys()),
    }


@router.delete("/{setup_id}")
def delete_setup_item(setup_id: str, user_id: str = Depends(verify_jwt)):
    from emotional_budget_tracker.utils.mongo_client import delete_row
    result = delete_row("setup_items", {"setup_id": setup_id, "user_id": user_id})
    return {"message": "Burden removed", "setup_id": setup_id, "deleted": result.deleted_count > 0}
