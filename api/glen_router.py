# emotional_budget_tracker/api/glen_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timedelta

from emotional_budget_tracker.utils.mongo_client import select_rows

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"
PHOENIX_API_URL = os.getenv("PHOENIX_API_URL", "http://127.0.0.1:8000")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(prefix="/glen", tags=["glen"])


def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@router.get("/")
def view_glen(
    user_id: str = Depends(verify_jwt),
    token: str = Depends(oauth2_scheme),
    days: int = Query(14)
):
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Valhalla's own recent transactions
    transactions = select_rows("transactions", {"user_id": user_id, "date": {"$gte": cutoff}})
    for t in transactions:
        if "_id" in t:
            t["_id"] = str(t["_id"])

    # Phoenix fragments in the same window, via the shared-token bridge
    fragments = []
    try:
        resp = requests.get(
            f"{PHOENIX_API_URL}/phoenix/state/",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        raw = resp.json().get("raw", {})
        for key in ["fragments", "emotional_fragments", "revelations"]:
            for f in raw.get(key, []):
                ts = f.get("timestamp") or f.get("date")
                if ts and str(ts)[:10] >= cutoff:
                    fragments.append({
                        "id": f.get("id") or f.get("_id"),
                        "date": str(ts)[:10],
                        "subject": f.get("subject") or f.get("title"),
                        "tags": f.get("tags", [])
                    })
    except requests.exceptions.RequestException:
        pass  # Glen still shows transactions even if Phoenix is unreachable

    return {"transactions": transactions, "fragments": fragments, "window_days": days}
