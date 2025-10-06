from utils.mongo_client import select_rows, update_row
from .setup_utils import format_currency, total_components

def run_setup_module(user_id):

    while True:
        print("\n🛠️ Setup Rituals Menu:")
        print("1. View Active Setup Items")
        print("2. Create New Setup Item")
        print("3. Archive Setup Item")
        print("4. Edit Existing Setup Item")
        print("5. Return to Main Menu")
        choice = input("Choose an option: ")

        if choice == "1":
            # Enhanced view of all setup item metadata
            items = select_rows("setup_items", {
            "user_id": user_id,
            "active": True
            })


            if not items:
                print("\n⚠️ No anchors have been placed in the ritual field.")
                print("🌌 This is pure potential. Begin your setup to shape the myth.\n")
            else:
                print("\n🔍 Active Setup Items:")
                for item in items:



                    # Inside the for item in items loop
                    print(f"• {item['name']} ({item['category']})")
                    print(f"  - Monthly Payment: {format_currency(item.get('amount', 0))}")
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
            setup_id = input("Enter setup_id to archive: ")
            update_row("setup_items", {"setup_id": setup_id}, {"active": False}) 
            print("📦 Setup item archived.")

        elif choice == "4":
            from rituals.core.edit_setup import edit_setup_item
            edit_setup_item(user_id)

        elif choice == "5":
            print("🔙 Returning to main menu...")
            break


        else:
            print("⚠️ Invalid choice. Please select a valid option.")
