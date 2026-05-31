# Guardian Health — Security Architecture Overview

A plain-English explanation of the security layers built into this system.

---

## The Big Picture

Every time a user types a symptom or health question, the message passes through **five security checkpoints** before any response is sent back. Think of it like airport security — multiple independent scanners, each checking for a different risk.

---

## Layer 1: Medical Firewall (the Bouncer)

**File:** `backend/app/medical_firewall.py`

Before anything else happens, the system checks: *"Is this even a medical question?"*

An AI classifier reads the user's message and decides whether it's health-related. If someone tries to use the medical chatbot to do something unrelated (or potentially harmful), the request is rejected immediately and never reaches the rest of the system.

- **Why it matters:** Prevents misuse of a medical-grade AI for non-medical purposes.
- **Fail-safe:** If the classifier itself crashes or can't decide, the system defaults to *letting the message through* rather than blocking a patient who might genuinely need help.

---

## Layer 2: Privacy Proxy (the Redactor)

**File:** `backend/app/privacy_proxy.py`

Once a message is confirmed as medical, the system automatically strips out any **personally identifiable information (PII)** before the message is processed.

What gets redacted:
| Detected | Replaced With |
|---|---|
| Full names (e.g. "John Smith") | `[NAME]` |
| Phone numbers | `[PHONE]` |
| Email addresses | `[EMAIL]` |
| Social Security Numbers | `[SSN]` |
| City names | `[LOCATION]` |

It uses two detection methods in order:
1. **Presidio** (Microsoft's enterprise PII detection library) — when available
2. **Regex fallback** — pattern-matching rules, used if Presidio isn't installed

The rest of the system only ever sees the *scrubbed* version of the message. The original is never passed to the AI models.

- **Why it matters:** Patients often accidentally share their name, location, or contact info. This ensures that personal data is never sent to external AI services.

---

## Layer 3: Compliance Agent (the Medical-Legal Filter)

**File:** `backend/app/compliance_agent.py`

After the AI generates a triage response, a compliance check reviews the *output* before it reaches the user. It blocks two categories of content:

**Prohibited diagnosis language** — phrases like:
- "You are diagnosed with..."
- "The diagnosis is..."
- "You're suffering from..."

**Prescription-level medication language** — phrases like:
- "dose of X mg/kg"
- "prescribe you..."
- "prescription only"

If any of these are detected, the response is **replaced entirely** with a safe fallback that directs the user to consult a real healthcare professional.

Every response also gets a mandatory disclaimer appended:
> *"This is an AI-assisted triage suggestion only. It is NOT a medical diagnosis. Always consult a licensed healthcare professional before making any medical decisions."*

- **Why it matters:** It's illegal and dangerous for an AI to make diagnoses or prescribe medication. This layer ensures the system can never accidentally cross that line, even if the underlying AI model tries to.

---

## Layer 4: Authentication & Token Security

**File:** `backend/app/auth.py`

User accounts are protected with:

- **Password hashing** using PBKDF2-SHA256 (a one-way cryptographic function — passwords are never stored in plain text)
- **JWT tokens** for session management — each login produces a signed token that expires after 1 week
- Tokens are validated on every request; invalid or expired tokens are silently rejected

- **Why it matters:** Standard security practice to prevent account takeover even if the database is ever compromised.

---

## Layer 5: Audit Logging (the Paper Trail)

**File:** `backend/tests/test_safety_evals.py` (verified via tests)

Every interaction gets:
- A **unique interaction ID** — so no two sessions can be confused or merged
- An **audit hash** (64-character SHA-256) — a cryptographic fingerprint of the interaction that can detect if logs were tampered with

- **Why it matters:** In healthcare, you need to be able to prove what the system said, to whom, and when. This creates an immutable record.

---

## How the Layers Work Together

```
User Message
     │
     ▼
[1] Medical Firewall ──── non-medical? ──→ REJECTED
     │ (medical)
     ▼
[2] Privacy Proxy ─────── strips PII from message
     │ (scrubbed text)
     ▼
  AI Processing (symptom extraction, ML prediction, triage)
     │ (draft response)
     ▼
[3] Compliance Agent ──── diagnosis/drug language? ──→ REPLACED with safe fallback
     │ (approved response)
     ▼
[5] Audit Hash + ID attached
     │
     ▼
User receives response
```

Authentication (Layer 4) wraps the entire system — only logged-in users can reach any of the above steps.

---

## Safety Tests

**File:** `backend/tests/test_safety_evals.py`

A dedicated test suite verifies that all safety behaviors hold. It checks:

- PII is detected and flagged when a name is present
- Clean queries pass through without false alarms
- Chest pain and breathing difficulty correctly route to **Emergency Room**
- Every response includes a disclaimer
- No response ever contains a direct diagnosis phrase
- No response ever names a specific drug
- Every audit log has a hash and a unique ID

These tests run in mock mode (no real AI calls needed), so they can be run in CI/CD on every code change.

---

## Summary

| Risk | Mitigation |
|---|---|
| Misuse / off-topic queries | Medical Firewall |
| Patient PII leaking to AI models | Privacy Proxy (auto-redaction) |
| AI making illegal medical diagnoses | Compliance Agent (output filter) |
| Unauthorized access | JWT auth + hashed passwords |
| Tampered or disputed logs | Audit hash per interaction |
| Safety regressions in future code | Automated safety test suite |
