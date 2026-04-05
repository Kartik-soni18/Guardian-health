import sys
import os
import uuid
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.supervisor import orchestrate as handle
from app import db, auth
import uvicorn
from mangum import Mangum

app = FastAPI(title="GuardianHealth API", version="3.0.0")
handler = Mangum(app, api_gateway_base_path=None)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:8080").split(",")
if "https://kartik-soni18.github.io" not in allowed_origins:
    allowed_origins.append("https://kartik-soni18.github.io")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TriageRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    conversation_history: Optional[list] = None

class ChatMetadata(BaseModel):
    chat_id: str
    title: str
    last_updated: datetime
    symptoms: List[str] = []
    status: str


@app.post("/register")
async def register(user_data: UserCreate):
    users_coll = await db.get_user_collection()
    if await users_coll.find_one({"username": user_data.username}):
        raise HTTPException(status_code=400, detail="Username already registered.")
    new_user = {
        "username": user_data.username,
        "hashed_password": auth.get_password_hash(user_data.password),
        "created_at": datetime.utcnow(),
    }
    await users_coll.insert_one(new_user)
    access_token = auth.create_access_token(data={"sub": user_data.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user_data.username}


@app.post("/login")
async def login(user_data: UserLogin):
    try:
        users_coll = await db.get_user_collection()
        user = await users_coll.find_one({"username": user_data.username})
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database inaccessible.")
    if not user or not auth.verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    access_token = auth.create_access_token(data={"sub": user_data.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user["username"]}


@app.get("/chats")
async def get_chats(user=Depends(auth.get_current_user_optional)):
    if not user:
        return []
    try:
        chats_coll = await db.get_chats_collection()
        cursor = chats_coll.find({"user_id": user["id"]}).sort("last_updated", -1)
        chats = []
        async for entry in cursor:
            chats.append({
                "chat_id": entry["chat_id"],
                "title": entry.get("title", "New Chat"),
                "last_updated": entry.get("last_updated", datetime.utcnow()),
                "symptoms": entry.get("symptoms", []),
                "status": entry.get("status", "new"),
            })
        return chats
    except Exception:
        return []


@app.get("/chats/{chat_id}")
async def get_chat_history(chat_id: str, user=Depends(auth.get_current_user_optional)):
    try:
        chats_coll = await db.get_chats_collection()
        query = {"chat_id": chat_id, "user_id": user["id"]} if user else {"chat_id": chat_id}
        chat = await chats_coll.find_one(query)
        return chat.get("messages", []) if chat else []
    except Exception:
        return []


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user=Depends(auth.get_current_user_optional)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        chats_coll = await db.get_chats_collection()
        result = await chats_coll.delete_one({"chat_id": chat_id, "user_id": user["id"]})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found.")
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete chat.")


@app.post("/triage")
async def triage(request: TriageRequest, user=Depends(auth.get_current_user_optional)):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chat_id = request.chat_id
    if user and not chat_id:
        chat_id = str(uuid.uuid4())

    result = await handle(
        user_query=request.query,
        user=user,
        chat_id=chat_id,
        conversation_history=request.conversation_history,
    )

    if isinstance(result.get("status"), int) and result["status"] >= 400:
        raise HTTPException(status_code=result["status"], detail=result.get("error"))

    result["chat_id"] = chat_id
    return result


@app.get("/health")
async def health():
    try:
        await db.db.command("ping")
        return {"status": "ok", "db": "mongodb connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


if __name__ == "__main__":
    uvicorn.run("local_server:app", host="0.0.0.0", port=8000, reload=True)
