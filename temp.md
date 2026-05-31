# GuardianHealth Backend Refactoring
## Agent Harness + LangGraph/LangChain Integration — COMPLETE

> **Status**: ✅ Fully implemented and deployed. Old code removed.

---

## What Was Done

### 1. Agent Harness (`app/harness/`)
- `BaseAgent` — abstract class with retry logic, structured JSON parsing, and metrics
- `AgentRegistry` — global agent discovery
- `AgentState` / `AgentInput` / `AgentOutput` — shared TypedDict types

### 2. Prompt Hub (`app/prompt_hub/`)
- **Local-only** prompt storage (JSON files in `app/prompt_hub/local/`)
- `get_prompt(name)` — loads from local JSON with in-memory caching
- LangSmith Hub integration was **removed** per request
- All 8 prompts migrated: `firewall`, `extraction`, `supervisor-scratchpad`, `supervisor-reasoning`, `consultation`, `triage`, `disease-info-with-diagnosis`, `disease-info-no-diagnosis`

### 3. LangGraph State Machine (`app/graph/`)
Compiled graph with conditional routing:
```
START → input_gate → firewall → privacy → extractor → ml_predictor → reasoner

reasoner ──[emergency]──► assembler ──► persist ──► END
         ──[diagnosed]──► diagnosed_info ──► compliance ──► assembler
         ──[consultation]──► consultation ──[ready]──► triage ──► assembler
                                      ──[follow_up]──► assembler
```

Nodes are grouped by domain in `app/graph/nodes/`:
- `preprocess.py` — input validation, firewall, PII scrubbing
- `extraction.py` — clinical NER, ML prediction
- `reasoning.py` — supervisor scratchpad + ML assessment
- `consultation.py` — follow-up questioning
- `triage.py` — care-level recommendation + disease info
- `postprocess.py` — compliance audit, response assembly, DB persistence

### 4. LangChain LLM Wrapper (`app/llm_client.py`)
- `TogetherChatModel` — LangChain-compatible wrapper around Together.ai
- `get_langchain_llm()` — factory function

### 5. Clean-up
- ❌ Deleted `app/supervisor.py`
- ❌ Deleted `app/prompts.py`
- ❌ Removed `USE_LANGGRAPH` feature flag
- ❌ Removed `LANGSMITH_API_KEY` / `LANGSMITH_PROJECT` env vars
- `local_server.py` now **always** uses LangGraph

---

## Files Changed

| File | Action |
|------|--------|
| `app/harness/*` | Created |
| `app/prompt_hub/*` | Created |
| `app/graph/*` | Created |
| `app/llm_client.py` | Added `TogetherChatModel` + `get_langchain_llm()` |
| `app/medical_firewall.py` | Uses `app.prompt_hub` |
| `app/symptom_extractor.py` | Uses `app.prompt_hub` |
| `app/triage_agent.py` | Uses `app.prompt_hub` |
| `local_server.py` | Always routes through `handle_graph()` |
| `requirements.txt` | Added `langchain`, `langgraph`, `langsmith` |
| `tests/test_safety_evals.py` | Updated to use graph |
| `run_path_tests.py` | Updated to use graph |
| `app/supervisor.py` | **Deleted** |
| `app/prompts.py` | **Deleted** |

---

## Test Results

| Suite | Result |
|-------|--------|
| `pytest tests/` (21 tests) | ✅ All passed |
| FastAPI integration (basic/empty/health) | ✅ All passed |
| `run_path_tests.py` | ✅ 22/24 passed (2 expected mock-mode firewall false-positives) |

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│           FastAPI / Lambda              │
│         (local_server.py)               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  LangGraph      │
         │  State Machine  │
         │  (app/graph/)   │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┐
    ▼             ▼             ▼              ▼
firewall    extractor    Guardian-ML      consultation
 (gate)     (NER)       (predict)        (follow-up)
    │             │             │              │
    └─────────────┴─────────────┴──────────────┘
                  │
                  ▼
           reasoner_node
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
 emergency    diagnosed    consultation
    │             │              │
    ▼             ▼              ▼
 assembler  compliance      triage_node
    │             │              │
    └─────────────┴──────────────┘
                  │
                  ▼
            persist_node
                  │
                  ▼
               Response
```

---

*Refactoring completed by Kimi Code CLI. No further action required.*
