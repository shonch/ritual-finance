from emotional_budget_tracker.utils.mongo_client import select_rows, update_row
from .setup_utils import format_currency, total_components

def monthly_equivalent(amount, frequency):
    if frequency == "weekly":
        return amount * 52 / 12
    elif frequency == "biweekly":
        return amount * 26 / 12
    elif frequency == "quarterly":
        return amount / 3
    elif frequency == "annually":
        return amount / 12
    return amount  # default monthly

def run_setup_module(user_id):
    while True:
        print("\n🛠️ Setup Rituals Menu:")
        print("1. View Active Setup Items")
        print("2. Create New Setup Item")
        print("3. Archive Setup Item")
        print("4. Edit Existing Setup Item")
        print("5. Return to Main Menu")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            items = select_rows("setup_items", {"user_id": user_id, "active": True})
            if not items:
                print("\n⚠️ No anchors have been placed in the ritual field.")
                print("🌌 This is pure potential. Begin your setup to shape the myth.\n")
            else:
                print("\n🔍 Active Setup Items:")
                for item in items:
                    print(f"• {item['name']} ({item['category']})")
                    print(f"  - Payment: {format_currency(item.get('amount', 0))} ({item.get('frequency', 'monthly')})")
                    monthly_estimate = monthly_equivalent(item.get('amount', 0), item.get('frequency', 'monthly'))
                    print(f"  - Estimated Monthly Cost: {format_currency(monthly_estimate)}")
                    print(f"  - Principal: {format_currency(item.get('principal', 0))}")
                    print(f"  - Interest Rate: {round(item.get('interest_rate', 0) * 100, 2)}%")
                    monthly_interest = item.get('principal', 0) * item.get('interest_rate', 0) / 12
                    print(f"  - Monthly Interest: {format_currency(monthly_interest)}")
                    print(f"  - Due Date: {item.get('due_date', 'N/A')}")
                    print(f"  - Emotion Tag: {item.get('emotion_tag_id', 'N/A')}")
                    print(f"  - Archetype: {item.get('archetype', 'N/A')}")
                    print(f"  - Symbolic Tag: {item.get('symbolic_tag', 'N/A')}")
                    print(f"  - Arc Enabled: {'✅' if item.get('arc_enabled') else '❌'}")
                    print(f"  - Setup ID: {item['setup_id']}")

                    if item.get("components"):
                        print("  - Component Breakdown:")
                        for comp in item["components"]:
                            print(f"    • {comp['label']}: {format_currency(comp['amount'])} ({comp['tag']})")
                        print(f"  - Total Component Cost: {format_currency(total_components(item['components']))}")
                    else:
                        print("  - No components added yet. This setup is pure potential.")

        elif choice == "2":
            from rituals.core.create_setup import create_setup_item
            create_setup_item(user_id)

        elif choice == "3":
            setup_id = input("Enter setup_id to archive: ").strip()
            if not setup_id or len(setup_id) < 10 or " " in setup_id:
                print("⚠️ Invalid setup_id. Please enter a valid UUID.")
                continue
            result = update_row("setup_items", {"setup_id": setup_id, "user_id": user_id}, {"active": False})
            if result.modified_count == 1:
                print(f"📦 Setup item '{setup_id}' archived successfully.")
            else:
                print("⚠️ Archive failed — setup item not found or already inactive.")

        elif choice == "4":
            from rituals.core.edit_setup import edit_setup_item
            edit_setup_item(user_id)

        elif choice == "5":
            print("🔙 Returning to main menu...")
            break

        else:
            print("⚠️ Invalid choice. Please select a valid option.")
