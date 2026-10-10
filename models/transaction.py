# models/transaction.py

from datetime import datetime, date
import math
from emotional_budget_tracker.prompts.emotion_tag_prompt import select_emotion_tag
from emotional_budget_tracker.prompts.symbolic_time_prompt import select_symbolic_time
from emotional_budget_tracker.utils.uuid_generator import generate_uuid
from emotional_budget_tracker.utils.mongo_client import select_rows, insert_row

# Import Phoenix tag bridge
from backend.modules.symbolic_tag import normalize_tag, create_tag


def log_transaction(user_id, transaction_type):
    print(f"\n🧾 Logging a {transaction_type} transaction")

    amount = float(input("Enter amount: ").strip())
    category = input("Enter category (e.g. rent, groceries, Lyft): ").strip()
    description = input("Enter description (optional): ").strip() or "No description"
    source = input("Enter source (e.g. employer, Lyft, Venmo): ").strip()
    due_date_input = input("Enter due date (optional, YYYY-MM-DD): ").strip()
    due_date = due_date_input if due_date_input else None
    emotional_weight = input("Enter emotional weight (low, medium, high): ").strip().lower()

    # 🧠 Suggest mode based on past transactions
    similar_entries = select_rows("transactions", {
        "user_id": user_id,
        "source": source,
        "category": category
    })
    flow_count = sum(1 for t in similar_entries if t.get("mode") == "flow")
    structured_count = sum(1 for t in similar_entries if t.get("mode") == "structured")

    if flow_count > structured_count:
        suggested_mode = "flow"
    elif structured_count > flow_count:
        suggested_mode = "structured"
    else:
        suggested_mode = None

    if suggested_mode:
        print(f"\n🧭 Based on past entries, this looks like a {suggested_mode} transaction.")
        override = input("Would you like to change it? (y/N): ").strip().lower()
        mode = input("Enter 'flow' or 'structured': ").strip().lower() if override == "y" else suggested_mode
    else:
        mode = input("No clear pattern found. Enter 'flow' or 'structured': ").strip().lower()

    # Normalize tags (CLI version leaves empty, but we can extend later)
    final_tags = []

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": amount,
        "type": transaction_type,
        "category": category,
        "date": str(date.today()),
        "description": description,
        "tags": final_tags,
        "source": source,
        "due_date": due_date,
        "emotional_weight": emotional_weight,
        "reconciliation_id": None,
        "mode": mode
    }

    result = insert_row("transactions", transaction)
    return f"Transaction logged with ID {transaction['transaction_id']}"



# --- NEW FUNCTION — for API use ---

# --- Errors raised to the API layer ----------------------------------------

