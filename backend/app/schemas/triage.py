"""Triage API schemas."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TriageRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    chat_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

    @field_validator("query")
    @classmethod
    def _normalize_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters after trimming.")
        return v


class TriageResponse(BaseModel):
    response: str
    triage_level: Optional[str] = None
    routing: str = "unknown"
    symptoms: List[str] = Field(default_factory=list)
    assessment: str = ""
    reasoning: str = ""
    what_to_do: List[str] = Field(default_factory=list)
    what_not_to_do: List[str] = Field(default_factory=list)
    likely_conditions: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    dataset_used: bool = False
    compliance_passed: bool = True
    audit_hash: Optional[str] = None
    disclaimer: str = (
        "This information is for educational purposes only and does not "
        "constitute medical advice. Seek professional care for medical concerns."
    )
