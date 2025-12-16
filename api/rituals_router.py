# emotional_budget_tracker/api/rituals_router.py
from fastapi import APIRouter, Depends, HTTPException

from emotional_budget_tracker.schemas import SetupItemCreate, SetupItemOut
from emotional_budget_tracker.rituals.core.setup_service import (
    create_ritual_setup,
    edit_ritual_setup,
    archive_ritual_setup,
    view_ritual_setups,
)
from emotional_budget_tracker.rituals.core.dashboard import generate_dashboard
from emotional_budget_tracker.rituals.core.arc_simulator import run_arc_simulation
from emotional_budget_tracker.rituals.reconciliation import run_reconciliation
from emotional_budget_tracker.api.auth_utils import verify_token

router = APIRouter(prefix="/rituals", tags=["rituals"])

@router.post("/setup", response_model=SetupItemOut, summary="Create ritual setup")
def setup_ritual(item: SetupItemCreate, user_id: str = Depends(verify_token)):
    result = create_ritual_setup(**item.dict())
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Failed to create setup item")
    return result["item"]

@router.get("/setup", summary="View active ritual setups")
def view_setups(user_id: str = Depends(verify_token)):
    return view_ritual_setups(user_id)

@router.put("/setup/{setup_id}", summary="Edit ritual setup")
def edit_setup(setup_id: str, updates: dict, user_id: str = Depends(verify_token)):
    return edit_ritual_setup(user_id, setup_id, updates)

@router.delete("/setup/{setup_id}", summary="Archive ritual setup")
def archive_setup(setup_id: str, user_id: str = Depends(verify_token)):
    return archive_ritual_setup(user_id, setup_id)

@router.get("/dashboard", summary="Generate ritual dashboard")
def ritual_dashboard(user_id: str = Depends(verify_token)):
    try:
        return generate_dashboard(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")

# Optional extras
@router.post("/arc_simulator", summary="Run arc simulation")
def arc_simulator(user_id: str = Depends(verify_token)):
    return run_arc_simulation(user_id)

@router.post("/reconciliation", summary="Run reconciliation logic")
def reconciliation(user_id: str = Depends(verify_token)):
    return run_reconciliation(user_id)
