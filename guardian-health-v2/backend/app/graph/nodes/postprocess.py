"""
Post-processing nodes: compliance, assembler, persist.

- compliance_node: Reviews output for safety compliance.
- assembler_node: Builds final response with audit metadata.
- persist_node: Saves to DynamoDB.
"""


import hashlib
import json
import logging
import os
import time
from typing import Any

import aioboto3

from app.agents.compliance import compliance_review
from app.graph.state import TriageState

logger = logging.getLogger("guardian.nodes.postprocess")

# ---------------------------------------------------------------------------
# DynamoDB configuration
# ---------------------------------------------------------------------------
DYNAMODB_TABLE = os.getenv("DYNAMODB_MESSAGES_TABLE", "guardian-messages")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

_dynamodb_resource = None


async def _get_dynamodb_table():
    """Get DynamoDB table resource (singleton pattern)."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        session = aioboto3.Session()
        _dynamodb_resource = await session.resource(
            "dynamodb", region_name=AWS_REGION
        ).__aenter__()
    return await _dynamodb_resource.Table(DYNAMODB_TABLE)


# ---------------------------------------------------------------------------
# Node: compliance
# ---------------------------------------------------------------------------
async def compliance_node(state: TriageState) -> dict:
    """
    Review the generated response for compliance violations.
    """
    if state.get("error") and not state.get("response_text"):
        return {}

    response_text = state.get("response_text", "")
    if not response_text:
        return {}

    # Build triage_result-like dict for compliance review
    review_input = {
        "response_text": response_text,
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
        # Fail-open: add disclaimer and proceed
        safe_response = response_text + (
            "\n\nDisclaimer: This information is for educational purposes only "
            "and does not replace professional medical advice. Always consult a "
            "qualified healthcare provider for personal medical concerns."
        )
        return {
            "compliance_passed": True,
            "compliance_note": f"Compliance review failed: {type(exc).__name__} — added default disclaimer",
            "response_text": safe_response,
        }


# ---------------------------------------------------------------------------
# Node: assembler
# ---------------------------------------------------------------------------
async def assembler_node(state: TriageState) -> dict:
    """
    Assemble the final response with metadata and audit hash.
    """
    if state.get("error") and not state.get("response_text"):
        error_msg = state.get("error", "An unknown error occurred")
        response_data = {
            "response": f"I apologize, but I encountered an issue processing your request: {error_msg}. "
                        f"Please try again or contact support if the problem persists.",
            "triage_level": None,
            "care_setting": None,
            "routing": "error",
            "metadata": {
                "error": error_msg,
                "timestamp": time.time(),
            },
        }
        return {"response_data": response_data}

    # Handle non-medical rejection
    if state.get("is_medical") is False:
        rejection_reason = state.get("rejection_reason", "This query is outside my medical scope.")
        response_data = {
            "response": f"I'm designed to help with health-related questions. {rejection_reason} "
                        f"Please ask me about symptoms, conditions, or health concerns.",
            "triage_level": None,
            "care_setting": None,
            "routing": "rejected",
            "metadata": {
                "rejection_category": state.get("rejection_category"),
                "timestamp": time.time(),
            },
        }
        return {"response_data": response_data}

    response_text = state.get("response_text", "")
    triage_result = state.get("triage_result", {})
    consultation_result = state.get("consultation_result", {})
    disease_info = state.get("disease_info", {})

    # Determine routing and level
    final_routing = state.get("final_routing", "unknown")
    triage_level = triage_result.get("level") if triage_result else None
    care_setting = triage_result.get("care_setting") if triage_result else None

    # Build audit hash
    audit_payload = {
        "user_id": state.get("user_id"),
        "chat_id": state.get("chat_id"),
        "symptoms": state.get("symptoms", []),
        "triage_level": triage_level,
        "routing": final_routing,
        "ml_confidence": state.get("ml_confidence", 0.0),
        "timestamp": time.time(),
    }
    audit_str = json.dumps(audit_payload, sort_keys=True, default=str)
    audit_hash = hashlib.sha256(audit_str.encode()).hexdigest()[:16]

    response_data = {
        "response": response_text,
        "triage_level": triage_level,
        "care_setting": care_setting,
        "routing": final_routing,
        "ml_confidence": state.get("ml_confidence", 0.0),
        "reasoning_confidence": state.get("reasoning_confidence", 0.0),
        "compliance_passed": state.get("compliance_passed", True),
        "metadata": {
            "audit_hash": audit_hash,
            "symptoms": state.get("symptoms", []),
            "duration": state.get("duration"),
            "severity": state.get("severity"),
            "emergency_detected": state.get("emergency_detected", False),
            "ml_prediction": state.get("ml_prediction"),
            "scratchpad": state.get("scratchpad"),
            "consultation": consultation_result,
            "disease_info": disease_info,
            "timestamp": time.time(),
        },
    }

    return {
        "response_data": response_data,
        "audit_hash": audit_hash,
    }


# ---------------------------------------------------------------------------
# Node: persist
# ---------------------------------------------------------------------------
async def persist_node(state: TriageState) -> dict:
    """
    Persist chat message to DynamoDB.
    """
    chat_id = state.get("chat_id")
    user_id = state.get("user_id")
    response_data = state.get("response_data")

    if not chat_id or not user_id or not response_data:
        logger.warning("Persist node: missing chat_id, user_id, or response_data — skipping")
        return {}

    try:
        table = await _get_dynamodb_table()
        timestamp = time.time()
        message_id = f"msg_{int(timestamp * 1000)}"

        item = {
            "PK": f"CHAT#{chat_id}",
            "SK": f"MSG#{message_id}",
            "user_id": user_id,
            "chat_id": chat_id,
            "message_id": message_id,
            "user_input": state.get("user_input", ""),
            "response": response_data.get("response", ""),
            "triage_level": response_data.get("triage_level"),
            "routing": response_data.get("routing"),
            "ml_confidence": response_data.get("ml_confidence"),
            "audit_hash": state.get("audit_hash"),
            "symptoms": state.get("symptoms", []),
            "timestamp": timestamp,
            "ttl": int(timestamp) + 90 * 24 * 3600,  # 90-day TTL
        }

        await table.put_item(Item=item)
        logger.info("Persisted message %s to chat %s", message_id, chat_id)

        return {
            "persisted": True,
            "message_id": message_id,
        }

    except Exception as exc:
        logger.error("Persist node DynamoDB error: %s", exc)
        # Don't fail the pipeline on persistence errors
        return {
            "persisted": False,
            "error": f"Persistence failed: {type(exc).__name__}",
        }
