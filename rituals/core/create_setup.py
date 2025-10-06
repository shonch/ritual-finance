from utils.mongo_client import insert_row
from utils.uuid_generator import generate_uuid
from prompts.emotion_tag_prompt import select_emotion_tag
from prompts.symbolic_time_prompt import select_symbolic_time

def create_setup_item(user_id):
    print("\n🔧 Creating New Setup Item")

    name = input("Name of the item: ").strip()
    category = input("Category (Debt, Subscription, Symbolic, Legacy): ").strip()
    monthly_payment = float(input("Monthly Payment: ").strip())
    principal = float(input("Principal Amount: ").strip())
    interest_rate = float(input("Interest Rate (%): ").strip()) / 100
    due_date = input("Due Date (YYYY-MM-DD): ").strip()
    emotion_tag_id = select_emotion_tag(user_id)
    archetype = input("Archetype (e.g., The Wanderer, The Guardian): ").strip()
    symbolic_tag = input("Symbolic Tag (e.g., 'Echo of Oslo', 'Debt to the Past'): ").strip()
    arc_enabled = input("Enable payoff arc simulation? (yes/no): ").strip().lower() == "yes"
    symbolic_time = select_symbolic_time()
    
    print("\n🔍 Begin Component Breakdown Ritual")
    components = []
    while True:
        add_component = input("Add a component to this debt? (yes/no): ").strip().lower()
        if add_component != "yes":
            break

        label = input("Component Label (e.g., Insurance, Service Fee): ").strip()
        amount = float(input(f"Amount for {label}: ").strip())
        tag = input("Emotional Tag (e.g., survival, extraction, safety): ").strip()

        component = {
            "label": label,
            "amount": amount,
            "tag": tag
        }
        components.append(component)

    print("🧾 Component breakdown complete. Emotional resonance logged.")
    setup_item = {
        "setup_id": generate_uuid(),
        "user_id": user_id,
        "name": name,
        "category": category,
        "amount": monthly_payment,
        "principal": principal,
        "interest_rate": interest_rate,
        "due_date": due_date,
        "emotion_tag_id": emotion_tag_id,
        "archetype": archetype,
        "symbolic_tag": symbolic_tag,
        "arc_enabled": arc_enabled,
        "symbolic_time": symbolic_time,
        "active": True,
        "components": components,
    }

    result = insert_row("setup_items", setup_item)
    if result.inserted_id:
        print(f"\n🪐 Setup item '{name}' placed in the ritual field.")
    else:
        print("⚠️ Failed to place setup item. Please try again.")
