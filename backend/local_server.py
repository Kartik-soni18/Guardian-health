import sys
import os
import time
import uuid
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app.core.config import settings
from app.core.events import lifespan
from app.api.router import api_router
from app.services.auth_service import (
    get_current_user_optional,
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.services.chat_service import ChatService
from app.services.triage_service import TriageService
from app import db

app = FastAPI(
    title="GuardianHealth API",
    version="3.2.0",
    lifespan=lifespan,
)
_mangum_handler = Mangum(app, api_gateway_base_path=None)


def handler(event, context):
    """Lambda entry point."""
    return _mangum_handler(event, context)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID Middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start = time.time()

    response = await call_next(request)

    latency = (time.time() - start) * 1000
    response.headers["X-Request-ID"] = request_id

    # Attach structured log extras for JSON formatter
    import logging
    logger = logging.getLogger("guardianhealth")
    extra = {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "latency_ms": round(latency, 2),
    }
    logger.info("%s %s %d %.2fms", request.method, request.url.path, response.status_code, latency, extra=extra)
    return response


# ── V1 API Router ─────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Legacy Routes (Backward Compatibility) ────────────────────────────────────
# These mirror the pre-refactor endpoints so the existing frontend continues
# to work without changes.

from app.models.user import UserCreate, UserLogin
from app.models.triage import TriageRequest


@app.post("/register")
async def legacy_register(user_data: UserCreate):
    users_coll = await db.get_user_collection()
    if await users_coll.find_one({"username": user_data.username}):
        raise HTTPException(status_code=400, detail="Registration failed. Please try a different username.")
    new_user = {
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": __import__("datetime").datetime.utcnow(),
    }
    await users_coll.insert_one(new_user)
    access_token = create_access_token(data={"sub": user_data.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user_data.username}


@app.post("/login")
async def legacy_login(user_data: UserLogin):
    try:
        users_coll = await db.get_user_collection()
        user = await users_coll.find_one({"username": user_data.username})
    except Exception:
        raise HTTPException(status_code=503, detail="Database inaccessible.")
    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer", "username": user["username"]}


@app.get("/chats")
async def legacy_get_chats(user=Depends(get_current_user_optional)):
    if not user:
        return []
    return await ChatService.list_chats(user["id"])


@app.get("/chats/{chat_id}")
async def legacy_get_chat_history(chat_id: str, user=Depends(get_current_user_optional)):
    user_id = user["id"] if user else None
    return await ChatService.get_chat_history(chat_id, user_id)


@app.delete("/chats/{chat_id}")
async def legacy_delete_chat(chat_id: str, user=Depends(get_current_user_optional)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    deleted = await ChatService.delete_chat(chat_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"status": "deleted"}


@app.post("/triage")
async def legacy_triage(request: TriageRequest, user=Depends(get_current_user_optional)):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chat_id = request.chat_id
    if user and not chat_id:
        chat_id = str(uuid.uuid4())

    result = await TriageService.invoke_graph(
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
async def legacy_health():
    try:
        await db.db.command("ping")
        return {"status": "ok", "db": "mongodb connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("local_server:app", host="0.0.0.0", port=8000, reload=True)
