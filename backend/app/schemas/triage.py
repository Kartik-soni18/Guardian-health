"""Triage schema definitions — re-exports plus TriageResult helper."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import TriageLevel
from app.models.triage import TriageRequest, TriageResponse


class TriageResult(BaseModel):
    """Internal triage outcome produced by ML/rules engine."""

    level: TriageLevel = TriageLevel.UNKNOWN
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    explanation: str = ""
    recommended_actions: List[str] = []
    follow_up_questions: List[str] = []


class SimpleTriageResponse(BaseModel):
    """Simplified triage response used by legacy service layer."""

    triage: TriageResult
    response: str = ""
    sources: List[str] = []
    chat_id: Optional[str] = None


__all__ = [
    "TriageLevel",
    "TriageRequest",
    "TriageResponse",
    "TriageResult",
    "SimpleTriageResponse",
    "ConversationMessage",
]