class TransactionError(Exception):
    """A rejected transaction operation, carrying the HTTP status the API should use."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


EDITABLE_TRANSACTION_FIELDS = ("amount", "date", "category", "description", "source")


def _build_transaction_content(tx):
    """Render the markdown snapshot stored on every transaction.
    Used by both create and edit so the two can never drift apart."""
    tags = tx.get("tags") or []
    lines = [
        f'**Category**: {tx.get("category")}',
        f'**Amount**: {tx.get("amount")}',
        f'**Mode**: {tx.get("mode", "structured")}',
        f'**Tags**: {", ".join(tags) if tags else "none"}',
        f'**Date**: {tx.get("date")}',
        f'**Source**: {tx.get("source")}',
        f'**Due Date**: {tx.get("due_date") or "N/A"}',
        f'**Emotional Weight**: {tx.get("emotional_weight", "medium")}',
        f'**Status**: {tx.get("status")}',
    ]
    body = "  \n".join(lines)
    return (
        "### 💸 Transaction Logged\n\n"
        f"{body}\n\n"
        "---\n\n"
        f'{tx.get("description", "No description")}\n'
    )


# --- NEW FUNCTION — for API use ---
def log_transaction_from_api(user_id, transaction_data):
    # Normalize tags
    raw_tags = transaction_data.get("tags", [])
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags] if raw_tags.strip() else []
    final_tags = [normalize_tag(tag) for tag in raw_tags]

    # Create tags in Phoenix
    for tag in final_tags:
        create_tag({"name": tag, "description": "Auto-inserted from Valhalla transaction"})

    # Determine status: no date, or date <= today -> landed (posted).
    # A future date -> foretold (scheduled), until manually marked landed.
    tx_date_str = transaction_data.get("date")
    if tx_date_str:
        try:
            tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
        except ValueError:
            tx_date = datetime.utcnow().date()
    else:
        tx_date = datetime.utcnow().date()
        tx_date_str = str(tx_date)

    status = "scheduled" if tx_date > datetime.utcnow().date() else "posted"

    transaction = {
        "transaction_id": generate_uuid(),
        "user_id": user_id,
        "amount": transaction_data.get("amount"),
        "type": transaction_data.get("type"),
        "category": transaction_data.get("category"),
        "date": tx_date_str,
        "description": transaction_data.get("description", "No description"),
        "tags": final_tags,
        "source": transaction_data.get("source"),
        "due_date": transaction_data.get("due_date"),
        "emotional_weight": transaction_data.get("emotional_weight", "medium"),
        "reconciliation_id": None,
        "mode": transaction_data.get("mode", "structured"),
        "status": status,
    }
    transaction["content"] = _build_transaction_content(transaction)

    insert_row("transactions", transaction)
    return {
        "message": "Transaction logged",
        "transaction_id": transaction["transaction_id"],
        "content": transaction["content"],
        "status": status,
    }


def edit_scheduled_transaction(user_id, transaction_id, changes):
    """Edit a foretold (scheduled) transaction. Posted transactions are history
    and are locked; a balance that drifted is corrected through a reckoning."""
    from emotional_budget_tracker.utils.mongo_client import update_row

    rows = select_rows("transactions", {"transaction_id": transaction_id, "user_id": user_id})
    if not rows:
        raise TransactionError("Transaction not found.", 404)
    existing = rows[0]

    if existing.get("type") == "adjustment":
        raise TransactionError(
            "Reset adjustments are part of the Ragnarök record and cannot be edited.", 409
        )
    if existing.get("status") != "scheduled":
        raise TransactionError(
            "Only foretold transactions can be edited. A posted transaction is part of "
            "your history — correct a drifted balance through a reckoning instead.", 409
        )

    updates = {}
    for field in EDITABLE_TRANSACTION_FIELDS:
        value = changes.get(field)
        if value is None:
            continue

        if field == "amount":
            try:
                amount = float(value)
            except (TypeError, ValueError):
                raise TransactionError("Amount must be a number.")
            if not math.isfinite(amount) or amount <= 0:
                raise TransactionError("Amount must be greater than zero.")
            updates["amount"] = round(amount, 2)

        elif field == "date":
            try:
                new_date = datetime.strptime(str(value), "%Y-%m-%d").date()
            except ValueError:
                raise TransactionError("Date must be in YYYY-MM-DD form.")
            new_date_str = new_date.isoformat()
            if new_date_str != existing.get("date"):
                if new_date <= datetime.utcnow().date():
                    raise TransactionError(
                        "A foretold transaction can only be moved to a future date. "
                        "If it has already arrived, use Mark as landed instead."
                    )
                updates["date"] = new_date_str

        elif field == "category":
            category = str(value).strip()
            if not category:
                raise TransactionError("Category cannot be empty.")
            updates["category"] = category

        elif field == "source":
            updates["source"] = str(value).strip()

        elif field == "description":
            updates["description"] = str(value).strip() or "No description"

    if not updates:
        raise TransactionError("Nothing to change.")

    merged = {**existing, **updates}
    updates["content"] = _build_transaction_content(merged)

    # The status filter makes the write itself refuse a row that landed in the meantime.
    update_row(
        "transactions",
        {"transaction_id": transaction_id, "user_id": user_id, "status": "scheduled"},
        updates,
    )

    return {
        "message": "Transaction updated",
        "transaction_id": transaction_id,
        "transaction": {
            "transaction_id": transaction_id,
            "type": merged.get("type"),
            "amount": merged.get("amount"),
            "date": merged.get("date"),
            "category": merged.get("category"),
            "description": merged.get("description"),
            "source": merged.get("source"),
            "status": merged.get("status"),
        },
    }


def mark_transaction_posted(user_id, transaction_id, actual_date=None):
    """Flip a foretold (scheduled) transaction to posted (landed).

    A posted transaction is dated the day it actually landed, never a future day:
    last-entry sorts posted rows by date, so a future-dated one would break the
    Ragnarök clock."""
    from emotional_budget_tracker.utils.mongo_client import update_row

    rows = select_rows("transactions", {"transaction_id": transaction_id, "user_id": user_id})
    if not rows:
        raise TransactionError("Transaction not found.", 404)
    existing = rows[0]

    if existing.get("status") != "scheduled":
        raise TransactionError(
            "Only a foretold transaction can be marked as landed. This one is already posted.", 409
        )

    today = datetime.utcnow().date()

    if actual_date:
        try:
            landed_on = datetime.strptime(actual_date, "%Y-%m-%d").date()
        except ValueError:
            raise TransactionError("Actual date must be in YYYY-MM-DD form.")
        if landed_on > today:
            raise TransactionError("A transaction cannot have landed in the future.")
    else:
        # No date given: it lands on its scheduled date, unless that is still
        # in the future, in which case it landed today.
        try:
            scheduled_on = datetime.strptime(existing.get("date"), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            scheduled_on = today
        landed_on = min(scheduled_on, today)

    updates = {"status": "posted", "date": landed_on.isoformat()}
    merged = {**existing, **updates}
    updates["content"] = _build_transaction_content(merged)

    # The status filter makes the write itself refuse a row that already landed.
    update_row(
        "transactions",
        {"transaction_id": transaction_id, "user_id": user_id, "status": "scheduled"},
        updates,
    )

    return {
        "message": "Transaction marked as landed",
        "transaction_id": transaction_id,
        "status": "posted",
        "date": landed_on.isoformat(),
    }

def delete_transaction(user_id, transaction_id):
    """Remove a foretold (scheduled) transaction. Posted transactions are written
    in stone: they are history, and a drifted balance is corrected by a reckoning."""
    from emotional_budget_tracker.utils.mongo_client import delete_row

    rows = select_rows("transactions", {"transaction_id": transaction_id, "user_id": user_id})
    if not rows:
        raise TransactionError("Transaction not found.", 404)
    if rows[0].get("status") != "scheduled":
        raise TransactionError(
            "Only a foretold transaction can be removed. A posted transaction is part of your history.",
            409,
        )

    result = delete_row(
        "transactions",
        {"transaction_id": transaction_id, "user_id": user_id, "status": "scheduled"},
    )
    return {
        "message": "Transaction deleted",
        "transaction_id": transaction_id,
        "deleted": result.deleted_count > 0,
    }
