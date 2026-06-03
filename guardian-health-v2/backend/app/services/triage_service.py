"""GuardianHealth v2 Triage Service — symptom checker with ML + rules fallback."""


import time
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.schemas.triage import (
    ConversationMessage,
    TriageLevel,
    TriageRequest,
    TriageResponse,
    TriageResult,
)
from app.services.ml_service import MLService


# Emergency keywords for fast-path detection
EMERGENCY_KEYWORDS = {
    "chest pain", "heart attack", "cardiac arrest", "not breathing",
    "unconscious", "seizure", "stroke", "severe bleeding", "anaphylaxis",
    "allergic reaction", "suicide", "overdose", "poisoning",
    "can't breathe", "difficulty breathing", "shortness of breath",
    "sudden numbness", "paralyzed", "gunshot", "stab wound",
    "head injury", "burns",
}

URGENT_KEYWORDS = {
    "fever", "infection", "possible fracture", "dehydration",
    "severe vomiting", "severe diarrhea", "migraine", "concussion",
    "abdominal pain", "back pain", "eye injury",
}

SELF_CARE_KEYWORDS = {
    "mild cold", "runny nose", "sore throat", "minor cut", "bruise",
    "mild headache", "cough", "seasonal allergies", "sunburn",
    "rest", "fluids", "otc",
}


class TriageService:
    """Orchestrates triage: ML model -> rules -> optional LLM fallback."""

    def __init__(self, ml_service: Optional[MLService] = None) -> None:
        self.ml = ml_service or MLService()

    async def invoke_graph(self, request: TriageRequest) -> TriageResponse:
        """Run the full triage pipeline."""
        query_lower = request.query.lower()

        # 1. Emergency keyword fast-path
        if any(kw in query_lower for kw in EMERGENCY_KEYWORDS):
            return TriageResponse(
                triage=TriageResult(
                    level=TriageLevel.EMERGENCY,
                    confidence=0.95,
                    explanation="Emergency keywords detected in symptoms.",
                    recommended_actions=[
                        "Call emergency services (911) immediately.",
                        "Do not drive yourself to the hospital.",
                        "Stay calm and rest while waiting for help.",
                    ],
                ),
                response="🚨 This sounds like a medical emergency. Please call 911 or go to the nearest emergency room immediately. Do not wait.",
            )

        # 2. Try ML model
        ml_result = None
        try:
            ml_result = await self.ml.predict(request.query)
        except Exception:
            ml_result = None

        if ml_result and ml_result.confidence >= 0.7:
            return self._build_response(ml_result, request)

        # 3. Rules-based fallback
        rules_result = self._rules_based_triage(query_lower)
        if rules_result.confidence >= 0.6:
            return self._build_response(rules_result, request)

        # 4. ML with lower confidence
        if ml_result:
            return self._build_response(ml_result, request)

        # 5. Final fallback
        return self._build_response(
            TriageResult(
                level=TriageLevel.UNKNOWN,
                confidence=0.5,
                explanation="Unable to confidently assess symptoms. Recommend consulting a healthcare professional.",
                follow_up_questions=[
                    "How long have you been experiencing these symptoms?",
                    "Are the symptoms getting worse?",
                    "Do you have any pre-existing medical conditions?",
                ],
                recommended_actions=["Consult a healthcare professional for proper diagnosis."],
            ),
            request,
        )

    def _rules_based_triage(self, query_lower: str) -> TriageResult:
        """Simple keyword-based triage when ML is unavailable or uncertain."""
        if any(kw in query_lower for kw in EMERGENCY_KEYWORDS):
            return TriageResult(
                level=TriageLevel.EMERGENCY,
                confidence=0.9,
                explanation="Emergency keywords detected.",
                recommended_actions=["Seek emergency care immediately."],
            )
        if any(kw in query_lower for kw in URGENT_KEYWORDS):
            return TriageResult(
                level=TriageLevel.URGENT,
                confidence=0.75,
                explanation="Urgent symptoms detected that need prompt medical attention.",
                recommended_actions=["See a doctor within 24 hours."],
            )
        if any(kw in query_lower for kw in SELF_CARE_KEYWORDS):
            return TriageResult(
                level=TriageLevel.SELF_CARE,
                confidence=0.7,
                explanation="Mild symptoms that can likely be managed at home.",
                recommended_actions=["Rest, hydrate, monitor symptoms.", "Seek care if symptoms worsen."],
            )
        return TriageResult(
            level=TriageLevel.UNKNOWN,
            confidence=0.4,
            explanation="No clear symptom patterns detected.",
        )

    def _build_response(self, result: TriageResult, request: TriageRequest) -> TriageResponse:
        """Build human-readable response from triage result."""
        response_text = self._generate_response_text(result)
        return TriageResponse(
            triage=result,
            response=response_text,
            sources=["GuardianHealth symptom database"],
        )

    def _generate_response_text(self, result: TriageResult) -> str:
        templates = {
            TriageLevel.EMERGENCY: "🚨 Emergency: {}",
            TriageLevel.URGENT: "⚠️ Urgent: {}",
            TriageLevel.PRIMARY_CARE: "📅 Primary Care: {}",
            TriageLevel.SELF_CARE: "🏠 Self-Care: {}",
            TriageLevel.UNKNOWN: "❓ {}",
        }
        explanation = result.explanation or "No detailed explanation available."
        template = templates.get(result.level, "{}")
        return template.format(explanation)
