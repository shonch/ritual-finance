# emotional_budget_tracker/api/interest_router.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.schemas import InterestUpdate, InterestOut

# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/interest", tags=["interest"])

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
@router.patch("/update", response_model=InterestOut, summary="Update user interest")
def update_interest(interest: InterestUpdate, user_id: str = Depends(verify_jwt)):
    interest_doc = {
        "interest_id": f"{user_id}-interest",  # replace with UUID if you prefer
        "user_id": user_id,
        "interest": interest.interest,
        "level": interest.level,
    }
    insert_row("interests", interest_doc)
    return {"message": "Interest updated", "interest_id": interest_doc["interest_id"]}
