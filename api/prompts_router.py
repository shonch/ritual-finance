# emotional_budget_tracker/api/prompts_router.py
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from emotional_budget_tracker.prompts.emotion_tag_prompt import select_emotion_tag
from emotional_budget_tracker.prompts.symbolic_time_prompt import select_symbolic_time
from emotional_budget_tracker.schemas import EmotionPromptOut, TimePromptOut

# --- Environment ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")  # must match Phoenix
ALGORITHM = "HS256"

# --- OAuth2 setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Router ---
router = APIRouter(prefix="/prompts", tags=["prompts"])

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
@router.post("/emotion", response_model=EmotionPromptOut, summary="Generate an emotion prompt")
def generate_emotion_prompt(user_id: str = Depends(verify_jwt)):
    prompt = select_emotion_tag(user_id)
    return {"prompt": prompt}

@router.get("/time", response_model=TimePromptOut, summary="Generate a symbolic time prompt")
def generate_time_prompt(user_id: str = Depends(verify_jwt)):
    prompt = select_symbolic_time(user_id)
    return {"prompt": prompt}
