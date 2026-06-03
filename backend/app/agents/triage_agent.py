"""
Triage Agent — Provides clinical consultation and triage analysis.

Two main modes:
1. consult(): Full consultation with context building
2. analyze(): Structured triage level assignment
"""


import json
import logging
from pathlib import Path
from typing import Any

from app.agents.llm_client import AsyncLLMClient

logger = logging.getLogger("guardian.triage")

CONSULTATION_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "consultation.txt"
)
TRIAGE_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "triage.txt"
)
SCRATCHPAD_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "scratchpad.txt"
)


def _build_context(
    scrubbed: str,
    history: list[dict],
    clinical_entities: dict[str, Any] | None = None,
    ml_prediction: dict[str, Any] | None = None,
    top_predictions: list[dict] | None = None,
    ml_confidence: float = 0.0,
) -> str:
    """Build rich context string for LLM prompts."""
    lines = ["=== PATIENT QUERY ===", scrubbed, ""]

    if history:
        lines.append("=== CONVERSATION HISTORY ===")
        for msg in history[-6:]:  # Last 6 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        lines.append("")

    if clinical_entities:
        lines.append("=== EXTRACTED CLINICAL ENTITIES ===")
        lines.append(json.dumps(clinical_entities, indent=2))
        lines.append("")

    if ml_prediction:
        lines.append("=== ML PREDICTION ===")
        lines.append(json.dumps(ml_prediction, indent=2))
        lines.append("")

    if top_predictions:
        lines.append("=== ML TOP PREDICTIONS ===")
        for pred in top_predictions[:5]:
            lines.append(f"- {pred.get('condition', 'unknown')}: {pred.get('confidence', 0):.2f}")
        lines.append(f"Overall ML confidence: {ml_confidence:.2f}")
        lines.append("")

    return "\n".join(lines)


def _heuristic_triage(symptoms: list[str], severity: str | None = None) -> dict[str, Any]:
    """Heuristic fallback triage when LLM fails."""
    emergent_keywords = {
        "chest_pain", "shortness_of_breath", "syncope", "seizure",
        "cyanosis", "severe_bleeding", "suicidal_ideation", "anaphylaxis",
        "stroke", "dyspnea",
    }
    urgent_keywords = {
        "fever", "dehydration", "vomiting", "severe_abdominal_pain",
        "altered_mental_status", "vision_loss", "petechiae",
    }

    symptom_set = set(s.lower().replace(" ", "_") for s in symptoms)

    if symptom_set & emergent_keywords or severity == "severe":
        return {
            "level": "emergent",
            "care_setting": "ER",
            "explanation": "Your symptoms include features that require immediate emergency evaluation.",
            "action": "Seek emergency care immediately or call emergency services.",
            "timeframe": "Immediately",
            "red_flags": list(symptom_set & emergent_keywords),
            "safety_net": "If symptoms worsen while waiting, call emergency services.",
            "heuristic": True,
        }

    if symptom_set & urgent_keywords or severity == "moderate":
        return {
            "level": "urgent",
            "care_setting": "urgent_care",
            "explanation": "Your symptoms should be evaluated promptly by a medical professional.",
            "action": "Visit an urgent care center or schedule a same-day appointment.",
            "timeframe": "Within 24 hours",
            "red_flags": list(symptom_set & urgent_keywords),
            "safety_net": "Go to the emergency department if symptoms worsen significantly.",
            "heuristic": True,
        }

    return {
        "level": "routine",
        "care_setting": "primary_care",
        "explanation": "Your symptoms do not suggest an immediate emergency but should be evaluated.",
        "action": "Schedule an appointment with your primary care provider.",
        "timeframe": "Within 3-5 days",
        "red_flags": [],
        "safety_net": "Seek urgent care if symptoms worsen or new symptoms develop.",
        "heuristic": True,
    }


async def consult(
    scrubbed: str,
    history: list[dict],
    top_predictions: list[dict],
    ml_confidence: float,
    llm: AsyncLLMClient,
) -> dict[str, Any]:
    """
    Provide a full clinical consultation.

    Args:
        scrubbed: Scrubbed user input.
        history: Conversation history.
        top_predictions: ML model top predictions.
        ml_confidence: Overall ML confidence score.
        llm: AsyncLLMClient.

    Returns:
        Consultation result dict.
    """
    try:
        prompt_text = CONSULTATION_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Consultation prompt not found")
        return {
            "assessment": "Consultation service temporarily unavailable.",
            "key_concerns": [],
            "plan": "Please consult a healthcare provider directly.",
            "when_to_seek": "If you feel your condition is urgent, seek immediate care.",
            "disclaimer": "This is not medical advice. Consult a healthcare professional.",
            "references": [],
            "follow_up_questions": ["Can you describe your symptoms in more detail?"],
        }

    context = _build_context(
        scrubbed=scrubbed,
        history=history,
        top_predictions=top_predictions,
        ml_confidence=ml_confidence,
    )

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=context,
            node_type="consultation",
            max_tokens=1024,
        )
        result["heuristic"] = False
        return result
    except Exception as exc:
        logger.error("Consultation LLM call failed: %s", exc)
        return {
            "assessment": "Unable to generate full consultation at this time.",
            "key_concerns": [p.get("condition", "unknown") for p in top_predictions[:3]],
            "plan": "Please consult a healthcare provider for personalized advice.",
            "when_to_seek": "Seek immediate care for severe or worsening symptoms.",
            "disclaimer": "This is not medical advice. Consult a healthcare professional.",
            "references": [],
            "follow_up_questions": ["Can you describe your main symptom?", "How long have you had these symptoms?"],
            "heuristic": True,
        }


async def analyze(
    scrubbed: str,
    history: list[dict],
    clinical_entities: dict[str, Any],
    ml_prediction: dict[str, Any] | None,
    llm: AsyncLLMClient,
) -> dict[str, Any]:
    """
    Analyze and assign triage level.

    Args:
        scrubbed: Scrubbed user input.
        history: Conversation history.
        clinical_entities: Extracted clinical entities.
        ml_prediction: ML prediction dict with top_predictions.
        llm: AsyncLLMClient.

    Returns:
        Triage analysis dict with level, care_setting, etc.
    """
    try:
        prompt_text = TRIAGE_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Triage prompt not found, using heuristic fallback")
        return _heuristic_triage(
            symptoms=clinical_entities.get("symptoms", []),
            severity=clinical_entities.get("severity"),
        )

    top_predictions = []
    ml_confidence = 0.0
    if ml_prediction:
        top_predictions = ml_prediction.get("top_predictions", [])
        ml_confidence = ml_prediction.get("confidence", 0.0)

    context = _build_context(
        scrubbed=scrubbed,
        history=history,
        clinical_entities=clinical_entities,
        ml_prediction=ml_prediction,
        top_predictions=top_predictions,
        ml_confidence=ml_confidence,
    )

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=context,
            node_type="triage",
            max_tokens=768,
        )
        result["heuristic"] = False
        return result
    except Exception as exc:
        logger.error("Triage analysis LLM call failed: %s", exc)
        return _heuristic_triage(
            symptoms=clinical_entities.get("symptoms", []),
            severity=clinical_entities.get("severity"),
        )
