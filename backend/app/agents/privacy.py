"""
Privacy Agent — PII scrubbing for user health queries.

Tries Microsoft Presidio first, falls back to regex-based scrubbing.
Graceful degradation ensures the pipeline never breaks on PII issues.
"""


import logging
import re
from typing import Any

logger = logging.getLogger("guardian.privacy")

# ---------------------------------------------------------------------------
# Regex patterns for fallback PII detection
# ---------------------------------------------------------------------------
PII_PATTERNS: dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "dob": re.compile(r"\b\d{1,2}[\/\-]\d{1,2}[\/\-](?:\d{2}|\d{4})\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "mrn": re.compile(r"\bMRN[\s:#]?(\d{6,10})\b", re.IGNORECASE),
    "name_prefix": re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-zA-Z]+\b"),
}

# Generic name detection (simple heuristic)
NAME_PATTERN = re.compile(r"\b(my name is|i am|this is)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", re.IGNORECASE)
ADDRESS_PATTERN = re.compile(
    r"\b\d+\s+(?:[A-Za-z]+\s+)*(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b",
    re.IGNORECASE,
)

# Placeholder mapping
PLACEHOLDERS: dict[str, str] = {
    "ssn": "[SSN_REDACTED]",
    "phone": "[PHONE_REDACTED]",
    "email": "[EMAIL_REDACTED]",
    "dob": "[DOB_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "mrn": r"[MRN_\1_REDACTED]",
    "name_prefix": "[NAME_REDACTED]",
    "name": "[NAME_REDACTED]",
    "address": "[ADDRESS_REDACTED]",
}


async def scrub_pii(text: str) -> dict[str, Any]:
    """
    Scrub PII from user text.

    Returns:
        {
            "scrubbed_text": str,
            "pii_detected": bool,
            "entities_found": list[dict],
            "method": "presidio" | "regex" | "none"
        }
    """
    entities_found: list[dict] = []
    scrubbed = text
    method = "none"

    # ---- Attempt 1: Presidio ----
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()

        results = analyzer.analyze(text=text, language="en")
        if results:
            anon_result = anonymizer.anonymize(text=text, analyzer_results=results)
            scrubbed = anon_result.text
            entities_found = [
                {"type": r.entity_type, "start": r.start, "end": r.end}
                for r in results
            ]
            method = "presidio"
            logger.info("Presidio scrubbed %d PII entities", len(results))
        else:
            method = "presidio"

        return {
            "scrubbed_text": scrubbed,
            "pii_detected": len(entities_found) > 0,
            "entities_found": entities_found,
            "method": method,
        }

    except ImportError:
        logger.warning("Presidio not installed, falling back to regex PII scrubbing")
    except Exception as exc:
        logger.warning("Presidio failed (%s), falling back to regex", type(exc).__name__)

    # ---- Attempt 2: Regex fallback ----
    method = "regex"

    for entity_type, pattern in PII_PATTERNS.items():
        matches = list(pattern.finditer(scrubbed))
        for match in matches:
            placeholder = PLACEHOLDERS[entity_type]
            if entity_type == "mrn":
                placeholder = f"[MRN_REDACTED]"
            scrubbed = scrubbed.replace(match.group(), placeholder)
            entities_found.append({
                "type": entity_type,
                "start": match.start(),
                "end": match.end(),
                "value": match.group(),
            })

    # Generic name detection
    for match in NAME_PATTERN.finditer(scrubbed):
        scrubbed = scrubbed.replace(match.group(), f"{match.group(1)} [NAME_REDACTED]")
        entities_found.append({
            "type": "name",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(2),
        })

    # Address detection
    for match in ADDRESS_PATTERN.finditer(scrubbed):
        scrubbed = scrubbed.replace(match.group(), "[ADDRESS_REDACTED]")
        entities_found.append({
            "type": "address",
            "start": match.start(),
            "end": match.end(),
            "value": match.group(),
        })

    logger.info("Regex fallback scrubbed %d PII entities", len(entities_found))

    return {
        "scrubbed_text": scrubbed,
        "pii_detected": len(entities_found) > 0,
        "entities_found": entities_found,
        "method": method,
    }
