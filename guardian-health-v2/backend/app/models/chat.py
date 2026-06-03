"""Pydantic models for Chat domain — DynamoDB-native.

Chats are stored as single items (chat_id, user_id composite PK) with an
embedded message list. DynamoDB item size limit (400 KB) is sufficient for
typical medical conversations of 20-50 turns.
"""


from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ChatStatus, TriageLevel


# ------------------------------------------------------------------------------
# Message sub-model
# ------------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """A single turn in a patient-clinician (or patient-LLM) conversation.

    audit_hash is a SHA-256 digest of (role + content + timestamp) used
    for tamper-evident logging.
    """

    role: str  # "user", "assistant", "system", "guardian"
    content: str
    timestamp: str = Field(default_factory=lambda: _utc_iso())
    triage_level: Optional[TriageLevel] = None
    symptoms: List[str] = Field(default_factory=list)
    audit_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("role")
    @classmethod
    def _valid_role(cls, v: str) -> str:
        allowed = {"user", "assistant", "system", "guardian", "tool"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v


# ------------------------------------------------------------------------------
# Chat (aggregate root)
# ------------------------------------------------------------------------------


class Chat(BaseModel):
    """A complete chat session stored as one DynamoDB item."""

    chat_id: str
    user_id: str
    title: str = "New Consultation"
    messages: List[ChatMessage] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    status: ChatStatus = ChatStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: _utc_iso())
    updated_at: str = Field(default_factory=lambda: _utc_iso())

    model_config = {"populate_by_name": True}


# ------------------------------------------------------------------------------
# Request / response DTOs
# ------------------------------------------------------------------------------


class ChatCreate(BaseModel):
    """Payload to start a new chat."""

    title: Optional[str] = "New Consultation"
    initial_message: Optional[str] = None


class ChatResponse(BaseModel):
    """Full chat representation for API responses."""

    chat_id: str
    user_id: str
    title: str
    messages: List[ChatMessage]
    symptoms: List[str]
    status: ChatStatus
    created_at: str
    updated_at: str
    message_count: int = 0

    @field_validator("message_count", mode="before")
    @classmethod
    def _count_messages(cls, v, info):
        if v == 0 and "messages" in info.data:
            return len(info.data["messages"])
        return v


class ChatListItem(BaseModel):
    """Lightweight chat metadata for listing endpoints."""

    chat_id: str
    user_id: str
    title: str
    status: ChatStatus
    created_at: str
    updated_at: str
    message_count: int = 0


class ChatListResponse(BaseModel):
    """Paginated list of chats."""

    items: List[ChatListItem]
    total: int
    next_cursor: Optional[str] = None


# ------------------------------------------------------------------------------
# DynamoDB serialization helpers
# ------------------------------------------------------------------------------


def chat_to_ddb_item(chat: Chat) -> Dict[str, Any]:
    """Serialize a Chat aggregate to a plain dict for DynamoDB storage."""
    return {
        "chat_id": chat.chat_id,
        "user_id": chat.user_id,
        "title": chat.title,
        "messages": [_message_to_dict(m) for m in chat.messages],
        "symptoms": chat.symptoms,
        "status": chat.status.value,
        "created_at": chat.created_at,
        "updated_at": chat.updated_at,
    }


def ddb_item_to_chat(item: Dict[str, Any]) -> Chat:
    """Reconstruct a Chat from a deserialized DynamoDB item.

    Handles both aioboto3 Table-style (plain values) and client-style
    (type-wrapped) attribute formats.
    """

    def _unwrap(v):
        if isinstance(v, dict):
            if "S" in v:
                return v["S"]
            if "N" in v:
                return v["N"]
            if "BOOL" in v:
                return v["BOOL"]
            if "L" in v:
                return [_unwrap(i) for i in v["L"]]
            if "M" in v:
                return {k: _unwrap(val) for k, val in v["M"].items()}
        return v

    u = {k: _unwrap(v) for k, v in item.items()}

    raw_messages = u.get("messages", [])
    messages: List[ChatMessage] = []
    for rm in raw_messages:
        if isinstance(rm, dict):
            messages.append(
                ChatMessage(
                    role=str(rm.get("role", "user")),
                    content=str(rm.get("content", "")),
                    timestamp=str(rm.get("timestamp", _utc_iso())),
                    triage_level=_parse_optional_triage(rm.get("triage_level")),
                    symptoms=list(rm.get("symptoms", [])),
                    audit_hash=rm.get("audit_hash"),
                    metadata=dict(rm.get("metadata", {})),
                )
            )

    return Chat(
        chat_id=str(u["chat_id"]),
        user_id=str(u["user_id"]),
        title=str(u.get("title", "New Consultation")),
        messages=messages,
        symptoms=list(u.get("symptoms", [])),
        status=ChatStatus(str(u.get("status", "active"))),
        created_at=str(u.get("created_at", _utc_iso())),
        updated_at=str(u.get("updated_at", _utc_iso())),
    )


def chat_to_response(chat: Chat) -> ChatResponse:
    """Convert internal Chat to API-facing ChatResponse."""
    return ChatResponse(
        chat_id=chat.chat_id,
        user_id=chat.user_id,
        title=chat.title,
        messages=chat.messages,
        symptoms=chat.symptoms,
        status=chat.status,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=len(chat.messages),
    )


def chat_to_list_item(chat: Chat) -> ChatListItem:
    """Convert internal Chat to lightweight list item."""
    return ChatListItem(
        chat_id=chat.chat_id,
        user_id=chat.user_id,
        title=chat.title,
        status=chat.status,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=len(chat.messages),
    )


# ------------------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------------------


def _message_to_dict(msg: ChatMessage) -> Dict[str, Any]:
    """Serialize a ChatMessage to a plain dict."""
    d: Dict[str, Any] = {
        "role": msg.role,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "symptoms": msg.symptoms,
        "metadata": msg.metadata,
    }
    if msg.triage_level:
        d["triage_level"] = msg.triage_level.value
    if msg.audit_hash:
        d["audit_hash"] = msg.audit_hash
    return d


def _parse_optional_triage(v: Any) -> Optional[TriageLevel]:
    if v is None:
        return None
    try:
        return TriageLevel(str(v))
    except ValueError:
        return None


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()