from utils.supabase_client import get_supabase_client

def run_setup_module(user_id):
    supabase = get_supabase_client()

    while True:
        print("\n🛠️ Setup Rituals Menu:")
        print("1. View Active Setup Items")
        print("2. Create New Setup Item")
        print("3. Archive Setup Item")
        print("4. Return to Main Menu")
        choice = input("Choose an option: ")

        if choice == "1":
            # Enhanced view of all setup item metadata
            items_response = supabase.table("setup_items").select("*").eq("user_id", user_id).eq("active", True).execute()
            items = items_response.data

            if not items:
                print("\n⚠️ No anchors have been placed in the ritual field.")
                print("🌌 This is pure potential. Begin your setup to shape the myth.\n")
            else:
                print("\n🔍 Active Setup Items:")
                for item in items:
                    print(f"• {item['name']} ({item['category']})")
                    print(f"  - Monthly Payment: ${item.get('amount', 'N/A')}")
                    print(f"  - Principal: ${item.get('principal', 'N/A')}")
                    print(f"  - Interest Rate: {round(item.get('interest_rate', 0) * 100, 2)}%")
                    print(f"  - Due Date: {item.get('due_date', 'N/A')}")
                    print(f"  - Emotion Tag: {item.get('emotion_tag_id', 'N/A')}")
                    print(f"  - Archetype: {item.get('archetype', 'N/A')}")
                    print(f"  - Symbolic Tag: {item.get('symbolic_tag', 'N/A')}")
                    print(f"  - Arc Enabled: {'✅' if item.get('arc_enabled') else '❌'}")
                    print(f"  - Setup ID: {item['setup_id']}\n")

        elif choice == "2":
            from rituals.core.create_setup import create_setup_item
            create_setup_item(user_id)

        elif choice == "3":
            setup_id = input("Enter setup_id to archive: ")
            supabase.table("setup_items").update({"active": False}).eq("setup_id", setup_id).execute()
            print("📦 Setup item archived.")

        elif choice == "4":
            print("🔙 Returning to main menu...")
            break

        else:
            print("⚠️ Invalid choice. Please select a valid option.")
