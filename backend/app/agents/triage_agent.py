"""
Triage Agent — Emergency medical triage with 5-level classification.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.agents.llm_client import AsyncLLMClient
from app.graph.response_builder import format_follow_up, format_triage_report
from app.graph.stream_context import get_stream_emit
from app.graph.streaming import emit_text_chunks
from app.models.enums import TriageLevel

logger = logging.getLogger("guardian.triage")

CONSULTATION_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "consultation.txt"
)
TRIAGE_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent / "prompts" / "triage.txt"
)


def _build_context(
    scrubbed: str,
    history: list[dict],
    clinical_entities: dict[str, Any] | None = None,
    ml_prediction: dict[str, Any] | None = None,
    top_predictions: list[dict] | None = None,
    ml_confidence: float = 0.0,
    scratchpad: dict[str, Any] | None = None,
) -> str:
    """Build compact context for LLM prompts."""
    user_turns = sum(1 for msg in history if msg.get("role") == "user")
    lines = [
        f"Query: {scrubbed}",
        f"Conversation turns (user): {user_turns + 1}",
    ]

    if history:
        recent = " | ".join(
            f"{msg.get('role', '?')}: {msg.get('content', '')[:150]}"
            for msg in history[-5:]
        )
        lines.append(f"History: {recent}")

    if clinical_entities:
        symptoms = ", ".join(clinical_entities.get("symptoms", []))
        lines.append(
            f"Entities: symptoms=[{symptoms}] dur={clinical_entities.get('duration')} "
            f"sev={clinical_entities.get('severity')}"
        )

    preds = top_predictions or (ml_prediction or {}).get("top_predictions", [])
    if preds:
        summary = ", ".join(
            f"{p.get('condition', '?')}({p.get('confidence', 0):.0%})"
            for p in preds[:3]
        )
        lines.append(f"Dataset predictions: {summary} (conf={ml_confidence:.2f})")

    matches = (ml_prediction or {}).get("matches", [])
    if matches:
        refs = "; ".join(
            f"{m['symptom']}:{m['severity']}/{m['region']}"
            for m in matches[:2]
        )
        lines.append(f"Regional data: {refs}")

    if scratchpad:
        if scratchpad.get("observations"):
            lines.append(f"Clinical notes: {scratchpad['observations'][:200]}")
        diffs = scratchpad.get("differentials") or []
        if diffs:
            lines.append(f"Differentials: {', '.join(str(d) for d in diffs[:3])}")
        missing = scratchpad.get("missing_info") or []
        if missing:
            lines.append(f"Missing info: {', '.join(str(m) for m in missing[:4])}")

    if ml_confidence < 0.5:
        lines.append("Dataset confidence is LOW — use clinical reasoning to infer likely conditions.")

    if user_turns <= 1:
        lines.append(
            "NOTE: First user message — prefer follow_up mode unless symptoms clearly indicate emergency."
        )
    else:
        lines.append(
            "NOTE: Patient has answered follow-up questions — you MUST produce triage_report mode with full 5-level assessment."
        )

    return "\n".join(lines)


def _heuristic_triage(symptoms: list[str], severity: str | None = None) -> dict[str, Any]:
    """Heuristic fallback triage when LLM fails."""
    level_1_keywords = {
        "not_breathing", "unresponsive", "pulseless", "cardiac_arrest",
        "anaphylaxis", "choking",
    }
    level_2_keywords = {
        "chest_pain", "shortness_of_breath", "syncope", "seizure",
        "cyanosis", "severe_bleeding", "suicidal_ideation", "stroke",
        "dyspnea", "altered_mental_status",
    }
    level_3_keywords = {
        "fever", "dehydration", "vomiting", "severe_abdominal_pain",
        "vision_loss", "petechiae",
    }

    symptom_set = {s.lower().replace(" ", "_") for s in symptoms}

    if symptom_set & level_1_keywords:
        return {
            "response_mode": "triage_report",
            "triage_level": TriageLevel.LEVEL_1.value,
            "level_title": "Resuscitation",
            "level_justification": "Symptoms suggest an imminent life-threatening condition.",
            "immediate_actions": [
                "Contact local emergency services (102/108 in India) immediately.",
                "Begin CPR if the person is unresponsive and not breathing.",
                "Do not leave the person alone.",
            ],
            "crucial_warnings": [
                "Do not delay calling for emergency help.",
                "Do not attempt to move someone with suspected spinal injury.",
            ],
            "resource_recommendations": [
                "Nearest hospital emergency department — go immediately.",
            ],
            "required_follow_up": [
                "Any loss of consciousness, worsening breathing, or no pulse.",
            ],
            "assessment": "Critical emergency features detected requiring immediate resuscitation-level response.",
            "care_setting": "ER",
            "heuristic": True,
        }

    if symptom_set & level_2_keywords or severity == "severe":
        return {
            "response_mode": "triage_report",
            "triage_level": TriageLevel.LEVEL_2.value,
            "level_title": "Emergent",
            "level_justification": "High-risk symptoms that may deteriorate rapidly without immediate care.",
            "immediate_actions": [
                "Go to the nearest hospital emergency department immediately.",
                "Contact local emergency services (102/108 in India) if you need urgent transport.",
                "Have someone stay with you and monitor your condition.",
            ],
            "crucial_warnings": [
                "Do not drive yourself if you have severe symptoms.",
                "Do not wait to see if symptoms pass on their own.",
            ],
            "resource_recommendations": [
                "Emergency Room — immediate evaluation required.",
            ],
            "required_follow_up": [
                "Worsening pain, difficulty breathing, confusion, or fainting.",
            ],
            "assessment": "Your symptoms require emergent medical evaluation.",
            "care_setting": "ER",
            "heuristic": True,
        }

    if symptom_set & level_3_keywords or severity == "moderate":
        return {
            "response_mode": "triage_report",
            "triage_level": TriageLevel.LEVEL_3.value,
            "level_title": "Urgent",
            "level_justification": "Symptoms need prompt medical evaluation with multiple resources.",
            "immediate_actions": [
                "Visit an urgent care center or emergency department today.",
                "Monitor vital signs if possible (temperature, pulse).",
                "Stay hydrated and rest while arranging care.",
            ],
            "crucial_warnings": [
                "Do not ignore worsening symptoms.",
                "Do not self-medicate with prescription drugs without guidance.",
            ],
            "resource_recommendations": [
                "Urgent Care or Emergency Department — same-day evaluation.",
                "A thermometer and pulse oximeter may help monitor your condition.",
            ],
            "required_follow_up": [
                "High fever, persistent vomiting, severe pain, or confusion.",
            ],
            "assessment": "Your symptoms should be evaluated promptly by a medical professional.",
            "care_setting": "urgent_care",
            "heuristic": True,
        }

    if severity == "mild" or symptom_set:
        return {
            "response_mode": "triage_report",
            "triage_level": TriageLevel.LEVEL_5.value,
            "level_title": "Non-Urgent",
            "level_justification": "Symptoms appear mild and manageable with self-care or routine evaluation.",
            "immediate_actions": [
                "Rest and monitor symptoms at home.",
                "Stay hydrated and maintain adequate nutrition.",
                "Use OTC remedies as appropriate for your symptoms.",
            ],
            "crucial_warnings": [
                "Do not ignore symptoms that worsen suddenly.",
            ],
            "resource_recommendations": [
                "Home care with self-monitoring.",
                "Primary care visit if symptoms persist beyond 5–7 days.",
                "A thermometer may help track fever.",
            ],
            "required_follow_up": [
                "Sudden severe pain, high fever, difficulty breathing, or new alarming symptoms.",
            ],
            "assessment": "Your symptoms appear non-urgent but should be monitored.",
            "care_setting": "home_care",
            "heuristic": True,
        }

    return {
        "response_mode": "follow_up",
        "follow_up_questions": [
            "What is your main symptom right now?",
            "How long have you had these symptoms?",
            "Are you experiencing any difficulty breathing, chest pain, or severe bleeding?",
        ],
        "preliminary_assessment": "I need a few more details to assess your situation safely.",
        "heuristic": True,
    }


async def _run_llm_json(
    llm: AsyncLLMClient,
    *,
    system_prompt: str,
    user_content: str,
    node_type: str,
    max_tokens: int,
) -> dict[str, Any]:
    emit = get_stream_emit()
    final_nodes = {"consultation", "triage", "disease_info"}

    if emit and node_type in final_nodes:
        status = emit({"type": "status", "message": "Writing your response..."})
        if asyncio.iscoroutine(status):
            await status
        result = await llm.parse_json_stream(
            system_prompt=system_prompt,
            user_content=user_content,
            node_type=node_type,
            max_tokens=max_tokens,
        )
        mode = (result.get("response_mode") or "triage_report").lower()
        if mode == "follow_up":
            visible = format_follow_up(result)
        elif node_type == "disease_info":
            visible = result.get("description") or f"Information about {result.get('condition', 'this condition')}."
        else:
            visible = format_triage_report(result)
        await emit_text_chunks(emit, visible)
        return result

    return await llm.parse_json(
        system_prompt=system_prompt,
        user_content=user_content,
        node_type=node_type,
        max_tokens=max_tokens,
    )


async def consult(
    scrubbed: str,
    history: list[dict],
    top_predictions: list[dict],
    ml_confidence: float,
    llm: AsyncLLMClient,
    clinical_entities: dict[str, Any] | None = None,
    scratchpad: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        prompt_text = CONSULTATION_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Consultation prompt not found")
        return _heuristic_triage(
            symptoms=(clinical_entities or {}).get("symptoms", []),
            severity=(clinical_entities or {}).get("severity"),
        )

    context = _build_context(
        scrubbed=scrubbed,
        history=history,
        clinical_entities=clinical_entities,
        top_predictions=top_predictions,
        ml_confidence=ml_confidence,
        scratchpad=scratchpad,
    )

    try:
        result = await _run_llm_json(
            llm,
            system_prompt=prompt_text,
            user_content=context,
            node_type="consultation",
            max_tokens=1536,
        )
        result["heuristic"] = False
        return result
    except Exception as exc:
        logger.error("Consultation LLM call failed: %s", exc)
        return _heuristic_triage(
            symptoms=(clinical_entities or {}).get("symptoms", []),
            severity=(clinical_entities or {}).get("severity"),
        )


async def analyze(
    scrubbed: str,
    history: list[dict],
    clinical_entities: dict[str, Any],
    ml_prediction: dict[str, Any] | None,
    llm: AsyncLLMClient,
    scratchpad: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
        scratchpad=scratchpad,
    )

    try:
        result = await _run_llm_json(
            llm,
            system_prompt=prompt_text,
            user_content=context,
            node_type="triage",
            max_tokens=1536,
        )
        result["heuristic"] = False
        return result
    except Exception as exc:
        logger.error("Triage analysis LLM call failed: %s", exc)
        return _heuristic_triage(
            symptoms=clinical_entities.get("symptoms", []),
            severity=clinical_entities.get("severity"),
        )
