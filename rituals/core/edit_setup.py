from utils.mongo_client import update_row, select_rows
from utils.uuid_generator import generate_uuid
from rituals.core.setup_utils import (
    format_currency,
    generate_due_dates,
    prompt_principal_and_interest,
    validate_frequency,
    get_emotion_tag
)

def edit_setup_item(user_id):
    setup_id = input("Enter setup_id to edit: ").strip()
    item = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id})

    if not item:
        print("⚠️ No setup item found with that ID.")
        return

    item = item[0]  # get the first match

    category = item.get("category", "").lower()
    print(f"\n🛠️ Editing '{item['name']}'")

    # Basic fields
    new_name = input(f"Name [{item['name']}]: ").strip() or item["name"]
    new_amount = input(f"Payment Amount [{item['amount']}]: ").strip()
    new_amount = float(new_amount) if new_amount else item["amount"]

    new_frequency = input(
        f"Payment Frequency [{item.get('frequency', 'monthly')}]: "
    ).strip().lower() or item.get("frequency", "monthly")


    principal, interest_rate = prompt_principal_and_interest(category)


    new_due_date = input(f"Due Date [{item['due_date']}]: ").strip() or item["due_date"]
    new_archetype = (
        input(f"Archetype [{item['archetype']}]: ").strip() or item["archetype"]
    )
    new_symbolic_tag = get_emotion_tag()
    
   
  

    # Recurrence Update
    new_recurrence = input(
        f"Recurrence [{item.get('recurrence', 'none')}]: "
    ).strip().lower() or item.get("recurrence", "none")
    new_start_date = input(
        f"Start Date [{item.get('start_date', 'N/A')}]: "
    ).strip() or item.get("start_date", "N/A")
    new_end_date = input(
        f"End Date [{item.get('end_date', 'None')}]: "
    ).strip() or item.get("end_date", None)

    # Component mutation
    print("\n🔍 Begin Component Mutation Ritual")
    components = item.get("components", [])
    while True:
        mutate = input("Add a new component? (yes/no): ").strip().lower()
        if mutate != "yes":
            break
        label = input("Component Label: ").strip()
        amount = float(input(f"Amount for {label}: ").strip())
        tag = input("Emotional Tag: ").strip()
        components.append({"label": label, "amount": amount, "tag": tag})

    # Optional emotional commentary
    print("\n📝 Attach emotional commentary (type 'END' on a new line to finish):")


lines = []
while True:
    line = input()
    if line.strip().upper() == "END":
        break
    lines.append(line)
note = "\n".join(lines)
if note:
    item["note"] = note

    # Final update
    update_row(
        "setup_items",
        {"setup_id": setup_id},
        {
            "name": new_name,
            "amount": new_amount,
            "principal": new_principal,
            "interest_rate": new_interest_rate,
            "due_date": new_due_date,
            "archetype": new_archetype,
            "symbolic_tag": new_symbolic_tag,
            "recurrence": new_recurrence,
            "start_date": new_start_date,
            "end_date": new_end_date,
            "components": components,
            "note": item.get("note", ""),
            "frequency": new_frequency,
        },
    )

    print("✅ Setup item updated with full emotional and symbolic clarity.")
