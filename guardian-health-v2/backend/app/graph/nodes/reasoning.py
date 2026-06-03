"""
Reasoning node: ML-LLM synthesis and clinical scratchpad generation.
"""


import json
import logging
from pathlib import Path

from app.agents.llm_client import AsyncLLMClient
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.reasoning")

_llm: AsyncLLMClient | None = None

def _get_llm() -> AsyncLLMClient:
    global _llm
    if _llm is None:
        _llm = AsyncLLMClient()
    return _llm

REASONING_PROMPT_PATH = (
    Path(__file__).with_suffix("").parent.parent / "prompts" / "scratchpad.txt"
)


async def reasoner_node(state: TriageState) -> dict:
    """
    Synthesize ML predictions with clinical reasoning.
    Produces scratchpad, reasoning narrative, and confidence score.
    """
    if state.get("error"):
        return {}

    scrubbed = state.get("scrubbed_input", state["user_input"])
    symptoms = state.get("symptoms", [])
    duration = state.get("duration")
    severity = state.get("severity")
    ml_prediction = state.get("ml_prediction")
    top_predictions = state.get("top_predictions", [])
    ml_confidence = state.get("ml_confidence", 0.0)
    history = state.get("conversation_history", [])
    extra_context = state.get("extra_context", "")

    # Build context for reasoning prompt
    context_lines = ["=== CLINICAL CONTEXT ===", f"Symptoms: {', '.join(symptoms)}"]
    if duration:
        context_lines.append(f"Duration: {duration}")
    if severity:
        context_lines.append(f"Severity: {severity}")
    if extra_context:
        context_lines.append(f"Notes: {extra_context}")
    context_lines.append("")

    if ml_prediction:
        context_lines.append("=== ML PREDICTIONS ===")
        for pred in top_predictions[:5]:
            context_lines.append(f"- {pred.get('condition', 'unknown')}: {pred.get('confidence', 0):.2f}")
        context_lines.append(f"Overall confidence: {ml_confidence:.2f}")
        context_lines.append("")

    if history:
        context_lines.append("=== RECENT HISTORY ===")
        for msg in history[-3:]:
            role = msg.get("role", "?")
            content = msg.get("content", "")[:200]
            context_lines.append(f"{role}: {content}")
        context_lines.append("")

    context = "\n".join(context_lines)

    try:
        prompt_text = REASONING_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error("Reasoning prompt not found")
        # Fallback reasoning
        return _fallback_reasoning(symptoms, ml_prediction, ml_confidence)

    llm = _get_llm()

    try:
        result = await llm.parse_json(
            system_prompt=prompt_text,
            user_content=f"{context}\n\nProvide clinical reasoning for this case.",
            node_type="reasoning",
            max_tokens=768,
        )

        return {
            "scratchpad": {
                "observations": result.get("observations", ""),
                "differentials": result.get("differentials", []),
                "red_flags": result.get("red_flags", []),
                "missing_info": result.get("missing_info", []),
                "heuristic_notes": result.get("heuristic_notes", ""),
            },
            "ml_reasoning": result.get("observations", ""),
            "discrepancy_note": result.get("discrepancy_note", ""),
            "reasoning_confidence": float(result.get("confidence", ml_confidence)),
        }
    except Exception as exc:
        logger.error("Reasoner node LLM error: %s", exc)
        return _fallback_reasoning(symptoms, ml_prediction, ml_confidence)


def _fallback_reasoning(
    symptoms: list[str],
    ml_prediction: dict | None,
    ml_confidence: float,
) -> dict:
    """Generate heuristic reasoning when LLM fails."""
    differentials = []
    if ml_prediction:
        differentials = [p.get("condition", "unknown") for p in ml_prediction.get("top_predictions", [])]
    if not differentials and symptoms:
        differentials = [f"Condition related to {s}" for s in symptoms[:3]]

    red_flags = []
    high_risk = {"chest_pain", "shortness_of_breath", "syncope", "seizure", "severe_bleeding", "suicidal_ideation"}
    symptom_set = set(s.lower().replace(" ", "_") for s in symptoms)
    if symptom_set & high_risk:
        red_flags = list(symptom_set & high_risk)

    confidence = ml_confidence if ml_confidence > 0 else (0.4 if symptoms else 0.1)

    return {
        "scratchpad": {
            "observations": f"Symptoms: {', '.join(symptoms)}. ML confidence: {ml_confidence:.2f}",
            "differentials": differentials,
            "red_flags": red_flags,
            "missing_info": ["Duration of symptoms?", "Severity?", "Patient age and medical history?"],
            "heuristic_notes": "Fallback reasoning due to LLM error.",
        },
        "ml_reasoning": f"ML-based analysis with confidence {ml_confidence:.2f}. Top: {differentials[:3]}",
        "discrepancy_note": "LLM reasoning unavailable — using heuristic fallback." if not ml_prediction else "",
        "reasoning_confidence": confidence,
    }
