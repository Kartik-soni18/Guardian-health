"""Pre-processing nodes: input validation, firewall, privacy scrubbing."""

import logging

from app.graph.state import TriageState
from app.medical_firewall import gate as firewall_gate
from app.privacy_proxy import scrub_pii

logger = logging.getLogger(__name__)

_FORCE_PHRASES = [
    "that's it", "thats it", "just give me", "give me results",
    "i don't have more", "i dont have more", "proceed anyway",
    "just tell me", "no more info",
]


def input_gate_node(state: TriageState) -> dict:
    """Validate input and detect force phrases."""
    user_query = state.get("user_input", "")
    if not user_query or not user_query.strip():
        return {
            "status": "error",
            "error": "Empty query. Please describe your symptoms.",
            "response_data": {"error": "Empty query. Please describe your symptoms.", "status": 400},
        }

    force_used = any(p in user_query.lower() for p in _FORCE_PHRASES)
    logger.info("[Graph] input_gate force_phrase=%s", force_used)
    return {"force_phrase_used": force_used}


def firewall_node(state: TriageState) -> dict:
    """Run medical firewall unless user is forcing results."""
    if state.get("force_phrase_used"):
        logger.info("[Graph] firewall skipped (force phrase)")
        return {}

    user_query = state.get("user_input", "")
    rejection = firewall_gate(user_query)
    if rejection:
        logger.info("[Graph] firewall REJECTED")
        return {
            "status": "rejected",
            "rejection_reason": rejection.get("reason", "non-medical_query"),
            "response_data": rejection,
        }

    logger.info("[Graph] firewall PASSED")
    return {}


def privacy_node(state: TriageState) -> dict:
    """Scrub PII from user input."""
    user_query = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])

    # Build accumulated text (same logic as original supervisor)
    prior_user_text = ""
    for entry in (conversation_history or []):
        if entry.get("role") == "user":
            prior_user_text += entry.get("content", "") + "\n"

    if state.get("force_phrase_used") and prior_user_text.strip():
        proxy_result = scrub_pii(prior_user_text.strip())
        accumulated_text = proxy_result["scrubbed_text"]
    else:
        proxy_result = scrub_pii(user_query)
        accumulated_text = prior_user_text + proxy_result["scrubbed_text"]

    logger.info("[Graph] privacy pii_detected=%s", proxy_result["pii_detected"])
    return {
        "scrubbed_input": proxy_result["scrubbed_text"],
        "pii_detected": proxy_result["pii_detected"],
        "privacy_block": {
            "pii_detected": proxy_result["pii_detected"],
            "message": "PII redacted." if proxy_result["pii_detected"] else "No PII detected.",
        },
        "_accumulated_text": accumulated_text,  # ephemeral, used by next node
    }
