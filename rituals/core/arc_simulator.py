# rituals/core/arc_simulator.py

from utils.supabase_client import get_supabase_client
from datetime import datetime, timedelta
import math

def simulate_payoff_arc(setup_id):
    supabase = get_supabase_client()

    response = supabase.table("setup_items").select(
        "label, principal, interest_rate, amount, symbolic_tag, emotion_tag_id"
    ).eq("setup_id", setup_id).single().execute()

    item = response.data
    if not item or not item.get("principal") or not item.get("interest_rate"):
        print("⚠️ Arc simulation unavailable — missing principal or interest rate.")
        return

    principal = float(item["principal"])
    interest_rate = float(item["interest_rate"]) / 100 / 12  # monthly rate
    monthly_payment = float(item["amount"])

    months = 0
    balance = principal
    total_interest = 0

    while balance > 0:
        interest = balance * interest_rate
        principal_payment = monthly_payment - interest
        if principal_payment <= 0:
            print("⚠️ Monthly payment too low to reduce principal.")
            return
        balance -= principal_payment
        total_interest += interest
        months += 1

    payoff_date = datetime.today() + timedelta(days=months * 30)

    print(f"\n🎯 Payoff Arc Simulation for '{item['label']}':")
    print(f"• Months to payoff: {months}")
    print(f"• Total interest paid: ${total_interest:.2f}")
    print(f"• Estimated payoff date: {payoff_date.date()}")
    print(f"• Symbolic Tag: {item.get('symbolic_tag', '—')}")
    print(f"• Emotion Tag ID: {item.get('emotion_tag_id', '—')}")
