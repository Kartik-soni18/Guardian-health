"""GuardianHealth v2 Chat Service — DynamoDB backend."""

from typing import Any, Dict, List, Optional

from app.db.dynamodb import DynamoDBManager


class ChatService:
    """Business logic for chat management."""

    def __init__(self, db: DynamoDBManager) -> None:
        self.db = db

    async def create_chat(
        self,
        user_id: Optional[str],
        title: str,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create a new chat."""
        return await self.db.create_chat(user_id, title, messages)

    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat by ID."""
        return await self.db.get_chat(chat_id)

    async def list_user_chats(self, user_id: str) -> List[Dict[str, Any]]:
        """List all chats for a user."""
        return await self.db.list_chats_by_user(user_id)

    async def update_messages(self, chat_id: str, messages: List[Dict[str, Any]], title: Optional[str] = None) -> None:
        """Update chat messages."""
        await self.db.update_chat_messages(chat_id, messages, title)

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        return await self.db.delete_chat(chat_id)

    def is_owner(self, chat: Dict[str, Any], user_id: str) -> bool:
        """Check if user owns the chat."""
        return chat.get("user_id") == user_id
