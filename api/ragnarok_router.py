# emotional_budget_tracker/api/ragnarok_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime, date

from emotional_budget_tracker.utils.mongo_client import insert_row, select_rows
from emotional_budget_tracker.models.balance import calculate_available_balance
from emotional_budget_tracker.models.transaction import log_transaction_from_api

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(prefix="/ragnarok", tags=["ragnarok"])


def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@router.post("/reset")
def reset(payload: dict, user_id: str = Depends(verify_jwt)):
    """
    Completes a Ragnarök reset: records the reflection, computes the gap
    between what the Ledger currently believes and the true new balance,
    and writes that gap as a single adjustment transaction — the same
    mechanism a real bank reconciliation correction would use.
    """
    what_happened = payload.get("what_happened", "").strip()
    symbolic_image = payload.get("symbolic_image", "").strip()
    new_balance = payload.get("new_balance")

    if not what_happened:
        raise HTTPException(status_code=400, detail="The Stone requires an answer.")
    if new_balance is None:
        raise HTTPException(status_code=400, detail="A true balance is required to complete the reset.")

    try:
        new_balance = float(new_balance)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="New balance must be a number.")

    previous_balance = calculate_available_balance(user_id)["balance"]
    adjustment_amount = new_balance - previous_balance

    today_str = str(datetime.utcnow().date())

    tx_result = log_transaction_from_api(user_id, {
        "type": "adjustment",
        "category": "Ragnarök Reset",
        "amount": adjustment_amount,
        "date": today_str,
        "source": "ragnarok",
        "description": f"Reset to true balance of {new_balance:.2f}. {what_happened}",
    })

    log_entry = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "what_happened": what_happened,
        "symbolic_image": symbolic_image,
        "previous_balance": previous_balance,
        "new_balance": new_balance,
        "adjustment_amount": adjustment_amount,
        "transaction_id": tx_result.get("transaction_id"),
    }

    result = insert_row("ragnarok_log", log_entry)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to record the reset.")

    return {
        "message": "The old ledger ends here. A new one begins.",
        "previous_balance": previous_balance,
        "new_balance": new_balance,
        "adjustment_amount": adjustment_amount,
        "transaction_id": tx_result.get("transaction_id"),
    }


@router.get("/history", summary="Past Ragnarök reset events")
def history(user_id: str = Depends(verify_jwt)):
    logs = select_rows("ragnarok_log", {"user_id": user_id}, sort=[("timestamp", -1)])
    for l in logs:
        if "_id" in l:
            l["_id"] = str(l["_id"])
    return {"events": logs}
