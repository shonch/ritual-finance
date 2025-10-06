from utils.mongo_client import update_row
from utils.mongo_client import select_rows

def edit_setup_item(user_id):
    setup_id = input("Enter setup_id to edit: ").strip()
    item = select_rows("setup_items", {"setup_id": setup_id, "user_id": user_id})
    
    if not item:
        print("⚠️ No setup item found with that ID.")
        return

    item = item[0]  # get the first match

    print(f"\n🛠️ Editing '{item['name']}'")
    new_name = input(f"Name [{item['name']}]: ").strip() or item['name']
    new_amount = input(f"Monthly Payment [{item['amount']}]: ").strip()
    new_amount = float(new_amount) if new_amount else item['amount']

    update_row("setup_items", {"setup_id": setup_id}, {
        "name": new_name,
        "amount": new_amount
    })

    print("✅ Setup item updated.")
