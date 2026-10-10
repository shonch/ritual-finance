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
            "overdue": overdue,
            "payments_remaining": item.get("payments_remaining"),
            "total_payments": item.get("total_payments"),
            "current_balance": item.get("current_balance"),
            "archetype": item.get("archetype"),
            "symbolic_tag": item.get("symbolic_tag"),
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


@router.delete("/{setup_id}")
def delete_setup_item(setup_id: str, user_id: str = Depends(verify_jwt)):
    from emotional_budget_tracker.utils.mongo_client import delete_row
    result = delete_row("setup_items", {"setup_id": setup_id, "user_id": user_id})
    return {"message": "Burden removed", "setup_id": setup_id, "deleted": result.deleted_count > 0}
