# emotional_budget_tracker/api/balances_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from pathlib import Path
from emotional_budget_tracker.models.balance import calculate_balance
from emotional_budget_tracker.schemas import BalanceUpdate, BalanceOut

# --- Environment ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/balances", tags=["balances"])

# --- JWT verification ---
def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

# --- Endpoints ---

@router.get("/view", summary="View balance history")
def view_balance(
    user_id: str = Depends(verify_jwt),
    start_date: str = Query(None),
    end_date: str = Query(None),
    mode: str = Query(None),
    category: str = Query(None),
):
    return calculate_balance(user_id, start_date, end_date, mode, category)
