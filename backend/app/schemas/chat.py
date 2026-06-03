"""Chat schema re-exports from app.models."""

from app.models.chat import ChatCreate, ChatListResponse, ChatMessage, ChatResponse

# Alias used by triage router for conversation history
ConversationMessage = ChatMessage

__all__ = [
    "ChatCreate",
    "ChatListResponse",
    "ChatMessage",
    "ChatResponse",
    "ConversationMessage",
]
