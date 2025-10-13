from fastapi import FastAPI, Request
from models.user import add_user, user_exists, get_user
from models.transaction import log_transaction_from_api
from fastapi import Header, HTTPException, Depends, Query
from bson import ObjectId
import os
app = FastAPI()

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/transaction", dependencies=[Depends(verify_api_key)])
async def create_transaction(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    transaction_data = data.get("transaction", {})
    return log_transaction_from_api(user_id, transaction_data)

@app.post("/user/init", dependencies=[Depends(verify_api_key)])
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

from bson import ObjectId

@app.get("/transaction/view", dependencies=[Depends(verify_api_key)])
def view_transactions(user_id: str = Query(...), category: str = Query(None), mode: str = Query(None)):
    from utils.mongo_client import select_rows

    query = {"user_id": user_id}
    if category:
        query["category"] = {"$regex": f"^{category.strip()}$", "$options": "i"}
    if mode:
        query["mode"] = {"$regex": f"^{mode.strip()}$", "$options": "i"}

    transactions = select_rows("transactions", query)

    for t in transactions:
        if "_id" in t and isinstance(t["_id"], ObjectId):
            t["_id"] = str(t["_id"])

    return {"transactions": transactions or []}
