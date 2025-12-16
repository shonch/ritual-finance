# emotional_budget_tracker/api/emotion_tags_router.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.schemas import EmotionTagCreate, EmotionTagOut

# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/emotion_tags", tags=["emotion-tags"])

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
@router.post("/", response_model=EmotionTagOut, summary="Create a new emotion tag")
def create_emotion_tag(tag: EmotionTagCreate, user_id: str = Depends(verify_jwt)):
    tag_doc = {
        "tag_id": f"{user_id}-tag",  # replace with UUID if you prefer
        "user_id": user_id,
        "tag": tag.tag,
        "intensity": tag.intensity,
    }
    insert_row("emotion_tags", tag_doc)
    return {"message": "Emotion tag created", "tag_id": tag_doc["tag_id"]}
