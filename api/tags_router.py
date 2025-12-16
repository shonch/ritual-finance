# emotional_budget_tracker/api/tags_router.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.schemas import ValhallaTagCreate, ValhallaTagOut

# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/tags", tags=["valhalla-tags"])

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
@router.post("/", response_model=ValhallaTagOut, summary="Create Tag")
def create_tag(tag: ValhallaTagCreate, user_id: str = Depends(verify_jwt)):
    tag_doc = {
        "tag_id": f"{user_id}-tag",  # replace with UUID if you prefer
        "user_id": user_id,
        "name": tag.name,
        "description": tag.description,
    }
    insert_row("tags", tag_doc)
    return {"message": "Tag created", "tag_id": tag_doc["tag_id"]}
