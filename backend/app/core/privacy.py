"""Regex-based PII scrubbing for user health queries."""

import logging
import re
from typing import Any

logger = logging.getLogger("guardian.privacy")

PII_PATTERNS: dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "dob": re.compile(r"\b\d{1,2}[\/\-]\d{1,2}[\/\-](?:\d{2}|\d{4})\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "mrn": re.compile(r"\bMRN[\s:#]?(\d{6,10})\b", re.IGNORECASE),
    "name_prefix": re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-zA-Z]+\b"),
}

NAME_PATTERN = re.compile(
    r"\b(my name is|i am|this is)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
    re.IGNORECASE,
)
ADDRESS_PATTERN = re.compile(
    r"\b\d+\s+(?:[A-Za-z]+\s+)*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b",
    re.IGNORECASE,
)

PLACEHOLDERS: dict[str, str] = {
    "ssn": "[SSN_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "email": "[EMAIL_REDACTED]",
    "dob": "[DOB_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "mrn": "[MRN_REDACTED]",
    "name_prefix": "[NAME_REDACTED]",
    "name": "[NAME_REDACTED]",
    "address": "[ADDRESS_REDACTED]",
}


async def scrub_pii(text: str) -> dict[str, Any]:
    """Scrub PII from user text using regex patterns."""
    entities_found: list[dict] = []
    scrubbed = text

    for entity_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(scrubbed):
            placeholder = PLACEHOLDERS[entity_type]
            scrubbed = scrubbed.replace(match.group(), placeholder)
            entities_found.append({
                "type": entity_type,
                "start": match.start(),
                "end": match.end(),
                "value": match.group(),
            })

    for match in NAME_PATTERN.finditer(scrubbed):
        scrubbed = scrubbed.replace(match.group(), f"{match.group(1)} [NAME_REDACTED]")
        entities_found.append({
            "type": "name",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(2),
        })

    for match in ADDRESS_PATTERN.finditer(scrubbed):
        scrubbed = scrubbed.replace(match.group(), "[ADDRESS_REDACTED]")
        entities_found.append({
            "type": "address",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
        })

    method = "regex" if entities_found else "none"
    if entities_found:
        logger.info("Regex scrubbed %d PII entities", len(entities_found))

    return {
        "scrubbed_text": scrubbed,
        "pii_detected": len(entities_found) > 0,
        "entities_found": entities_found,
        "method": method,
    }
