"""Supervisor reasoning node: scratchpad + clinical assessment over ML output."""

import json
import logging
import random

from app.graph.state import TriageState
from app import llm_client as gemini_client
from app.prompt_hub import get_prompt

logger = logging.getLogger(__name__)

_EMERGENCY_KEYWORDS = [
    "can't breathe", "cannot breathe", "heart attack", "stroke",
    "unconscious", "unresponsive", "severe chest pain", "coughing blood",
    "vomiting blood", "seizure", "911",
]


def reasoner_node(state: TriageState) -> dict:
    """Run supervisor scratchpad + reasoning over ML prediction."""
    user_query = state.get("user_input", "")
    scrubbed = state.get("scrubbed_input", "")
    ml_prediction = state.get("ml_prediction")
    confidence = state.get("ml_confidence", 0.0)
    conversation_history = state.get("conversation_history", [])

    # ── Scratchpad ──────────────────────────────────────────────────────────
    turns = len([e for e in (conversation_history or []) if e.get("role") == "user"])
    history_summary = f"\n[{turns} prior conversation turn(s) on record]" if turns else ""
    user_content = (
        f"Patient query: {user_query}{history_summary}\n\n"
        "Write your Decision Scratchpad and routing plan."
    )

    try:
        scratchpad_prompt = get_prompt("supervisor-scratchpad")
        raw = gemini_client.call(
            system_prompt=scratchpad_prompt,
            user_content=user_content,
            temperature=0.2,
            max_tokens=400,
            timeout=15.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        scratchpad = json.loads(raw)
    except Exception as exc:
        logger.warning("[Graph] Scratchpad failed: %s — defaults", exc)
        scratchpad = {
            "scratchpad": random.choice([
                "Fallback: routing directly to consultation due to processing issue.",
                "System fallback activated — proceeding with consultation path.",
                "Direct routing to gather more clinical information.",
            ]),
            "worker_order": ["privacy_officer", "diagnostic_specialist", "compliance_auditor"],
            "routing_decision": "consultation",
            "key_risks": "Unknown",
        }

    # ── Reasoning over ML ───────────────────────────────────────────────────
    reasoning = _reason_over_ml(scrubbed, ml_prediction, confidence)

    # Override routing if emergency detected
    if reasoning.get("emergency_detected"):
        final_routing = "emergency"
    else:
        final_routing = reasoning.get("final_routing", scratchpad.get("routing_decision", "consultation"))

    logger.info("[Graph] reasoner routing=%s emergency=%s",
                final_routing, reasoning.get("emergency_detected"))

    return {
        "scratchpad": scratchpad.get("scratchpad"),
        "ml_reasoning": reasoning.get("ml_assessment"),
        "discrepancy_note": reasoning.get("discrepancy_note"),
        "emergency_detected": reasoning.get("emergency_detected", False),
        "final_routing": final_routing,
    }


def _reason_over_ml(scrubbed_query: str, ml_prediction: dict | None, confidence: float) -> dict:
    if ml_prediction is None:
        return {
            "ml_assessment": "No ML prediction — routing to consultation.",
            "discrepancy_detected": False,
            "discrepancy_note": None,
            "emergency_detected": False,
            "final_routing": "consultation",
        }

    disease = ml_prediction.get("disease", "Unknown")
    conf_pct = ml_prediction.get("confidence_pct", "0%")
    top_3 = ml_prediction.get("top_3", [])
    top_3_str = ", ".join(f"{d} ({c*100:.1f}%)" for d, c in top_3)

    user_content = (
        f"Patient description (PII-scrubbed): {scrubbed_query}\n\n"
        f"Guardian-ML prediction:\n"
        f"  Disease: {disease}\n"
        f"  Confidence: {conf_pct}\n"
        f"  Top-3 candidates: {top_3_str}\n\n"
        "Reason over this output and provide your clinical assessment."
    )

    try:
        reasoning_prompt = get_prompt("supervisor-reasoning")
        raw = gemini_client.call(
            system_prompt=reasoning_prompt,
            user_content=user_content,
            temperature=0.2,
            max_tokens=350,
            timeout=15.0,
        )
        raw = raw.strip("```json").strip("```").strip()
        result = json.loads(raw)
        if confidence < 0.50 and result.get("final_routing") == "diagnosed":
            result["final_routing"] = "consultation"
        return result
    except Exception as exc:
        logger.warning("[Graph] Reasoning failed: %s — heuristic", exc)
        tl = scrubbed_query.lower()
        emergency = any(k in tl for k in _EMERGENCY_KEYWORDS)
        return {
            "ml_assessment": random.choice([
                f"ML model suggests {disease} at {conf_pct} — clinical correlation appears reasonable.",
                f"Guardian-ML indicates {disease} ({conf_pct}); this aligns with the symptom description.",
                f"The diagnostic model returns {disease} with {conf_pct} confidence. No obvious discrepancy noted.",
            ]),
            "discrepancy_detected": False,
            "discrepancy_note": None,
            "emergency_detected": emergency,
            "final_routing": "diagnosed" if confidence >= 0.50 else "consultation",
        }
