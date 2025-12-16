# emotional_budget_tracker/api/inspiration_router.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.inspiration.quotes import fetch_quote, fetch_curated_quote
from emotional_budget_tracker.schemas import InspirationQuoteOut

# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/inspiration", tags=["inspiration"])

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
@router.get("/quote", response_model=InspirationQuoteOut, summary="Get an inspirational quote from ZenQuotes API")
def get_quote(user_id: str = Depends(verify_jwt)):
    quote = fetch_quote()
    return {"quote": quote}

@router.get("/curated", response_model=InspirationQuoteOut, summary="Get a curated inspirational quote")
def get_curated_quote(user_id: str = Depends(verify_jwt)):
    quote = fetch_curated_quote()
    return {"quote": quote}
