"""MongoDB connection and user/chat persistence."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("app.db.mongodb")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def _normalize_created_at(value: Any) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _normalize_chat_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = _normalize_created_at(doc.get("created_at"))
    doc["updated_at"] = _normalize_created_at(doc.get("updated_at"))
    return doc


def _normalize_message_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["id"] = str(doc.pop("_id"))
    doc["created_at"] = _normalize_created_at(doc.get("created_at"))
    return doc


def _normalize_user_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc.pop("_id", None)
    username = doc["username"]
    doc["id"] = username
    doc["created_at"] = _normalize_created_at(doc.get("created_at"))
    doc.setdefault("is_active", True)
    doc.setdefault("is_verified", False)
    doc.setdefault("role", "patient")
    doc.setdefault("auth_provider", "local")
    hashed = doc.get("hashed_password", doc.get("password_hash", ""))
    doc["hashed_password"] = hashed
    doc["password_hash"] = hashed
    return doc


async def connect_mongodb() -> None:
    global _client, _db
    if _db is not None:
        return
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_db_name]
    await _db.command("ping")
    try:
        await _db.users.create_index("username", unique=True)
        await _db.users.create_index("google_id", unique=True, sparse=True)
        await _db.users.create_index("email", unique=True, sparse=True)
    except Exception as exc:
        logger.warning("Could not ensure user indexes: %s", exc)
    try:
        await _db.users.drop_index("email_1")
        logger.info("Dropped legacy email index from users collection")
    except Exception:
        pass
    try:
        await _db.chats.create_index([("user_id", 1), ("updated_at", -1)])
        await _db.chats.create_index([("_id", 1), ("user_id", 1)])
        await _db.messages.create_index([("chat_id", 1), ("created_at", 1)])
    except Exception as exc:
        logger.warning("Could not ensure chat/message indexes: %s", exc)
    logger.info("Connected to MongoDB database=%s", settings.mongodb_db_name)


async def ensure_mongodb() -> None:
    """Connect on startup or lazily on first request (Lambda-friendly)."""
    if _db is None:
        await connect_mongodb()


async def close_mongodb() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("MongoDB is not connected. Call ensure_mongodb() first.")
    return _db


async def ping_mongodb() -> bool:
    try:
        await ensure_mongodb()
        await _db.command("ping")
        return True
    except Exception as exc:
        logger.warning("MongoDB ping failed: %s", exc)
        return False


class MongoDBManager:
    """Async MongoDB manager for user and chat CRUD."""

    def __init__(
        self,
        db: Optional[AsyncIOMotorDatabase] = None,
        sync_db: Any = None,
    ) -> None:
        self._db = db
        self._sync_db = sync_db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is not None:
            return self._db
        return get_database()

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        if self._sync_db is not None:
            doc = await asyncio.to_thread(
                self._sync_db.users.find_one, {"username": username}
            )
        else:
            doc = await self.db.users.find_one({"username": username})
        if doc is None:
            return None
        return _normalize_user_doc(doc)

    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        if self._sync_db is not None:
            doc = await asyncio.to_thread(
                self._sync_db.users.find_one, {"google_id": google_id}
            )
        else:
            doc = await self.db.users.find_one({"google_id": google_id})
        if doc is None:
            return None
        return _normalize_user_doc(doc)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        normalized = email.strip().lower()
        if self._sync_db is not None:
            doc = await asyncio.to_thread(
                self._sync_db.users.find_one, {"email": normalized}
            )
        else:
            doc = await self.db.users.find_one({"email": normalized})
        if doc is None:
            return None
        return _normalize_user_doc(doc)

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        username = user_data["username"]
        now = datetime.now(timezone.utc)
        doc = {
            "username": username,
            "hashed_password": user_data.get(
                "password_hash", user_data.get("hashed_password", "")
            ),
            "created_at": now,
        }
        for key in (
            "google_id",
            "email",
            "auth_provider",
            "is_verified",
            "is_active",
            "role",
        ):
            if key in user_data:
                doc[key] = user_data[key]
        if self._sync_db is not None:
            await asyncio.to_thread(self._sync_db.users.insert_one, doc)
        else:
            await self.db.users.insert_one(doc)
        return _normalize_user_doc(doc)

    async def create_oauth_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            **user_data,
            "password_hash": "",
            "auth_provider": user_data.get("auth_provider", "google"),
            "is_verified": user_data.get("is_verified", True),
        }
        if "email" in payload and payload["email"]:
            payload["email"] = payload["email"].strip().lower()
        return await self.create_user(payload)

    async def link_google_account(
        self,
        username: str,
        google_id: str,
        email: str,
    ) -> Optional[Dict[str, Any]]:
        normalized_email = email.strip().lower()
        update: Dict[str, Any] = {"google_id": google_id, "email": normalized_email}
        query = {"username": username}
        if self._sync_db is not None:
            result = await asyncio.to_thread(
                self._sync_db.users.update_one,
                query,
                {"$set": update},
            )
            if result.matched_count == 0:
                return None
            doc = await asyncio.to_thread(self._sync_db.users.find_one, query)
        else:
            result = await self.db.users.update_one(query, {"$set": update})
            if result.matched_count == 0:
                return None
            doc = await self.db.users.find_one(query)
        if doc is None:
            return None
        return _normalize_user_doc(doc)

    async def create_chat(self, user_id: str, title: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        chat_id = str(uuid.uuid4())
        doc = {
            "_id": chat_id,
            "user_id": user_id,
            "title": title,
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        if self._sync_db is not None:
            await asyncio.to_thread(self._sync_db.chats.insert_one, doc)
        else:
            await self.db.chats.insert_one(doc)
        return _normalize_chat_doc(doc)

    async def list_chats(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = {"user_id": user_id}
        if self._sync_db is not None:
            cursor = self._sync_db.chats.find(query).sort("updated_at", -1).limit(limit)
            docs = await asyncio.to_thread(list, cursor)
        else:
            cursor = self.db.chats.find(query).sort("updated_at", -1).limit(limit)
            docs = await cursor.to_list(length=limit)
        return [_normalize_chat_doc(doc) for doc in docs]

    async def get_chat(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        query = {"_id": chat_id, "user_id": user_id}
        if self._sync_db is not None:
            doc = await asyncio.to_thread(self._sync_db.chats.find_one, query)
        else:
            doc = await self.db.chats.find_one(query)
        if doc is None:
            return None
        return _normalize_chat_doc(doc)

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        query = {"_id": chat_id, "user_id": user_id}
        if self._sync_db is not None:
            result = await asyncio.to_thread(self._sync_db.chats.delete_one, query)
            if result.deleted_count:
                await asyncio.to_thread(
                    self._sync_db.messages.delete_many, {"chat_id": chat_id}
                )
                return True
            return False
        result = await self.db.chats.delete_one(query)
        if result.deleted_count:
            await self.db.messages.delete_many({"chat_id": chat_id})
            return True
        return False

    async def list_messages(
        self,
        chat_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        chat = await self.get_chat(chat_id, user_id)
        if chat is None:
            return []
        query = {"chat_id": chat_id}
        if self._sync_db is not None:
            cursor = (
                self._sync_db.messages.find(query).sort("created_at", 1).limit(limit)
            )
            docs = await asyncio.to_thread(list, cursor)
        else:
            cursor = self.db.messages.find(query).sort("created_at", 1).limit(limit)
            docs = await cursor.to_list(length=limit)
        return [_normalize_message_doc(doc) for doc in docs]

    async def append_messages(
        self,
        chat_id: str,
        user_id: str,
        messages: List[Dict[str, Any]],
    ) -> None:
        if not messages:
            return
        chat = await self.get_chat(chat_id, user_id)
        if chat is None:
            raise ValueError("Chat not found or access denied")

        now = datetime.now(timezone.utc)
        docs = []
        for msg in messages:
            docs.append({
                "_id": msg.get("id") or str(uuid.uuid4()),
                "chat_id": chat_id,
                "user_id": user_id,
                "role": msg["role"],
                "content": msg["content"],
                "triage": msg.get("triage"),
                "created_at": msg.get("created_at") or now,
            })

        if self._sync_db is not None:
            await asyncio.to_thread(self._sync_db.messages.insert_many, docs)
            await asyncio.to_thread(
                self._sync_db.chats.update_one,
                {"_id": chat_id, "user_id": user_id},
                {"$set": {"updated_at": now}},
            )
        else:
            await self.db.messages.insert_many(docs)
            await self.db.chats.update_one(
                {"_id": chat_id, "user_id": user_id},
                {"$set": {"updated_at": now}},
            )

    async def update_chat_title(self, chat_id: str, user_id: str, title: str) -> None:
        if self._sync_db is not None:
            await asyncio.to_thread(
                self._sync_db.chats.update_one,
                {"_id": chat_id, "user_id": user_id},
                {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
            )
        else:
            await self.db.chats.update_one(
                {"_id": chat_id, "user_id": user_id},
                {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
            )
