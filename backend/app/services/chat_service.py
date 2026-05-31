"""Chat service layer — encapsulates MongoDB chat CRUD operations."""

from datetime import datetime
from typing import List, Optional

from app import db


class ChatService:
    @staticmethod
    async def list_chats(user_id: str) -> List[dict]:
        """Return all chats for a user, sorted by last_updated descending."""
        chats_coll = await db.get_chats_collection()
        cursor = chats_coll.find({"user_id": user_id}).sort("last_updated", -1)
        chats = []
        async for entry in cursor:
            last_updated = entry.get("last_updated", datetime.utcnow())
            created_at = entry.get("created_at", last_updated)
            symptoms = entry.get("symptoms", [])
            chats.append({
                "chat_id": entry["chat_id"],
                "id": entry["chat_id"],
                "title": entry.get("title", "New Chat"),
                "last_updated": last_updated,
                "updated_at": last_updated,
                "created_at": created_at,
                "symptoms": symptoms,
                "symptom_tags": symptoms,
                "status": entry.get("status", "new"),
            })
        return chats

    @staticmethod
    async def get_chat_history(chat_id: str, user_id: str | None = None) -> List[dict]:
        """Return message history for a chat."""
        chats_coll = await db.get_chats_collection()
        query = {"chat_id": chat_id}
        if user_id:
            query["user_id"] = user_id
        chat = await chats_coll.find_one(query)
        return chat.get("messages", []) if chat else []

    @staticmethod
    async def delete_chat(chat_id: str, user_id: str) -> bool:
        """Delete a chat belonging to a user. Returns True if deleted."""
        chats_coll = await db.get_chats_collection()
        result = await chats_coll.delete_one({"chat_id": chat_id, "user_id": user_id})
        return result.deleted_count > 0
