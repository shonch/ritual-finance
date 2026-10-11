# emotional_budget_tracker/api/transactions_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from bson import ObjectId
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel


from emotional_budget_tracker.models.transaction import (
    log_transaction_from_api,
    mark_transaction_posted,
    delete_transaction,
    edit_scheduled_transaction,
    TransactionError,
)
from emotional_budget_tracker.utils.mongo_client import select_rows, count_rows
from emotional_budget_tracker.schemas import TransactionCreate, TransactionOut

# --- Environment ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/transactions", tags=["transactions"])
class TransactionEdit(BaseModel):
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
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
@router.post("/", response_model=TransactionOut, summary="Create a new transaction")
async def create_transaction(transaction: TransactionCreate, user_id: str = Depends(verify_jwt)):
    return log_transaction_from_api(user_id, transaction.dict())

@router.get("/last-entry", summary="Most recent posted transaction date")
def last_entry_date(user_id: str = Depends(verify_jwt)):
    results = select_rows(
        "transactions",
        {"user_id": user_id, "status": "posted"},
        sort=[("date", -1)],
        limit=1
    )
    return {"last_date": results[0]["date"] if results else None}


TRANSACTION_SORTS = {
    "date_desc": [("date", -1), ("_id", -1)],
    "date_asc": [("date", 1), ("_id", 1)],
    "amount_desc": [("amount", -1), ("date", -1), ("_id", -1)],
    "amount_asc": [("amount", 1), ("date", -1), ("_id", -1)],
}
TRANSACTION_SEARCH_FIELDS = ("category", "source", "description", "tags")


@router.get("/", summary="View transactions with filters, search, sorting and paging")
def view_transactions(
    user_id: str = Depends(verify_jwt),
    category: str = Query(None),
    mode: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_amount: float = Query(None),
    max_amount: float = Query(None),
    q: str = Query(None, description="Search words; every word must appear in category, source, description or tags"),
    tx_type: str = Query(None, alias="type", description="income, expense or adjustment"),
    status: str = Query(None, description="scheduled or posted"),
    sort: str = Query("date_desc", description="date_desc, date_asc, amount_desc or amount_asc"),
    limit: int = Query(None, ge=1, le=500, description="Page size; omit to return everything"),
    skip: int = Query(0, ge=0),
    slim: bool = Query(False, description="Leave out the long 'content' field"),
):
    if sort not in TRANSACTION_SORTS:
        raise HTTPException(
            status_code=400,
            detail=f"sort must be one of: {', '.join(TRANSACTION_SORTS)}",
        )

    query = {"user_id": user_id}

    if category:
        query["category"] = {"$regex": f"^{re.escape(category.strip())}$", "$options": "i"}
    if mode:
        query["mode"] = {"$regex": f"^{re.escape(mode.strip())}$", "$options": "i"}
    if tx_type:
        query["type"] = tx_type.strip().lower()
    if status:
        query["status"] = status.strip().lower()
    if start_date or end_date:
        query["date"] = {}
        if start_date:
            query["date"]["$gte"] = start_date
        if end_date:
            query["date"]["$lte"] = end_date
    if min_amount is not None or max_amount is not None:
        query["amount"] = {}
        if min_amount is not None:
            query["amount"]["$gte"] = min_amount
        if max_amount is not None:
            query["amount"]["$lte"] = max_amount

    terms = (q or "").split()
    if terms:
        query["$and"] = [
            {
                "$or": [
                    {field: {"$regex": re.escape(term), "$options": "i"}}
                    for field in TRANSACTION_SEARCH_FIELDS
                ]
            }
            for term in terms
        ]

    total = count_rows("transactions", query)
    transactions = select_rows(
        "transactions",
        query,
        sort=TRANSACTION_SORTS[sort],
        limit=limit,
        skip=skip or None,
        projection={"content": 0} if slim else None,
    )

    for t in transactions:
        if "_id" in t and isinstance(t["_id"], ObjectId):
            t["_id"] = str(t["_id"])

    return {
        "transactions": transactions or [],
        "total": total,
        "limit": limit,
        "skip": skip,
    }


@router.patch("/{transaction_id}/mark-posted", summary="Mark a foretold transaction as landed")
def mark_posted(
    transaction_id: str,
    actual_date: str = Query(None, description="Optional: the day it actually landed (not in the future)"),
    user_id: str = Depends(verify_jwt),
):
    try:
        return mark_transaction_posted(user_id, transaction_id, actual_date)
    except TransactionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.patch("/{transaction_id}", summary="Edit a foretold (scheduled) transaction")
def edit_transaction_route(
    transaction_id: str,
    changes: TransactionEdit,
    user_id: str = Depends(verify_jwt),
):
    try:
        return edit_scheduled_transaction(
            user_id, transaction_id, changes.dict(exclude_unset=True)
        )
    except TransactionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))

@router.delete("/{transaction_id}", summary="Delete a foretold (scheduled) transaction")
def delete_transaction_route(transaction_id: str, user_id: str = Depends(verify_jwt)):
    try:
        return delete_transaction(user_id, transaction_id)
    except TransactionError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
