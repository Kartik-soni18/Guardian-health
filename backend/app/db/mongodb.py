"""MongoDB connection and user persistence."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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


def _normalize_user_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc.pop("_id", None)
    username = doc["username"]
    doc["id"] = username
    doc["created_at"] = _normalize_created_at(doc.get("created_at"))
    doc.setdefault("is_active", True)
    doc.setdefault("is_verified", False)
    doc.setdefault("role", "patient")
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
    except Exception as exc:
        logger.warning("Could not ensure username index: %s", exc)
    try:
        await _db.users.drop_index("email_1")
        logger.info("Dropped legacy email index from users collection")
    except Exception:
        pass
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
    """Async MongoDB manager for user CRUD."""

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
        if self._sync_db is not None:
            await asyncio.to_thread(self._sync_db.users.insert_one, doc)
        else:
            await self.db.users.insert_one(doc)
        return _normalize_user_doc(doc)
