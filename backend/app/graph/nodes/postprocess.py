"""Post-processing: compliance review, response assembly, no-op persist."""

import hashlib
import json
import logging
import time

from app.agents.compliance import compliance_review
from app.graph.response_builder import build_triage_response
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.postprocess")


async def compliance_node(state: TriageState) -> dict:
    if state.get("error") and not state.get("response_text"):
        return {}

    response_text = state.get("response_text", "")
    if not response_text:
        return {}

    structured = state.get("structured_response") or {}
    review_input = {
        "response_text": response_text,
        "response_mode": structured.get("response_mode"),
        **(state.get("triage_result") or {}),
        **(state.get("consultation_result") or {}),
    }

    try:
        result = compliance_review(review_input)
        return {
            "compliance_passed": result["approved"],
            "compliance_note": result.get("blocked_reason"),
            "response_text": result["final_response"],
            "compliance_violations": result.get("violations", []),
        }
    except Exception as exc:
        logger.error("Compliance node error: %s", exc)
        return {
            "compliance_passed": True,
            "compliance_note": f"Compliance review failed: {type(exc).__name__}",
            "response_text": response_text,
        }


async def assembler_node(state: TriageState) -> dict:
    if state.get("error") and not state.get("response_text"):
        error_msg = state.get("error", "An unknown error occurred")
        return {
            "response_data": {
                "response": f"I encountered an issue: {error_msg}. Please try again.",
                "triage_level": None,
                "routing": "error",
                "metadata": {"error": error_msg},
            }
        }

    if state.get("is_medical") is False:
        rejection_reason = state.get("rejection_reason", "This query is outside my medical scope.")
        return {
            "response_data": {
                "response": (
                    f"I'm designed to help with health-related questions. {rejection_reason}"
                ),
                "triage_level": None,
                "routing": "rejected",
                "metadata": {"rejection_category": state.get("rejection_category")},
            }
        }

    response_text = state.get("response_text", "")
    triage_result = state.get("triage_result") or {}
    consultation_result = state.get("consultation_result") or {}
    structured = state.get("structured_response") or {}
    if not structured:
        source = triage_result or consultation_result
        if source:
            structured = build_triage_response(source, state)
            response_text = structured.get("response", response_text)
    final_routing = state.get("final_routing", "unknown")
    triage_level = (
        structured.get("triage_level")
        or triage_result.get("triage_level")
        or triage_result.get("level")
    )

    audit_payload = {
        "user_id": state.get("user_id"),
        "symptoms": state.get("symptoms", []),
        "triage_level": triage_level,
        "routing": final_routing,
        "timestamp": time.time(),
    }
    audit_hash = hashlib.sha256(
        json.dumps(audit_payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    return {
        "response_data": {
            "response": response_text,
            "triage_level": triage_level,
            "level_title": structured.get("level_title"),
            "level_justification": structured.get("level_justification", ""),
            "response_mode": structured.get("response_mode", "triage_report"),
            "needs_follow_up": structured.get("needs_follow_up", False),
            "follow_up_questions": structured.get("follow_up_questions", []),
            "care_setting": structured.get("care_setting") or triage_result.get("care_setting"),
            "routing": final_routing,
            "assessment": structured.get("assessment", ""),
            "immediate_actions": structured.get("immediate_actions", []),
            "crucial_warnings": structured.get("crucial_warnings", []),
            "resource_recommendations": structured.get("resource_recommendations", []),
            "required_follow_up": structured.get("required_follow_up", []),
            "assumptions": structured.get("assumptions", []),
            "what_to_do": structured.get("what_to_do", []),
            "what_not_to_do": structured.get("what_not_to_do", []),
            "likely_conditions": structured.get("likely_conditions", []),
            "red_flags": structured.get("red_flags", []),
            "reasoning": structured.get("reasoning", state.get("ml_reasoning", "")),
            "confidence": structured.get("confidence", state.get("reasoning_confidence", 0.0)),
            "dataset_used": structured.get("dataset_used", False),
            "reasoning_confidence": state.get("reasoning_confidence", 0.0),
            "compliance_passed": state.get("compliance_passed", True),
            "metadata": {
                "audit_hash": audit_hash,
                "symptoms": state.get("symptoms", []),
                "duration": state.get("duration"),
                "severity": state.get("severity"),
                "scratchpad": state.get("scratchpad"),
                "consultation": state.get("consultation_result"),
                "disease_info": state.get("disease_info"),
            },
        },
        "audit_hash": audit_hash,
    }


async def persist_node(state: TriageState) -> dict:
    """No-op persist — chat storage removed in slimmed-down build."""
    return {}
