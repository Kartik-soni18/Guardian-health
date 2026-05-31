"""
Standalone async path tester for GuardianHealth backend.
Tests every routing path without modifying any app code.
Run: source venv/bin/activate && python3 run_path_tests.py
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from app.graph import get_triage_graph
from app.graph.state import TriageState

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"
INFO = "\033[94m INFO\033[0m"

results = []


def check(name, condition, actual=None):
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}")
    if not condition and actual is not None:
        print(f"         got: {json.dumps(actual, default=str)[:200]}")
    results.append((name, condition))


async def run(label, query, history=None):
    print(f"\n{'='*60}")
    print(f" PATH: {label}")
    print(f" Query: {query!r}")
    print(f"{'='*60}")
    try:
        graph = get_triage_graph()
        state: TriageState = {
            "user_input": query,
            "user": None,
            "chat_id": None,
            "conversation_history": history or [],
        }
        final = await graph.ainvoke(state)
        result = final.get("response_data", {})
        print(f" Status: {result.get('status')}")
        return result
    except Exception as exc:
        print(f"  [{FAIL}] EXCEPTION: {exc}")
        results.append((label, False))
        return {}


async def main():
    # ── 1. Non-medical firewall ───────────────────────────────────────
    r = await run("Firewall — non-medical query", "What is the capital of France?")
    check("Blocked with status 400", r.get("status") == 400, r.get("status"))
    check("Error message present", bool(r.get("error")))

    # ── 2. Empty query ────────────────────────────────────────────────
    r = await run("Edge case — empty query", "   ")
    check("Returns status 400", r.get("status") == 400, r.get("status"))

    # ── 3. Emergency path ─────────────────────────────────────────────
    r = await run("Emergency path", "I can't breathe and I'm losing consciousness.")
    check("Status = emergency", r.get("status") == "emergency", r.get("status"))
    check("Emergency message present", "emergency" in r.get("message", "").lower() or "911" in r.get("message", ""))
    check("Privacy block present", "privacy" in r)

    # ── 4. PII detection ──────────────────────────────────────────────
    r = await run("Privacy — PII in query", "My name is John Smith and I have a headache.")
    check("PII detected", r.get("privacy", {}).get("pii_detected") is True, r.get("privacy"))

    # ── 5. Clean query (no PII) ───────────────────────────────────────
    r = await run("Privacy — clean query", "I have a mild headache and feel tired.")
    check("No PII detected", r.get("privacy", {}).get("pii_detected") is False, r.get("privacy"))

    # ── 6. Consultation path (vague symptom, low info) ────────────────
    r = await run("Consultation path", "I feel unwell.")
    check("Status is follow_up or triage", r.get("status") in ("follow_up", "triage", "diagnosed"), r.get("status"))
    check("Privacy block present", "privacy" in r)

    # ── 7. Diagnosed or triage path (rich symptoms) ───────────────────
    r = await run("Rich symptoms — diagnosed or triage", "I have had fever, chills, body ache, and runny nose for 3 days. Severity is moderate.")
    check("Status is diagnosed or triage", r.get("status") in ("diagnosed", "triage"), r.get("status"))
    check("Symptoms extracted", len(r.get("symptoms", [])) > 0, r.get("symptoms"))
    if r.get("status") == "diagnosed":
        check("Disease name present", bool(r.get("disease", {}).get("name")))
        check("Confidence present", r.get("disease", {}).get("confidence") is not None)
        check("Care info present", bool(r.get("care")))
        check("Disclaimer present", bool(r.get("disclaimer")))
    if r.get("status") == "triage":
        triage = r.get("triage", {})
        check("Triage level present", triage.get("level") in ("Self-Care", "Urgent Care", "Emergency Room"), triage.get("level"))
        check("Disclaimer in triage", bool(triage.get("disclaimer") or "consult" in triage.get("reasoning", "").lower()))

    # ── 8. Self-care triage (minor symptom) ───────────────────────────
    r = await run("Self-care — minor cut", "I have a small cut on my finger, it stopped bleeding.")
    check("Not an emergency", r.get("status") != "emergency", r.get("status"))
    if r.get("status") == "triage":
        level = r.get("triage", {}).get("level")
        check("Level is Self-Care", level == "Self-Care", level)

    # ── 9. Urgent care / ER — chest pain ─────────────────────────────
    r = await run("Urgent/ER — chest pain", "I have severe chest pain and shortness of breath for the past hour.")
    check("Not blocked", r.get("status") != 400, r.get("status"))
    if r.get("status") == "triage":
        level = r.get("triage", {}).get("level")
        check("Level is Urgent Care or ER", level in ("Urgent Care", "Emergency Room"), level)

    # ── 10. Force-phrase path ─────────────────────────────────────────
    history = [
        {"role": "user", "content": "I have a headache."},
        {"role": "assistant", "content": "Can you tell me more?"},
        {"role": "user", "content": "It's been 2 days, moderate."},
    ]
    r = await run("Force-phrase path", "just give me results", history=history)
    check("Bypasses consultation", r.get("status") in ("triage", "diagnosed", "emergency"), r.get("status"))
    check("Supervisor notes present", "supervisor_notes" in r)

    # ── 11. Compliance — no diagnosis language ────────────────────────
    r = await run("Compliance — fever query", "I have a high fever and chills for 2 days.")
    if r.get("status") in ("diagnosed", "triage"):
        reasoning = ""
        if r.get("status") == "triage":
            reasoning = r.get("triage", {}).get("reasoning", "").lower()
        elif r.get("status") == "diagnosed":
            care = r.get("care", {})
            reasoning = str(care).lower()
        banned = ["you have", "diagnosis is", "you are suffering from"]
        violations = [p for p in banned if p in reasoning]
        check("No prohibited diagnosis phrases", len(violations) == 0, violations)

    # ── 12. Compliance — disclaimer present ───────────────────────────
    graph = get_triage_graph()
    for query in ["I have a headache.", "My stomach hurts.", "I have chest pain."]:
        state: TriageState = {
            "user_input": query,
            "user": None,
            "chat_id": None,
            "conversation_history": [],
        }
        final = await graph.ainvoke(state)
        r2 = final.get("response_data", {})
        triage = r2.get("triage", {})
        disclaimer = triage.get("disclaimer", "") or r2.get("disclaimer", "")
        reasoning = triage.get("reasoning", "").lower()
        has_disclaimer = bool(disclaimer) or "consult" in reasoning or "professional" in reasoning
        check(f"Disclaimer present for: '{query}'", has_disclaimer, {"disclaimer": disclaimer, "reasoning": reasoning[:80]})

    # ── SUMMARY ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    colour = "\033[92m" if passed == total else "\033[91m"
    print(f" {colour}RESULT: {passed}/{total} checks passed\033[0m")
    print(f"{'='*60}")

    failed = [(n, ok) for n, ok in results if not ok]
    if failed:
        print("\n Failed checks:")
        for name, _ in failed:
            print(f"  - {name}")


asyncio.run(main())
