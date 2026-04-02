# 🛡️ GuardianHealth

> **A Serverless, Governance-First Medical Triage Agent**

GuardianHealth is a portfolio-grade, compliance-focused medical triage platform. It demonstrates advanced AI governance techniques including PII scrubbing, a two-agent compliance pipeline, and serverless AWS infrastructure — all at near-zero cost.

---

## ⚙️ Architecture

```
User Browser (React + Vite)
        │
        ▼
  Local FastAPI  ──── (mirrors AWS Lambda for local dev)
  (or API Gateway in production)
        │
        ▼
  Lambda Handler (Python)
  ├── 1. privacy_proxy.py    ← Presidio NER PII scrubber
  ├── 2. knowledge_base.py   ← Mini-RAG: injects medical guidelines
  ├── 3. triage_agent.py     ← Agent A: classifies severity
  ├── 4. compliance_agent.py ← Agent B: blocks diagnoses & Rx
  └── 5. audit_logger.py     ← SHA-256 hash → CloudWatch / stdout
        │
        ▼
  DynamoDB  (session metadata — non-PII)
  CloudWatch  (audit trail)
```

---

## 🚀 Quick Start (Local — No AWS Required)

### 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg   # Presidio NER model
cp .env.example .env
python local_server.py
# → API running at http://localhost:8000
```

### 🩺 Expert Health Tools (Native Python)
The pipeline includes a native Python version of the **Suncture Healthcare tools** for expert-grounded medical information. 
This is self-contained in `backend/app/healthcare_tools.py` and requires no external Node.js server.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
# → App running at http://localhost:5173
```

---

## 🧪 Safety Evaluations
```bash
cd backend
pytest tests/test_safety_evals.py -v
```

Tests verify:
- The agent **refuses** to prescribe specific medications
- Chest pain queries are classified as **Emergency Room**
- PII (names, locations) is **scrubbed** before hitting the AI
- No response contains a definitive **diagnosis** ("You have X")

---

## 🔒 Governance Features

| Feature | Implementation |
|---|---|
| PII Scrubbing | Microsoft Presidio (NER-based) |
| Two-Agent Pattern | Triage Agent → Compliance Review Agent |
| Audit Logging | SHA-256 integrity checks for all clinical interactions. |
| Expert-Grounded Healthcare Tools | Native Python implementation for disease information and symptom checking (replaces the Suncture Healthcare MCP requirement). |
| Grounded Responses | Mini-RAG from medical guidelines JSON |
| Mandatory Disclaimer | Enforced in every response by system prompt |

---

## ☁️ AWS Deployment (Optional)
```bash
cd backend
sam build
sam deploy --guided
```

Deploys: Lambda + API Gateway + DynamoDB + CloudWatch log group.

---

## ⚠️ Disclaimer

GuardianHealth is a **portfolio demonstration project**. It is not a certified medical device and should not be used for actual medical decisions. Always consult a licensed healthcare professional.
