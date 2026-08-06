from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

from emotional_budget_tracker.utils.mongo_client import insert_row, select_rows
from emotional_budget_tracker.rituals.core.dashboard import generate_dashboard

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(prefix="/hoard", tags=["hoard"])


def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")


@router.post("/create")
def create_asset(payload: dict, user_id: str = Depends(verify_jwt)):
    asset = {
        "asset_id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": payload.get("name"),
        "value": payload.get("value", 0.0),
        "created_at": datetime.utcnow().isoformat(),
    }
    result = insert_row("assets", asset)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to place asset.")
    return {"message": f"'{asset['name']}' added to the Hoard.", "asset_id": asset["asset_id"]}


@router.get("/view")
def view_hoard(user_id: str = Depends(verify_jwt)):
    assets = select_rows("assets", {"user_id": user_id})
    for a in assets:
        if "_id" in a:
            a["_id"] = str(a["_id"])

    total_assets = sum(a.get("value", 0) for a in assets)

    debt_data = generate_dashboard(user_id)
    total_debt = sum(c["amount"] for c in debt_data.get("commitments", []))

    return {
        "assets": assets,
        "total_assets": total_assets,
        "total_debt": total_debt,
        "net_worth": total_assets - total_debt,
    }
