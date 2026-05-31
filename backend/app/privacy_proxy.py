import re
import logging

logger = logging.getLogger(__name__)

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig

    _analyzer = AnalyzerEngine()
    _anonymizer = AnonymizerEngine()
    _PRESIDIO_AVAILABLE = True
except Exception as e:
    _PRESIDIO_AVAILABLE = False
    logger.warning(f"Presidio not available ({e}). Using regex fallback.")

_REGEX_PATTERNS = [
    (r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[NAME]"),
    (r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", "[PHONE]"),
    (r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b", "[EMAIL]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
    (r"\b(?:New York|Los Angeles|Chicago|Houston|Phoenix|"
     r"Philadelphia|San Antonio|San Diego|Dallas|San Jose|"
     r"Austin|Jacksonville|Fort Worth|Columbus|Charlotte|NYC)\b",
     "[LOCATION]"),
]


def scrub_pii(text: str) -> dict:
    original = text
    entities_found = []

    if _PRESIDIO_AVAILABLE:
        try:
            results = _analyzer.analyze(
                text=text,
                entities=["PERSON", "LOCATION", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN"],
                language="en",
            )
            if results:
                entities_found = list({r.entity_type for r in results})
                operators = {
                    "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
                    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
                    "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
                }
                anonymized = _anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
                text = anonymized.text
        except Exception as e:
            logger.warning(f"Presidio scrub failed: {e}. Using regex fallback.")
            text, entities_found = _regex_scrub(text)
    else:
        text, entities_found = _regex_scrub(text)

    return {
        "scrubbed_text": text,
        "pii_detected": text != original or len(entities_found) > 0,
        "entities_found": entities_found,
    }


def _regex_scrub(text: str):
    entities = []
    for pattern, replacement in _REGEX_PATTERNS:
        new_text, n = re.subn(pattern, replacement, text)
        if n > 0:
            entities.append(replacement.strip("[]"))
            text = new_text
    return text, entities
