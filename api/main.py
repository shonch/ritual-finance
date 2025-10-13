from fastapi import FastAPI, Request
from models.user import add_user, user_exists, get_user
from models.transaction import log_transaction_from_api

app = FastAPI()

@app.post("/user/init")
async def init_user(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)

        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        note = data.get("note", "Initiated via API")

        print("Checking if user exists...")
        if not user_exists(user_id):
            print("User does not exist. Adding user...")
            add_user(user_id, name, email, note)

        print("Fetching user...")
        return get_user(user_id)

    except Exception as e:
        print("Error in /user/init:", e)
        return {"error": str(e)}

@app.post("/transaction")
async def create_transaction(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    transaction_data = data.get("transaction", {})
    return log_transaction_from_api(user_id, transaction_data)
