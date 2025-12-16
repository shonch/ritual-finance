from emotional_budget_tracker.utils.mongo_client import insert_row
from emotional_budget_tracker.utils.uuid_generator import generate_uuid
from emotional_budget_tracker.prompts.emotion_tag_prompt import select_emotion_tag
from emotional_budget_tracker.prompts.symbolic_time_prompt import select_symbolic_time
from datetime import datetime, timedelta
from emotional_budget_tracker.rituals.core.setup_utils import (
    format_currency,
    generate_due_dates,
    prompt_principal_and_interest,
    validate_frequency,
    get_emotion_tag
)

def generate_due_dates(start_date, frequency, count=6):
    delta_map = {
        "weekly": timedelta(weeks=1),
        "biweekly": timedelta(weeks=2),
        "monthly": timedelta(days=30),
        "quarterly": timedelta(days=90),
        "annually": timedelta(days=365)
    }
    delta = delta_map.get(frequency.lower(), timedelta(days=30))
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [(start + i * delta).strftime("%Y-%m-%d") for i in range(count)]

def create_setup_item(user_id):
    print("\n🔧 Creating New Setup Item")

    name = input("Name of the item: ").strip()
    category = input("Category (Debt, Subscription, Symbolic, Legacy): ").strip()

    # Payment
    amount_input = input("Total Payment Amount (includes interest if applicable): ").strip()
    amount = float(amount_input) if amount_input else 0.0

    # Recurrence
    print("\n🔁 Define Recurrence")
    print("Is this a one-time ritual or recurring?")
    print("Options: none (one-time), weekly, biweekly, monthly, quarterly, annually")
    recurrence = input("Recurrence: ").strip().lower() or "none"
    is_one_time = recurrence == "none"

    frequency = recurrence if recurrence != "none" else "one-time"

    # Principal and Interest - only if category is debt
    principal, interest_rate = prompt_principal_and_interest(category)

    # Due Date
    due_date = input("First Due Date (YYYY-MM-DD): ").strip()
    future_dates = generate_due_dates(due_date, frequency) if not is_one_time else [due_date]
    print(f"📆 First due date set for {due_date}. Recurs: {frequency}")
    print("📅 Upcoming Due Dates:")
    for date in future_dates:
        print(f"  - {date}")

    # Emotion Tag
    emotion_tag_id = select_emotion_tag(user_id)

    # Archetype
    print("\n🧬 Define Setup Item Archetype")
    archetype = input("Archetype (e.g., The Wanderer, The Guardian): ").strip() or "Unassigned"

    # Symbolic Tag
    symbolic_tag = input("Symbolic Tag (e.g., 'Echo of Oslo', 'Debt to the Past'): ").strip() or "Untitled"

    # Arc Simulation
    arc_enabled = input("Enable payoff arc simulation? (yes/no): ").strip().lower() == "yes"

    # Symbolic Time
    symbolic_time = select_symbolic_time()

    # Start and End Dates
    start_date = input("Start Date (YYYY-MM-DD): ").strip() or "N/A"
    end_date = input("End Date (YYYY-MM-DD, optional): ").strip() or None

    # Component Breakdown
    print("\n🔍 Begin Component Breakdown Ritual")
    components = []
    while True:
        add_component = input("Add a component to this item? (yes/no): ").strip().lower()
        if add_component != "yes":
            break
        label = input("Component Label (e.g., Insurance, Service Fee): ").strip()
        comp_amount = input(f"Amount for {label}: ").strip()
        tag = input("Emotional Tag (e.g., survival, extraction, safety): ").strip()
        component = {
            "label": label,
            "amount": float(comp_amount) if comp_amount else 0.0,
            "tag": tag
        }
        components.append(component)

    print("🧾 Component breakdown complete. Emotional resonance logged.")

    setup_item = {
        "setup_id": generate_uuid(),
        "user_id": user_id,
        "name": name,
        "category": category,
        "amount": amount,
        "frequency": frequency,
        "recurrence": recurrence,
        "is_one_time": is_one_time,
        "principal": principal,
        "interest_rate": interest_rate,
        "includes_interest": True,
        "due_date": due_date,
        "emotion_tag_id": emotion_tag_id,
        "archetype": archetype,
        "symbolic_tag": symbolic_tag,
        "arc_enabled": arc_enabled,
        "symbolic_time": symbolic_time,
        "start_date": start_date,
        "end_date": end_date,
        "active": True,
        "components": components
    }

    result = insert_row("setup_items", setup_item)
    if result.inserted_id:
        print(f"\n🪐 Setup item '{name}' placed in the ritual field.")
    else:
        print("⚠️ Failed to place setup item. Please try again.")
