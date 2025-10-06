# 🧰 core/setup_utils.py — Shared Ritual Tools

def format_currency(amount):
    """Formats a float as currency string."""
    return f"${amount:,.2f}"

def total_components(components):
    """Returns the total amount from all components."""
    return sum(comp.get("amount", 0) for comp in components)
