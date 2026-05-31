"""
healthcare_tools.py — Native Python Implementation of Healthcare Tools
─────────────────────────────────────────────────────────────────────
Replaces the Suncture Healthcare MCP server with a native Python module.
Provides:
- find_disease_info(condition: str)
- check_symptoms(symptoms: list, duration: str, severity: str, age: int, sex: str)
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# --- Data from Suncture Healthcare MCP ---
DISEASE_DATA = {
    "common cold": {
        "name": "Common Cold",
        "symptoms": ["Runny or stuffy nose", "Sore throat", "Cough", "Congestion", "Slight body aches", "Mild headache", "Sneezing", "Low-grade fever", "Generally feeling unwell"],
        "overview": "The common cold is a viral infection of your nose and throat. It's usually harmless, although it might not feel that way. Many types of viruses can cause a common cold.",
        "treatment": "There's no cure for the common cold. Antibiotics are of no use against cold viruses. Treatment includes rest, fluids, and over-the-counter medicines to relieve symptoms.",
        "prevention": "Wash your hands frequently, avoid close contact with sick people, don't touch your face with unwashed hands, and strengthen your immune system with a healthy diet and exercise."
    },
    "influenza": {
        "name": "Influenza (Flu)",
        "symptoms": ["Fever over 100.4°F (38°C)", "Aching muscles", "Chills and sweats", "Headache", "Dry, persistent cough", "Shortness of breath", "Tiredness and weakness", "Runny or stuffy nose", "Sore throat", "Eye pain", "Vomiting and diarrhea (more common in children)"],
        "overview": "Influenza is a viral infection that attacks your respiratory system — your nose, throat and lungs. Influenza is commonly called the flu.",
        "treatment": "Rest and fluids are essential. Antiviral medications may be prescribed to shorten the duration and reduce severity, especially for high-risk individuals.",
        "prevention": "Annual flu vaccination, washing hands regularly, avoiding close contact with sick people, and maintaining good health habits."
    },
    "hypertension": {
        "name": "Hypertension (High Blood Pressure)",
        "symptoms": ["Most people have no symptoms; a few may experience headaches", "Shortness of breath", "Nosebleeds", "Visual changes"],
        "overview": "Hypertension is a common condition in which the long-term force of the blood against your artery walls is high enough that it may eventually cause health problems, such as heart disease.",
        "treatment": "Lifestyle changes, including diet, exercise, stress management, and limiting alcohol and tobacco. Medications may be prescribed when lifestyle changes aren't enough.",
        "prevention": "Maintain a healthy weight, exercise regularly, eat a diet rich in fruits, vegetables, and low-fat dairy, limit sodium intake, limit alcohol consumption, avoid smoking, and manage stress."
    },
    "diabetes": {
        "name": "Diabetes Mellitus",
        "symptoms": ["Increased thirst", "Frequent urination", "Extreme hunger", "Unexplained weight loss", "Fatigue", "Irritability", "Blurred vision", "Slow-healing sores", "Frequent infections"],
        "overview": "Diabetes is a disease that occurs when your blood glucose (blood sugar) is too high. Blood glucose is your main source of energy and comes from the food you eat. Insulin helps glucose get into your cells to be used for energy.",
        "treatment": "Type 1 diabetes requires insulin therapy. Type 2 diabetes can be managed with lifestyle changes, oral medications, and sometimes insulin. Regular blood sugar monitoring is essential.",
        "prevention": "Type 1 diabetes cannot be prevented. Type 2 diabetes can often be prevented or delayed by maintaining a healthy weight, engaging in regular physical activity, and eating a balanced diet."
    },
    "asthma": {
        "name": "Asthma",
        "symptoms": ["Shortness of breath", "Chest tightness or pain", "Wheezing when exhaling", "Trouble sleeping caused by shortness of breath", "Coughing or wheezing attacks worsened by respiratory virus"],
        "overview": "Asthma is a condition in which your airways narrow and swell and may produce extra mucus. This can make breathing difficult and trigger coughing, a whistling sound (wheezing) when you breathe out and shortness of breath.",
        "treatment": "Long-term control and quick-relief medications, breathing exercises, and avoiding triggers. An asthma action plan is important for managing the condition.",
        "prevention": "While there's no way to prevent asthma, you can reduce asthma attacks by avoiding triggers, getting vaccinated for influenza and pneumonia, and working with your doctor to identify and treat attacks early."
    }
}

# --- Symptom Checker Logic ---
EMERGENCY_SYMPTOMS = [
    "chest pain", "shortness of breath", "difficulty breathing", 
    "sudden numbness", "paralysis", "difficulty speaking", 
    "sudden severe headache", "head injury", "uncontrollable bleeding",
    "severe abdominal pain", "coughing up blood", "vomiting blood",
    "suicidal thoughts", "seizure", "unconsciousness", "severe burn"
]

SYMPTOM_MAP = {
    "fever": ["common cold", "influenza", "covid-19", "infection"],
    "cough": ["common cold", "influenza", "covid-19", "asthma", "allergies"],
    "headache": ["tension headache", "migraine", "dehydration", "stress", "influenza"],
    "fatigue": ["depression", "anemia", "sleep disorder", "influenza", "hypothyroidism"],
    "sore throat": ["common cold", "influenza", "strep throat", "allergies"],
    "runny nose": ["common cold", "allergies", "influenza"],
    "stuffy nose": ["common cold", "allergies", "influenza"],
    "body aches": ["influenza", "fibromyalgia", "common cold"],
    "nausea": ["food poisoning", "migraine", "anxiety", "pregnancy", "motion sickness"],
    "vomiting": ["food poisoning", "gastroenteritis", "migraine", "pregnancy"],
    "diarrhea": ["food poisoning", "gastroenteritis", "irritable bowel syndrome"],
    "rash": ["allergic reaction", "eczema", "psoriasis", "chickenpox", "contact dermatitis"],
    "abdominal pain": ["gastroenteritis", "appendicitis", "irritable bowel syndrome", "menstrual cramps"],
    "joint pain": ["arthritis", "injury", "influenza", "lyme disease", "gout"],
    "dizziness": ["vertigo", "inner ear infection", "anemia", "dehydration", "anxiety"],
    "chest tightness": ["asthma", "anxiety", "pneumonia", "bronchitis"],
    "sneezing": ["common cold", "allergies", "influenza"],
    "wheezing": ["asthma", "bronchitis", "allergic reaction"],
    "itching": ["allergic reaction", "eczema", "psoriasis", "contact dermatitis"],
    "swelling": ["injury", "allergic reaction", "infection", "arthritis"],
    "shortness of breath": ["asthma", "anxiety", "pneumonia", "bronchitis", "covid-19"],
    "back pain": ["muscle strain", "herniated disc", "arthritis", "kidney infection"],
    "high blood pressure": ["hypertension", "anxiety", "pre-eclampsia"],
    "high blood sugar": ["diabetes", "prediabetes"]
}

# --- Core Tools (Python Native) ---

def find_disease_info(condition: str) -> Optional[str]:
    """Retrieve grounded information about a disease/condition (Native Python)."""
    normalized = condition.lower().strip()
    
    # Check local database
    for key, disease in DISEASE_DATA.items():
        if key in normalized or normalized in key:
            lines = [
                f"# {disease['name']}",
                "",
                "## Overview",
                disease['overview'],
                "",
                "## Symptoms",
                "\n".join(f"- {s}" for s in disease['symptoms']),
                "",
                "## Treatment",
                disease['treatment'],
                "",
                "## Prevention",
                disease['prevention'],
                "",
                "DISCLAIMER: This information is for educational purposes only and is not a substitute for professional medical advice."
            ]
            return "\n".join(lines)
            
    return None

def check_symptoms(
    symptoms: List[str], 
    duration: str = "days", 
    severity: str = "moderate", 
    age: int = 30, 
    sex: str = "male"
) -> Optional[str]:
    """Get a preliminary symptom assessment (Native Python)."""
    normalized = [s.lower().strip() for s in symptoms]
    
    # 1. Emergency Check
    for s in normalized:
        if any(e in s for e in EMERGENCY_SYMPTOMS):
            return (
                "⚠️ EMERGENCY WARNING ⚠️\n\n"
                "The symptoms you've described (including potential signs of emergency) "
                "require immediate medical attention. Please call emergency services (e.g., 911) "
                "or go to the nearest emergency room immediately."
            )
            
    # 2. Match potential conditions
    potential = {}
    for s in normalized:
        matches = SYMPTOM_MAP.get(s, [])
        for m in matches:
            potential[m] = potential.get(m, 0) + 1
            
    top_matches = sorted(potential.items(), key=lambda x: x[1], reverse=True)[:3]
    conditions_str = ", ".join(m[0] for m in top_matches) if top_matches else "undetermined"
    
    # 3. Build advice
    advice = "Rest, stay hydrated, and monitor your symptoms."
    if severity == "severe":
        care_now = "Please seek medical attention promptly today."
    elif duration in ["weeks", "months"]:
        care_now = "Consult with a healthcare provider for a proper evaluation of these persistent symptoms."
    else:
        care_now = "If symptoms worsen or persist beyond a week, consult a healthcare professional."
        
    lines = [
        "# Symptom Assessment (Expert-Grounded)",
        "",
        f"Based on your symptoms ({', '.join(symptoms)}), potential conditions include: {conditions_str}.",
        "",
        "## General Advice",
        advice,
        "",
        "## When to seek care",
        care_now,
        "",
        "IMPORTANT DISCLAIMER: This tool provides general information only and is not a substitute for professional medical advice, diagnosis, or treatment."
    ]
    return "\n".join(lines)
