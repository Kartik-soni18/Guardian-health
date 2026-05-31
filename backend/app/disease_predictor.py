import os
import json
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ML_MODELS_DIR = os.path.join(_BASE_DIR, "ml_models")

try:
    _best_model = joblib.load(os.path.join(_ML_MODELS_DIR, "best_model.joblib"))
    _label_encoder = joblib.load(os.path.join(_ML_MODELS_DIR, "label_encoder.joblib"))
    with open(os.path.join(_ML_MODELS_DIR, "symptom_cols.json"), "r") as f:
        _symptom_cols = json.load(f)
    _models_loaded = True
    logger.info("ML models loaded successfully")
except Exception as e:
    logger.error(f"Failed to load ML models: {e}")
    _models_loaded = False
    _best_model = _label_encoder = _symptom_cols = None


def predict_disease(symptoms_list: list, verbose: bool = False) -> dict:
    if not _models_loaded:
        return {
            "disease": None,
            "confidence": 0.0,
            "confidence_pct": "0%",
            "top_3": [],
            "unknown_symptoms": symptoms_list,
            "model_status": "not_loaded",
            "error": "ML models not initialized",
        }

    vec = np.zeros(len(_symptom_cols), dtype=int)
    unknown = []

    for sym in symptoms_list:
        sym_clean = sym.strip().lower().replace(' ', '_')
        if sym_clean in _symptom_cols:
            vec[_symptom_cols.index(sym_clean)] = 1
        else:
            unknown.append(sym)

    proba = _best_model.predict_proba([vec])[0]
    pred_id = np.argmax(proba)
    disease = _label_encoder.classes_[pred_id]
    confidence = float(proba[pred_id])

    top3_idx = np.argsort(proba)[::-1][:3]
    top3 = [(str(_label_encoder.classes_[i]), float(proba[i])) for i in top3_idx]

    if verbose:
        logger.info(f"Symptoms: {symptoms_list}, Prediction: {disease}, Confidence: {confidence*100:.1f}%")

    return {
        "disease": disease,
        "confidence": confidence,
        "confidence_pct": f"{confidence*100:.1f}%",
        "top_3": top3,
        "unknown_symptoms": unknown,
        "model_status": "loaded",
    }
