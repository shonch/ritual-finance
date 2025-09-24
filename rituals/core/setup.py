from dotenv import load_dotenv
load_dotenv()

from utils.uuid_generator import generate_uuid
from utils.supabase_client import get_supabase_client
from models.balance import insert_balance_snapshot
from utils.emotion_tags import get_or_create_emotion_tag

def run_setup_module(user_id):
    supabase = get_supabase_client()

    while True:
        print("\n🛠️ Setup Rituals Menu:")
        print("1. View Active Setup Items")
        print("2. Create New Setup Item")
        print("3. Convert Setup to Bill")
        print("4. Convert Setup to Goal")
        print("5. Convert Setup to Debt")
        print("6. Archive Setup Item")
        print("7. Return to Main Menu")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            response = supabase.table("setup_items").select(
                "label, type, amount, due_date, emotion_tag_id, archetype"
            ).eq("user_id", user_id).eq("active", True).execute()

            rows = response.data
            print("\n🔍 Active Setup Items:")

            if not rows:
                print("⚠️ No anchors have been placed in the ritual field.")
                print("🕯️ You are standing at the threshold — no bills, no goals, no debts.")
                print("🌌 This is pure potential. Begin your setup to shape the myth.")
            else:
                for row in rows:
                    print(f"• {row['label']} ({row['type']}) — ${row['amount']} due {row['due_date']}")

        elif choice == "2":
            label = input("📝 Name this item — literal or symbolic (e.g. 'Rent', 'Debt to Past Self', 'Oslo Threshold'): ")

            print("\n📂 Classify this item:")
            print("• bill — a recurring obligation")
            print("• goal — a future aspiration")
            print("• symbolic — an emotional or mythic anchor")
            print("• debt — a burden already carried or soon to be incurred")

            type_ = input("Your choice: ").strip().lower()
            valid_types = ["bill", "goal", "symbolic", "debt"]
            while type_ not in valid_types:
                print("⚠️ Please choose one of: bill, goal, symbolic, debt.")
                type_ = input("Your choice: ").strip().lower()

            amount = input("Amount (or leave blank): ")
            due_date = input("Due date (YYYY-MM-DD or blank): ")

            emotion_tag = input("Emotion Tag (or leave blank): ")
            emotion_tag_id = get_or_create_emotion_tag(emotion_tag)

            setup_id = generate_uuid()
            supabase.table("setup_items").insert({
                "setup_id": setup_id,
                "user_id": user_id,
                "label": label,
                "type": type_,
                "amount": amount,
                "due_date": due_date,
                "emotion_tag_id": emotion_tag_id,
                "active": True
            }).execute()

            print(f"✅ Setup item '{label}' created as a {type_}.")
        elif choice == "3":
            setup_id = input("Enter setup_id to convert to bill: ")
            supabase.table("setup_items").update({"type": "bill"}).eq("setup_id", setup_id).execute()
            print("💸 Setup item converted to bill.")

        elif choice == "4":
            setup_id = input("Enter setup_id to convert to goal: ")
            response = supabase.table("setup_items").select(
                "user_id, label, amount, due_date, emotion_tag_id"
            ).eq("setup_id", setup_id).single().execute()
            item = response.data

            supabase.table("goals").insert({
                "goal_id": generate_uuid(),
                "user_id": item["user_id"],
                "label": item["label"],
                "target_amount": item["amount"],
                "due_date": item["due_date"],
                "emotional_tag": item["emotion_tag_id"],
                "priority": "medium",
                "status": "active",
                "setup_id": setup_id
            }).execute()
            print("🎯 Setup item converted to goal.")

        elif choice == "5":
            print("\n🧱 Converting Setup to Debt — name the burden, honor the threshold.")

            response = supabase.table("setup_items").select(
                "id, label, type"
            ).eq("user_id", user_id).eq("active", True).execute()
            rows = response.data

            if not rows:
                print("⚠️ No setup items available to convert.")
            else:
                for i, row in enumerate(rows):
                    print(f"{i + 1}. {row['label']} ({row['type']})")

                selection = input("Choose an item to convert to debt (enter number): ").strip()
                try:
                    index = int(selection) - 1
                    selected_item = rows[index]

                    supabase.table("setup_items").update({"type": "debt"}).eq("id", selected_item["id"]).execute()
                    print(f"✅ '{selected_item['label']}' has been converted to a debt ritual.")
                except (ValueError, IndexError):
                    print("⚠️ Invalid selection. No conversion performed.")

        elif choice == "6":
            setup_id = input("Enter setup_id to archive: ")
            supabase.table("setup_items").update({
                "active": False,
                "last_updated": "now()"
            }).eq("setup_id", setup_id).execute()
            print("📦 Setup item archived.")

        elif choice == "7":
            print("🔙 Returning to Main Menu...")
            break

        else:
            print("⚠️ Invalid choice. Please select a valid option.")
