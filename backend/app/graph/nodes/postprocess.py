"""Post-processing nodes: compliance, response assembly, persistence."""

import hashlib
import json
import logging
import uuid
from datetime import datetime

from app.graph.state import TriageState
from app.compliance_agent import review as compliance_review
from app import db

logger = logging.getLogger(__name__)


def compliance_node(state: TriageState) -> dict:
    """Audit triage output for prohibited language."""
    triage_result = state.get("triage_result")
    if not triage_result:
        return {"compliance_passed": True, "compliance_note": None}

    audit = compliance_review(triage_result)
    logger.info("[Graph] compliance approved=%s", audit.get("approved"))
    return {
        "compliance_passed": audit.get("approved", True),
        "compliance_note": audit.get("blocked_reason"),
    }


def assembler_node(state: TriageState) -> dict:
    """Assemble the final response from all graph outputs."""
    status = state.get("status")
    error = state.get("error")
    rejection_reason = state.get("rejection_reason")
    emergency_detected = state.get("emergency_detected", False)
    final_routing = state.get("final_routing")
    triage_result = state.get("triage_result")
    disease_info = state.get("disease_info")
    ml_prediction = state.get("ml_prediction")
    ml_confidence = state.get("ml_confidence", 0.0)
    symptoms = state.get("symptoms", [])
    duration = state.get("duration")
    severity = state.get("severity")
    privacy_block = state.get("privacy_block")
    scratchpad = state.get("scratchpad")
    ml_reasoning = state.get("ml_reasoning")
    discrepancy_note = state.get("discrepancy_note")
    compliance_note = state.get("compliance_note")
    consultation_result = state.get("consultation_result")

    # Helper to map triage level strings to frontend-friendly slugs
    def _map_triage_level(level: str) -> str:
        level = (level or "").lower()
        if "emergency" in level:
            return "emergency"
        if "urgent" in level:
            return "urgent"
        if "self-care" in level or "self care" in level:
            return "self_care"
        return "moderate"

    # Build human-readable response text based on status
    response_text = ""

    # Handle errors / rejections first
    if error:
        response = {"error": error, "status": 400}
        response_text = f"Error: {error}"
    elif rejection_reason:
        response = {"status": "rejected", "reason": rejection_reason}
        response_text = "I'm designed to assist with health-related questions only."
    elif emergency_detected:
        response_text = (
            "⚠️ Your description contains signs that may indicate a medical emergency. "
            "Please call emergency services (911) or go to the nearest Emergency Room immediately. "
            "Do not wait."
        )
        response = {
            "status": "emergency",
            "message": response_text,
            "symptoms": symptoms,
            "disclaimer": "⚠️ This is an AI-assisted assessment only. Seek emergency care now and consult a licensed healthcare professional.",
        }
    elif final_routing == "diagnosed" and disease_info is not None:
        disease_name = ml_prediction.get("disease") if ml_prediction else "General Assessment"
        conf_pct = ml_prediction.get("confidence_pct", "0%") if ml_prediction else "0%"
        response_text = f"{disease_name} detected with {conf_pct} confidence. Please consult a doctor for confirmation."
        # Diagnosed path
        response = {
            "status": "diagnosed",
            "disease": {
                "name": disease_name,
                "confidence": ml_confidence,
                "confidence_pct": conf_pct,
                "all_predictions": ml_prediction.get("top_3", []) if ml_prediction else [],
            },
            "care": disease_info,
            "symptoms": symptoms,
            "duration": duration,
            "severity": severity,
            "disclaimer": "⚠️ This is an AI-assisted assessment only. It is NOT a medical diagnosis. Always consult a licensed healthcare professional before making any medical decisions.",
        }
        # Flattened fields for frontend convenience
        response["disease_name"] = disease_name
        response["confidence"] = ml_confidence
        response["all_predictions"] = response["disease"]["all_predictions"]
        response["care_advice"] = disease_info.get("self_care", "") if isinstance(disease_info, dict) else ""
        response["otc_products"] = disease_info.get("otc_products", []) if isinstance(disease_info, dict) else []
        if compliance_note:
            response["compliance_note"] = compliance_note
    elif triage_result is not None:
        level = triage_result.get("level", "")
        reasoning = triage_result.get("reasoning", "")
        response_text = f"{level}: {reasoning}" if reasoning else level
        # Triage path (including post-consultation)
        response = {
            "status": "triage",
            "triage": triage_result,
            "care": disease_info or {},
            "symptoms": symptoms,
        }
        # Flattened fields for frontend convenience
        response["triage_level"] = _map_triage_level(level)
        response["reasoning"] = reasoning
        response["red_flags"] = triage_result.get("red_flags", [])
        response["remedies"] = triage_result.get("remedies", [])
        response["care_advice"] = (disease_info or {}).get("self_care", "") if isinstance(disease_info, dict) else ""
        response["otc_products"] = (disease_info or {}).get("otc_products", []) if isinstance(disease_info, dict) else []
    elif consultation_result is not None and not consultation_result.get("ready_for_triage"):
        follow_msg = consultation_result.get("follow_up_message") or "Could you tell me more about your symptoms?"
        response_text = follow_msg
        # Follow-up path
        response = {
            "status": "follow_up",
            "message": follow_msg,
            "gathered_context": consultation_result.get("gathered_context", ""),
            "top_candidates": consultation_result.get("top_candidates", []),
            "current_symptoms": symptoms,
        }
    else:
        response_text = "Unable to process request."
        response = {
            "status": "error",
            "error": "Unable to process request.",
        }

    # Attach human-readable response text
    response["response"] = response_text

    # Attach privacy + supervisor notes
    response["privacy"] = privacy_block or {"pii_detected": False, "message": "No PII detected."}
    response["supervisor_notes"] = {
        "scratchpad": scratchpad,
        "ml_reasoning": ml_reasoning,
        "discrepancy": discrepancy_note,
    }

    # Add audit block
    response["audit"] = {
        "interaction_id": str(uuid.uuid4()),
        "audit_hash": hashlib.sha256(
            json.dumps(response, sort_keys=True, default=str).encode()
        ).hexdigest(),
    }

    return {"response_data": response}


async def persist_node(state: TriageState) -> dict:
    """Persist interaction to MongoDB if user and chat_id are present."""
    user = state.get("user")
    chat_id = state.get("chat_id")
    user_query = state.get("user_input", "")
    response_data = state.get("response_data", {})
    symptoms = state.get("symptoms", [])

    if chat_id and user:
        try:
            chats_coll = await db.get_chats_collection()
            await chats_coll.update_one(
                {"chat_id": chat_id, "user_id": user["id"]},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                {"role": "user", "content": user_query, "timestamp": datetime.utcnow()},
                                {"role": "assistant", "content": response_data, "timestamp": datetime.utcnow()},
                            ]
                        }
                    },
                    "$set": {
                        "last_updated": datetime.utcnow(),
                        "symptoms": symptoms,
                        "status": response_data.get("status"),
                    },
                    "$setOnInsert": {
                        "title": user_query[:50] + "..." if len(user_query) > 50 else user_query,
                        "created_at": datetime.utcnow(),
                    },
                },
                upsert=True,
            )
            logger.info("[Graph] persisted chat_id=%s", chat_id)
        except Exception as exc:
            logger.warning("[Graph] persist failed: %s", exc)

    return {"response_data": response_data}
