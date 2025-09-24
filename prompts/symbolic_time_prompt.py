# prompts/symbolic_time_prompt.py

def select_symbolic_time():
    options = {
        "1": "🌅 Morning",
        "2": "🌙 Evening",
        "3": "🌀 Transition",
        "4": "🔥 Urgency",
        "5": "💧 Release"
    }

    print("\n🕰️ Choose Symbolic Time:")
    for key, label in options.items():
        print(f"{key}. {label}")

    choice = input("Enter number: ")
    return options.get(choice, "🌫️ Undefined")
