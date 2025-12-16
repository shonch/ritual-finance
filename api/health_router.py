# valhalla/api/health_router.py
from fastapi import APIRouter, HTTPException
import requests, os

PHOENIX_URL = os.getenv("PHOENIX_URL", "http://127.0.0.1:8000")

router = APIRouter(prefix="/health", tags=["valhalla-health"])

@router.get("/")
def health_check():
    try:
        resp = requests.get(f"{PHOENIX_URL}/health")
        if resp.status_code == 200:
            return {
                "valhalla_status": "ok",
                "phoenix_status": resp.json().get("status", "unknown"),
                "phoenix_service": resp.json().get("service", "phoenix")
            }
        else:
            raise HTTPException(status_code=resp.status_code, detail="Phoenix health check failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bridge error: {str(e)}")
