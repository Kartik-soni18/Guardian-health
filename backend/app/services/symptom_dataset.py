"""Indian healthcare symptom-disease dataset lookup with Redis caching."""

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.cache import cache_get, cache_key, cache_set

logger = logging.getLogger("guardian.symptom_dataset")

DATASET_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "Indian-Healthcare-Symptom-Disease-Dataset.csv"
)

_SEVERITY_SCORE = {"Mild": 0.3, "Moderate": 0.6, "Severe": 0.9}


@dataclass(frozen=True)
class SymptomRecord:
    symptom: str
    possible_diseases: list[str]
    severity: str
    avg_duration_days: int
    region: str
    languages: list[str]


class SymptomDataset:
    def __init__(self) -> None:
        self._records: list[SymptomRecord] = []
        self._index: dict[str, SymptomRecord] = {}
        self._load()

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    def _load(self) -> None:
        if not DATASET_PATH.exists():
            logger.warning("Symptom dataset not found at %s", DATASET_PATH)
            return

        with DATASET_PATH.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                diseases = [
                    d.strip()
                    for d in row.get("Possible Diseases", "").split(",")
                    if d.strip()
                ]
                duration_raw = row.get("Average Duration (days)", "0")
                try:
                    duration = int(float(duration_raw))
                except ValueError:
                    duration = 0

                record = SymptomRecord(
                    symptom=row["Symptom"].strip(),
                    possible_diseases=diseases,
                    severity=row.get("Severity", "Moderate").strip(),
                    avg_duration_days=duration,
                    region=row.get("Common in Region", "Pan-India").strip(),
                    languages=[
                        lang.strip()
                        for lang in row.get("Language Availability", "").split(",")
                        if lang.strip()
                    ],
                )
                self._records.append(record)
                self._index[self._normalize(record.symptom)] = record

        logger.info("Loaded %d symptom records from dataset", len(self._records))

    def _match_record(self, symptom: str) -> SymptomRecord | None:
        normalized = self._normalize(symptom)
        if normalized in self._index:
            return self._index[normalized]

        for key, record in self._index.items():
            if normalized in key or key in normalized:
                return record
        return None

    def lookup(self, symptoms: list[str]) -> dict[str, Any]:
        matches: list[dict[str, Any]] = []
        disease_scores: dict[str, float] = {}

        for symptom in symptoms:
            record = self._match_record(symptom)
            if record is None:
                continue

            sev_score = _SEVERITY_SCORE.get(record.severity, 0.5)
            matches.append({
                "symptom": record.symptom,
                "possible_diseases": record.possible_diseases,
                "severity": record.severity,
                "avg_duration_days": record.avg_duration_days,
                "region": record.region,
                "languages": record.languages,
            })

            for idx, disease in enumerate(record.possible_diseases):
                weight = sev_score * (1.0 - idx * 0.15)
                disease_scores[disease] = max(disease_scores.get(disease, 0.0), weight)

        ranked = sorted(disease_scores.items(), key=lambda item: item[1], reverse=True)
        top_predictions = [
            {"condition": name, "confidence": round(score, 3)}
            for name, score in ranked[:5]
        ]

        confidence = top_predictions[0]["confidence"] if top_predictions else 0.0
        max_severity = "Mild"
        if any(m["severity"] == "Severe" for m in matches):
            max_severity = "Severe"
        elif any(m["severity"] == "Moderate" for m in matches):
            max_severity = "Moderate"

        return {
            "matches": matches,
            "top_predictions": top_predictions,
            "confidence": confidence,
            "max_severity": max_severity,
            "source": "indian_healthcare_dataset",
        }


_dataset: SymptomDataset | None = None


def get_symptom_dataset() -> SymptomDataset:
    global _dataset
    if _dataset is None:
        _dataset = SymptomDataset()
    return _dataset


async def lookup_symptoms(symptoms: list[str]) -> dict[str, Any]:
    normalized = sorted({s.strip().lower() for s in symptoms if s.strip()})
    if not normalized:
        return {
            "matches": [],
            "top_predictions": [],
            "confidence": 0.0,
            "max_severity": "Mild",
            "source": "indian_healthcare_dataset",
        }

    key = cache_key("symptom_lookup", *normalized)
    cached = await cache_get(key)
    if cached is not None:
        return cached

    result = get_symptom_dataset().lookup(symptoms)
    await cache_set(key, result)
    return result
