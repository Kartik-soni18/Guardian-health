"""
Compliance Reviewer — Post-processes triage output for safety compliance.

Checks for:
- Definitive diagnosis language
- Specific drug/dosage recommendations
- Unsafe self-treatment advice

Disclaimers are shown once in the app footer — do not append them to LLM responses.
"""


import logging
import re
from typing import Any

logger = logging.getLogger("guardian.compliance")

# ---------------------------------------------------------------------------
# Compliance regex patterns
# ---------------------------------------------------------------------------
DIAGNOSIS_PATTERNS = [
    re.compile(r"\byou have\s+([A-Z][a-zA-Z\s]+)", re.IGNORECASE),
    re.compile(r"\byour diagnosis is\b", re.IGNORECASE),
    re.compile(r"\bthis is\s+(?:a\s+)?([A-Z][a-zA-Z\s]+)\b", re.IGNORECASE),
    re.compile(r"\byou (?:are|were) diagnosed with\b", re.IGNORECASE),
    re.compile(r"\bdefinite(?:ly)?\s+(?:have|has)\b", re.IGNORECASE),
    re.compile(r"\bthis confirms\b", re.IGNORECASE),
]

DRUG_DOSAGE_PATTERNS = [
    re.compile(r"\btake\s+\d+\s*(?:mg|mcg|g|ml)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*(?:mg|mcg|g|ml)\s+(?:of\s+)?[a-zA-Z]+\b", re.IGNORECASE),
    re.compile(r"\bprescrib(?:e|ing|ed)\b", re.IGNORECASE),
    re.compile(r"\bdosage:\s*\d+", re.IGNORECASE),
    re.compile(r"\btake\s+(?:one|two|three|1|2|3)\s+(?:pill|tablet|capsule)", re.IGNORECASE),
]

SELF_TREATMENT_PATTERNS = [
    re.compile(r"\b(?:just|simply)\s+wait\s+it\s+out\b", re.IGNORECASE),
    re.compile(r"\bno\s+need\s+(?:to|for)\s+(?:see|visit|consult)\b", re.IGNORECASE),
    re.compile(r"\b(?:ignore|don't worry about)\s+(?:the\s+)?symptoms?\b", re.IGNORECASE),
    re.compile(r"\bit will go away on its own\b", re.IGNORECASE),
]

BLOCKED_PHRASES = [
    "experimental treatment",
    "not approved by fda",
    "miracle cure",
    "guaranteed to cure",
    "alternative to vaccination",
]


def _check_patterns(text: str, patterns: list[re.Pattern]) -> list[str]:
    """Check text against regex patterns, return matched strings."""
    matches = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            matched_text = match.group().strip()
            if matched_text and matched_text not in matches:
                matches.append(matched_text)
    return matches


def _check_blocked_phrases(text: str) -> list[str]:
    """Check for explicitly blocked phrases."""
    found = []
    lowered = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in lowered:
            found.append(phrase)
    return found


def compliance_review(triage_result: dict[str, Any]) -> dict[str, Any]:
    """
    Review triage/consultation output for compliance violations.

    Args:
        triage_result: Dict containing response text and metadata.

    Returns:
        {
            "approved": bool,
            "final_response": str (modified if needed),
            "blocked_reason": str | None,
            "violations": list[str],
            "modifications_made": list[str],
        }
    """
    if triage_result.get("response_mode") == "follow_up":
        response_text = triage_result.get("response_text", "")
        return {
            "approved": True,
            "final_response": response_text,
            "blocked_reason": None,
            "violations": [],
            "modifications_made": [],
        }

    response_text = triage_result.get("response_text", "")
    if not response_text:
        # Build from structured fields if available
        parts = []
        if "explanation" in triage_result:
            parts.append(triage_result["explanation"])
        if "action" in triage_result:
            parts.append(triage_result["action"])
        if "assessment" in triage_result:
            parts.append(triage_result["assessment"])
        response_text = " ".join(parts)

    violations: list[str] = []
    modifications: list[str] = []

    # Check for definitive diagnosis language
    diag_matches = _check_patterns(response_text, DIAGNOSIS_PATTERNS)
    if diag_matches:
        violations.append(f"Definitive diagnosis language detected: {diag_matches}")
        modifications.append("Added clarification that no definitive diagnosis is being made.")

    # Check for drug/dosage recommendations
    drug_matches = _check_patterns(response_text, DRUG_DOSAGE_PATTERNS)
    if drug_matches:
        violations.append(f"Specific drug/dosage recommendation detected: {drug_matches}")
        modifications.append("Removed specific dosing; added consult-provider warning.")

    # Check for unsafe self-treatment advice
    self_tx_matches = _check_patterns(response_text, SELF_TREATMENT_PATTERNS)
    if self_tx_matches:
        violations.append(f"Potentially unsafe self-treatment advice: {self_tx_matches}")
        modifications.append("Softened language to encourage professional consultation.")

    # Check blocked phrases
    blocked_found = _check_blocked_phrases(response_text)
    if blocked_found:
        violations.append(f"Blocked phrases detected: {blocked_found}")

    # Determine approval
    approved = True
    blocked_reason = None

    if blocked_found:
        approved = False
        blocked_reason = f"Blocked phrases detected: {blocked_found}"
    elif len(violations) >= 3:
        approved = False
        blocked_reason = f"Multiple compliance violations ({len(violations)}): {violations[:2]}..."

    # Build final response with modifications
    final_response = response_text

    if diag_matches and approved:
        final_response += (
            "\n\nPlease note: I cannot provide a definitive diagnosis based on symptoms alone. "
            "A healthcare professional can evaluate you fully and provide an accurate diagnosis."
        )

    if drug_matches and approved:
        final_response += (
            "\n\nAlways consult with your healthcare provider before starting, stopping, or changing any medication."
        )

    if self_tx_matches and approved:
        final_response = final_response.replace(
            "just wait it out",
            "monitor your symptoms and seek medical advice if they persist or worsen",
        )
        final_response = final_response.replace(
            "it will go away on its own",
            "many conditions improve with time, but consult a healthcare provider if symptoms persist",
        )

    logger.info(
        "Compliance review: approved=%s violations=%d modifications=%d",
        approved,
        len(violations),
        len(modifications),
    )

    return {
        "approved": approved,
        "final_response": final_response,
        "blocked_reason": blocked_reason,
        "violations": violations,
        "modifications_made": modifications,
    }
