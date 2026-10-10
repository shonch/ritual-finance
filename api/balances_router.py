# emotional_budget_tracker/api/balances_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
from pathlib import Path
from emotional_budget_tracker.models.balance import (
    calculate_balance,
    calculate_available_balance,
    calculate_daily_projection,
    calculate_end_of_month_projection,
    calculate_cashflow_outlook
)
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

@router.get("/available", summary="Real, spendable balance — landed transactions only")
def available_balance(user_id: str = Depends(verify_jwt)):
    return calculate_available_balance(user_id)


@router.get("/projection/daily", summary="Day-by-day projected balance walking forward through foretold transactions")
def daily_projection(
    user_id: str = Depends(verify_jwt),
    through_date: str = Query(None, description="Optional: project through this date (YYYY-MM-DD). Defaults to end of current month."),
):
    return {"daily": calculate_daily_projection(user_id, through_date)}


@router.get("/projection/end-of-month", summary="Single projected balance figure for the end of the current month")
def end_of_month_projection(user_id: str = Depends(verify_jwt)):
    return {"balance": calculate_end_of_month_projection(user_id)}

@router.get("/projection/outlook", summary="Will there be enough? Lowest point and ending balance at 1/3/6 months out")
def cashflow_outlook(
    user_id: str = Depends(verify_jwt),
    months: str = Query("1,3,6", description="Comma-separated horizons in months, e.g. 1,3,6"),
    floor: float = Query(0.0, description="Balance below which the outlook counts as a shortfall."),
):
    try:
        horizons = sorted({int(m) for m in months.split(",") if m.strip()})
    except ValueError:
        raise HTTPException(status_code=400, detail="months must be comma-separated whole numbers, e.g. 1,3,6")

    if not horizons or horizons[0] < 1 or horizons[-1] > 24 or len(horizons) > 6:
        raise HTTPException(status_code=400, detail="Give between 1 and 6 horizons, each between 1 and 24 months.")

    return calculate_cashflow_outlook(user_id, horizons_months=tuple(horizons), floor=floor)
