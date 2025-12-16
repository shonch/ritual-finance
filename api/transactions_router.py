# emotional_budget_tracker/api/transactions_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from bson import ObjectId
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.models.transaction import log_transaction_from_api
from emotional_budget_tracker.utils.mongo_client import select_rows
from emotional_budget_tracker.schemas import TransactionCreate, TransactionOut
# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/transactions", tags=["transactions"])

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

@router.get("/", summary="View transactions with filters")
def view_transactions(
    user_id: str = Depends(verify_jwt),
    category: str = Query(None),
    mode: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_amount: float = Query(None),
    max_amount: float = Query(None),
):
    query = {"user_id": user_id}

    if category:
        query["category"] = {"$regex": f"^{category.strip()}$", "$options": "i"}
    if mode:
        query["mode"] = {"$regex": f"^{mode.strip()}$", "$options": "i"}
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

    transactions = select_rows("transactions", query)

    for t in transactions:
        if "_id" in t and isinstance(t["_id"], ObjectId):
            t["_id"] = str(t["_id"])

    return {"transactions": transactions or []}
