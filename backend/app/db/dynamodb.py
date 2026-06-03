"""High-level DynamoDB manager for GuardianHealth services.

Wraps the low-level async DynamoDB client with domain-specific operations
for users, chats, and interactions.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.dynamodb import (
    can_ping_dynamodb,
    ddb_delete_item,
    ddb_get_item,
    ddb_put_item,
    ddb_query,
)
from app.logging_config import get_logger

logger = get_logger("app.db.dynamodb")


class DynamoDBManager:
    """Async DynamoDB manager for user, chat, and interaction CRUD."""

    def __init__(self) -> None:
        self.settings = get_settings()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by primary key (username)."""
        item = await ddb_get_item(
            self.settings.table_users, key={"username": username}
        )
        if item is None:
            # Try GSI lookup by email if it looks like an email
            if "@" in username:
                items = await ddb_query(
                    self.settings.table_users,
                    key_condition="email = :e",
                    expression_values={":e": username},
                    index_name="by_email",
                    limit=1,
                )
                if items:
                    item = items[0]
        return item

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new user record."""
        user_id = user_data.get("username", str(uuid.uuid4()))
        item = {
            "username": user_id,
            "email": user_data.get("email", ""),
            "full_name": user_data.get("full_name", ""),
            "hashed_password": user_data.get("password_hash", user_data.get("hashed_password", "")),
            "is_active": True,
            "is_verified": False,
            "role": "patient",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await ddb_put_item(self.settings.table_users, item)
        return {**item, "id": user_id, "password_hash": item["hashed_password"]}

    # ------------------------------------------------------------------
    # Chats
    # ------------------------------------------------------------------

    async def create_chat(
        self,
        user_id: Optional[str],
        title: str,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a new chat session."""
        chat_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "chat_id": chat_id,
            "user_id": user_id or "anonymous",
            "title": title,
            "messages": messages,
            "symptoms": [],
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        await ddb_put_item(self.settings.table_chats, item)
        return {**item, "id": chat_id}

    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a chat by its primary key."""
        # We don't know user_id for direct get, so query with a broad condition
        items = await ddb_query(
            self.settings.table_chats,
            key_condition="chat_id = :c",
            expression_values={":c": chat_id},
            limit=1,
        )
        return items[0] if items else None

    async def list_chats_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """List all chats for a given user (newest first)."""
        return await ddb_query(
            self.settings.table_chats,
            key_condition="user_id = :u",
            expression_values={":u": user_id},
            index_name="by_user",
            scan_index_forward=False,
            limit=100,
        )

    async def update_chat_messages(
        self,
        chat_id: str,
        messages: List[Dict[str, Any]],
        title: Optional[str] = None,
    ) -> None:
        """Update messages (and optionally title) for a chat."""
        # DynamoDB update requires knowledge of the sort key (user_id).
        # Fetch first, then rewrite.
        existing = await self.get_chat(chat_id)
        if existing is None:
            logger.warning("Chat %s not found for update", chat_id)
            return

        item = {
            "chat_id": chat_id,
            "user_id": existing.get("user_id", "anonymous"),
            "title": title or existing.get("title", "Chat"),
            "messages": messages,
            "symptoms": existing.get("symptoms", []),
            "status": existing.get("status", "active"),
            "created_at": existing.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await ddb_put_item(self.settings.table_chats, item)

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by ID."""
        existing = await self.get_chat(chat_id)
        if existing is None:
            return False
        await ddb_delete_item(
            self.settings.table_chats,
            key={"chat_id": chat_id, "user_id": existing.get("user_id", "anonymous")},
        )
        return True

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Check DynamoDB connectivity."""
        return await can_ping_dynamodb()
