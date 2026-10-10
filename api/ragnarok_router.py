# emotional_budget_tracker/api/ragnarok_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime, date

from emotional_budget_tracker.utils.mongo_client import insert_row, select_rows, update_row, delete_row
from emotional_budget_tracker.models.balance import calculate_available_balance
from emotional_budget_tracker.models.transaction import log_transaction_from_api
from emotional_budget_tracker.rituals.core.setup_service import apply_burden_payment
from emotional_budget_tracker.rituals.core.setup_utils import step_recurrence
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter(prefix="/ragnarok", tags=["ragnarok"])


def verify_jwt(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Token verification failed")

MAX_GAP_CYCLES = 12


def _due_cycles(item, today):
    """
    Cycles of one Burden that are due on or before `today`, oldest first,
    starting from the stored due_date (which is by definition the first
    unpaid cycle). Returns (cycles, truncated).

    A cycle is never offered beyond the Burden's end_date or beyond the
    number of payments it has left. One-time Burdens have a single cycle.
    At most MAX_GAP_CYCLES are returned; `truncated` says more were due.
    """
    due_str = item.get("due_date")
    if not due_str:
        return [], False
    try:
        due = datetime.strptime(due_str, "%Y-%m-%d").date()
    except ValueError:
        return [], False

    recurrence = item.get("recurrence") or "none"

    end = None
    if item.get("end_date"):
        try:
            end = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
        except ValueError:
            end = None

    limit = 1 if recurrence == "none" else item.get("payments_remaining")

    cycles = []
    truncated = False
    while due <= today:
        if end and due > end:
            break
        if limit is not None and len(cycles) >= limit:
            break
        if len(cycles) >= MAX_GAP_CYCLES:
            truncated = True
            break
        cycles.append(due.strftime("%Y-%m-%d"))
        if recurrence == "none":
            break
        due = step_recurrence(due, recurrence)

    return cycles, truncated


@router.get("/gap", summary="Burden payments that came due since the last entry")
def gap(user_id: str = Depends(verify_jwt)):
    """
    Read-only. For the Ragnarök reckoning: every active Burden with cycles
    due on or before today, so the user can say which were actually paid
    while the Ledger was dark. Must be read BEFORE the reset, because the
    reset's own adjustment becomes the new "last entry".
    """
    today = datetime.utcnow().date()

    last = select_rows(
        "transactions",
        {"user_id": user_id, "status": "posted"},
        sort=[("date", -1)],
        limit=1,
    )
    gap_start = last[0]["date"] if last else None

    burdens = []
    for item in select_rows("setup_items", {"user_id": user_id, "active": True}):
        cycles, truncated = _due_cycles(item, today)
        if not cycles:
            continue
        burdens.append({
            "setup_id": item.get("setup_id"),
            "name": item.get("name"),
            "plan_name": item.get("plan_name"),
            "amount": item.get("amount"),
            "recurrence": item.get("recurrence"),
            "cycles": [
                {"due_date": c, "before_gap": bool(gap_start and c < gap_start)}
                for c in cycles
            ],
            "truncated": truncated,
        })

    burdens.sort(key=lambda b: b["cycles"][0]["due_date"])
    return {"gap_start": gap_start, "today": str(today), "burdens": burdens}


@router.post("/reset")
def reset(payload: dict, user_id: str = Depends(verify_jwt)):
    """
    Completes a Ragnarök reset: records the reflection, computes the gap
    between what the Ledger currently believes and the true new balance,
    and writes that gap as a single adjustment transaction — the same
    mechanism a real bank reconciliation correction would use.

    Optionally takes `paid`: [{"setup_id": ..., "cycles": n}] — Burden
    payments the user confirms were made while the Ledger was dark. Each
    claim is checked against what was genuinely due BEFORE anything is
    written, and applied (schedule only, no transactions) afterwards. The
    balance already reflects that money leaving, so recording it again
    would double-count.

    Optionally takes `request_id`, one random value per reset attempt. The
    server claims it before doing any work, so a retry — a second click
    while the first request is still running on a slow server, or a resend
    after a lost response — can never run the reset twice. A retry of a
    finished reset gets the original result back, unchanged.
    """
    request_id = (payload.get("request_id") or "").strip() or None
    if request_id and len(request_id) > 100:
        raise HTTPException(status_code=400, detail="request_id is too long.")
    claim_filter = {"user_id": user_id, "request_id": request_id}

    # --- Already seen this attempt? ---------------------------------------
    if request_id:
        existing = select_rows("ragnarok_log", claim_filter)
        if existing:
            prior = existing[0]
            if prior.get("status") == "complete":
                return {
                    "message": "The old ledger ends here. A new one begins.",
                    "previous_balance": prior.get("previous_balance"),
                    "new_balance": prior.get("new_balance"),
                    "adjustment_amount": prior.get("adjustment_amount"),
                    "transaction_id": prior.get("transaction_id"),
                    "burdens_paid": prior.get("burdens_paid", []),
                    "burden_errors": prior.get("burden_errors", []),
                    "already_recorded": True,
                }
            raise HTTPException(
                status_code=409,
                detail="This reset is already being recorded. Give it a moment, then check your balance.",
            )

    what_happened = payload.get("what_happened", "").strip()
    symbolic_image = payload.get("symbolic_image", "").strip()
    new_balance = payload.get("new_balance")

    if not what_happened:
        raise HTTPException(status_code=400, detail="The Stone requires an answer.")
    if new_balance is None:
        raise HTTPException(status_code=400, detail="A true balance is required to complete the reset.")

    try:
        new_balance = float(new_balance)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="New balance must be a number.")

    # --- Validate the Burden claims before any write ---------------------
    paid = payload.get("paid") or []
    if not isinstance(paid, list):
        raise HTTPException(status_code=400, detail="'paid' must be a list.")

    today = datetime.utcnow().date()
    approved = []  # (burden record, number of cycles to apply)
    seen = set()
    for entry in paid:
        if not isinstance(entry, dict):
            raise HTTPException(status_code=400, detail="Each paid entry must be an object.")
        setup_id = entry.get("setup_id")
        try:
            cycles = int(entry.get("cycles", 0))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Paid cycles must be a whole number.")
        if cycles < 0:
            raise HTTPException(status_code=400, detail="Paid cycles can't be negative.")
        if cycles == 0:
            continue
        if setup_id in seen:
            raise HTTPException(status_code=400, detail="A Burden was listed twice.")
        seen.add(setup_id)

        items = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id, "active": True})
        if not items:
            raise HTTPException(status_code=400, detail="A Burden you marked as paid was not found.")
        due_cycles, _ = _due_cycles(items[0], today)
        if cycles > len(due_cycles):
            raise HTTPException(
                status_code=400,
                detail=f"'{items[0].get('name')}' has {len(due_cycles)} payment(s) due, not {cycles}. "
                       "Nothing was changed.",
            )
        approved.append((items[0], cycles))

    # --- Claim this attempt, then do the reset ---------------------------
    if request_id:
        claimed = insert_row("ragnarok_log", {
            **claim_filter,
            "status": "in_progress",
            "timestamp": datetime.utcnow().isoformat(),
        })
        if not claimed.inserted_id:
            raise HTTPException(status_code=500, detail="Could not begin the reset.")

    try:
        previous_balance = calculate_available_balance(user_id)["balance"]
        adjustment_amount = new_balance - previous_balance

        tx_result = log_transaction_from_api(user_id, {
            "type": "adjustment",
            "category": "Ragnarök Reset",
            "amount": adjustment_amount,
            "date": str(today),
            "source": "ragnarok",
            "description": f"Reset to true balance of {new_balance:.2f}. {what_happened}",
        })
    except Exception:
        # Nothing was written yet, so release the claim and let a retry run.
        if request_id:
            delete_row("ragnarok_log", claim_filter)
        raise

    # --- Advance the schedules the user confirmed paid -------------------
    burdens_paid = []
    burden_errors = []
    for item, cycles in approved:
        applied = 0
        last_result = {}
        for _ in range(cycles):
            last_result = apply_burden_payment(user_id, item["setup_id"])
            if not last_result.get("success"):
                break
            applied += 1
        if applied:
            burdens_paid.append({
                "setup_id": item["setup_id"],
                "name": item.get("name"),
                "cycles": applied,
                "new_due_date": last_result.get("new_due_date"),
                "paid_off": bool(last_result.get("paid_off")),
            })
        if applied < cycles:
            burden_errors.append(
                f"'{item.get('name')}': only {applied} of {cycles} payment(s) could be recorded."
            )

    log_fields = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "what_happened": what_happened,
        "symbolic_image": symbolic_image,
        "previous_balance": previous_balance,
        "new_balance": new_balance,
        "adjustment_amount": adjustment_amount,
        "transaction_id": tx_result.get("transaction_id"),
        "burdens_paid": burdens_paid,
        "burden_errors": burden_errors,
        "status": "complete",
    }

    if request_id:
        # The claim stays in place if this fails: a retry gets a "being
        # recorded" answer instead of running the reset a second time.
        finished = update_row("ragnarok_log", claim_filter, log_fields)
        if finished.modified_count != 1:
            raise HTTPException(status_code=500, detail="Failed to record the reset.")
    else:
        result = insert_row("ragnarok_log", {**log_fields})
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to record the reset.")

    return {
        "message": "The old ledger ends here. A new one begins.",
        "previous_balance": previous_balance,
        "new_balance": new_balance,
        "adjustment_amount": adjustment_amount,
        "transaction_id": tx_result.get("transaction_id"),
        "burdens_paid": burdens_paid,
        "burden_errors": burden_errors,
    }

@router.get("/history", summary="Past Ragnarök reset events")
def history(user_id: str = Depends(verify_jwt)):
    logs = select_rows("ragnarok_log", {"user_id": user_id}, sort=[("timestamp", -1)])
    for l in logs:
        if "_id" in l:
            l["_id"] = str(l["_id"])
    return {"events": logs}
