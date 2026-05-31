from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str | dict
    timestamp: datetime | None = None
    type: Optional[str] = None
    privacy: Optional[dict] = None
    metadata: Optional[dict] = None


class ChatMetadata(BaseModel):
    chat_id: str
    title: str = "New Chat"
    last_updated: datetime
    created_at: datetime | None = None
    symptoms: List[str] = []
    status: str = "new"
