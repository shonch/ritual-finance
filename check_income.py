# check_income.py — temporary debug script, safe to delete after use
from datetime import date
from emotional_budget_tracker.utils.mongo_client import select_rows

transactions = select_rows("transactions", {"type": "income"})
transactions.sort(key=lambda t: t.get("date", ""), reverse=True)

today = date.today()
today_str = str(today)

total_all = 0
total_landed = 0

print(f"\n{'Date':<12} {'Amount':>10} {'Status':<12} {'Category':<20} {'Source'}")
print("-" * 80)
for t in transactions:
    amt = t.get("amount", 0)
    status = t.get("status", "(none — treated as posted)")
    is_landed = t.get("status", "posted") == "posted"

    total_all += amt
    if is_landed:
        total_landed += amt

    flag = "  <-- LANDED" if is_landed else "  <-- foretold (future)"
    print(f"{t.get('date', '?'):<12} {amt:>10.2f} {status:<12} {t.get('category', ''):<20} {t.get('source', '')}{flag}")

print("-" * 80)
print(f"Total income transactions: {len(transactions)}")
print(f"Total of ALL income (landed + foretold): ${total_all:.2f}")
print(f"Total of LANDED income only: ${total_landed:.2f}")
