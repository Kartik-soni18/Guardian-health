from typing import Optional, List
from pydantic import BaseModel


class TriageRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None


class TriageResponse(BaseModel):
    status: str = "triage"
    level: Optional[str] = None
    reasoning: Optional[str] = None
    red_flags: Optional[List[str]] = None
    remedies: Optional[List[str]] = None
    guideline_source: Optional[str] = None
    disease: Optional[str] = None
    disease_name: Optional[str] = None
    confidence: Optional[float] = None
    symptoms: Optional[List[str]] = None
    care_advice: Optional[str] = None
    otc_products: Optional[List[str]] = None
    all_predictions: Optional[List[dict]] = None
    research: Optional[dict] = None
    audit: Optional[dict] = None
    chat_id: Optional[str] = None
