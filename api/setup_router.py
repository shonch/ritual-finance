from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timedelta

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


@router.post("/create")
def create_setup_item_route(payload: dict, user_id: str = Depends(verify_jwt)):
    recurrence = payload.get("recurrence", "none")
    is_one_time = recurrence == "none"
    frequency = recurrence if not is_one_time else "one-time"

    setup_item = {
        "setup_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": payload.get("name"),
        "category": payload.get("category"),
        "amount": payload.get("amount"),
        "frequency": frequency,
        "recurrence": recurrence,
        "is_one_time": is_one_time,
        "principal": payload.get("principal") or 0.0,
        "interest_rate": payload.get("interest_rate") or 0.0,
        "includes_interest": True,
        "due_date": payload.get("due_date"),
        "emotion_tag_id": payload.get("emotion_tag_id"),
        "archetype": payload.get("archetype") or "Unassigned",
        "symbolic_tag": payload.get("symbolic_tag") or "Untitled",
        "arc_enabled": payload.get("arc_enabled") or False,
        "symbolic_time": payload.get("symbolic_time"),
        "start_date": payload.get("start_date") or payload.get("due_date"),
        "end_date": payload.get("end_date"),
        "active": True,
        "components": payload.get("components") or [],
        "current_balance": payload.get("current_balance"),
        "term_months": payload.get("term_months"),

        }

    result = insert_row("setup_items", setup_item)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to place setup item.")

    return {"message": f"'{setup_item['name']}' placed in the ritual field.", "setup_id": setup_item["setup_id"]}


from emotional_budget_tracker.rituals.core.dashboard import generate_dashboard

@router.get("/dashboard")
def view_setup_dashboard(user_id: str = Depends(verify_jwt)):
    return generate_dashboard(user_id)

@router.post("/mark-agreed")
def mark_agreed(user_id: str = Depends(verify_jwt)):
    insert_row("reckoning_log", {"user_id": user_id, "date": datetime.utcnow().isoformat()})
    return {"message": "Marked agreed."}


@router.get("/last-reckoned")
def last_reckoned(user_id: str = Depends(verify_jwt)):
    from emotional_budget_tracker.utils.mongo_client import select_rows
    logs = select_rows("reckoning_log", {"user_id": user_id})
    if not logs:
        return {"last_reckoned_date": None}
    latest = max(logs, key=lambda l: l["date"])
    return {"last_reckoned_date": latest["date"]}



@router.post("/mark-agreed")
def mark_agreed(user_id: str = Depends(verify_jwt)):
    insert_row("reckoning_log", {"user_id": user_id, "date": datetime.utcnow().isoformat()})
    return {"message": "Marked agreed."}


@router.get("/last-reckoned")
def last_reckoned(user_id: str = Depends(verify_jwt)):
    from emotional_budget_tracker.utils.mongo_client import select_rows
    logs = select_rows("reckoning_log", {"user_id": user_id})
    if not logs:
        return {"last_reckoned_date": None}
    latest = max(logs, key=lambda l: l["date"])
    return {"last_reckoned_date": latest["date"]}
