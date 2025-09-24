import requests
import random

ZEN_QUOTES_API = "https://zenquotes.io/api/random"

def fetch_quote():
    try:
        response = requests.get(ZEN_QUOTES_API)
        if response.status_code == 200:
            data = response.json()
            quote = data[0]["q"]
            author = data[0]["a"]
            return f'"{quote}" — {author}'
        else:
            return "Could not fetch quote. API may be down."
    except Exception as e:
        return f"Error fetching quote: {e}"

def fetch_curated_quote():
    curated_quotes = [
        {"text": "The wound is the place where the Light enters you.", "author": "Rumi", "tag": "rebirth"},
        {"text": "You do not rise to the level of your goals. You fall to the level of your systems.", "author": "James Clear", "tag": "ritual"},
        {"text": "The opposite of addiction is connection.", "author": "Johann Hari", "tag": "sovereignty"},
    ]
    q = random.choice(curated_quotes)
    return f'"{q["text"]}" — {q["author"]} [{q["tag"]}]'
