"""Chat API schemas."""

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    initial_message: Optional[str] = Field(default=None, alias="initialMessage")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ChatResponse(BaseModel):
    id: str
    title: str
    user_id: str = Field(alias="userId")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class MessageResponse(BaseModel):
    id: str
    chat_id: str = Field(alias="chatId")
    role: str
    content: str
    triage: Optional[Any] = None
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)


class ChatDetailResponse(ChatResponse):
    messages: List[MessageResponse] = Field(default_factory=list)
