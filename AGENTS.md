# GuardianHealth — Agent Guide

> **A Serverless, Governance-First Medical Triage Agent**

This file is written for AI coding agents. It contains the factual, project-specific information you need to navigate, modify, and extend this codebase safely.

---

## 1. Project Overview

GuardianHealth is a portfolio-grade medical triage platform. A user describes symptoms in natural language, and the system routes them through a multi-layer governance pipeline:

1. **Medical Firewall** — rejects non-medical queries.
2. **Privacy Proxy** — scrubs PII (names, phones, emails, SSNs, locations) before any AI processing.
3. **Symptom Extractor + ML Predictor** — extracts clinical entities and runs a trained Random Forest classifier.
4. **Supervisor Reasoner** — an LLM reviews the ML output and decides routing (`emergency`, `diagnosed`, `consultation`).
5. **Consultation / Triage / Disease-Info Agents** — generate the clinical response.
6. **Compliance Agent** — blocks prohibited diagnosis language and prescription-level medication advice, and enforces a mandatory disclaimer on every response.
7. **Audit Logger** — attaches a SHA-256 hash and unique interaction ID to every response.

The backend is a **FastAPI** application that can run locally (`uvicorn`) or as an **AWS Lambda** (via Mangum). The frontend is a **React + Vite** single-page app deployed to **GitHub Pages**.

---

## 2. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript 5.9, Vite 7, Tailwind CSS 3, shadcn/ui (Radix + Lucide icons), Framer Motion, Axios |
| Backend Framework | FastAPI 0.111, Uvicorn, Mangum (Lambda adapter) |
| AI / LLM | Together.ai API (`meta-llama/Llama-3.3-70B-Instruct-Turbo` by default), Google Generative AI client, native `httpx` client |
| Agent Orchestration | LangGraph (`langgraph>=0.2.0`) with a compiled `StateGraph` |
| ML | scikit-learn Random Forest, joblib-serialized models, pandas, numpy |
| Database | MongoDB (local dev + production via Atlas), Motor async driver |
| Vector Store | ChromaDB (optional, used for caching PubMed abstracts) |
| Auth | JWT (python-jose), PBKDF2-SHA256 password hashing (passlib) |
| PII Scrubbing | Microsoft Presidio (primary) + regex fallback |
| Pydantic Config | `pydantic-settings` (`app/core/config.py`) |
| MCP | `mcp[cli]>=1.0.0` for the Guardian-ML Model Context Protocol server |
| Infrastructure | AWS Lambda + API Gateway + DynamoDB + CloudWatch (production), Docker Compose (local) |

---

## 3. Repository Layout

```
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI routers (v1 + legacy)
│   │   │   ├── router.py           # Aggregates /v1/* routers
│   │   │   └── v1/
│   │   │       ├── auth.py         # POST /v1/auth/register, /login
│   │   │       ├── chats.py        # GET/DELETE /v1/chats
│   │   │       ├── health.py       # GET /v1/health
│   │   │       └── triage.py       # POST /v1/triage
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic BaseSettings singleton
│   │   │   ├── events.py           # FastAPI lifespan (startup / shutdown)
│   │   │   └── logging.py          # JSON formatter for CloudWatch/ELK
│   │   ├── graph/                  # LangGraph StateGraph
│   │   │   ├── builder.py          # Assembles all nodes and edges
│   │   │   ├── state.py            # TriageState TypedDict
│   │   │   └── nodes/              # 11 graph nodes
│   │   │       ├── preprocess.py   # input_gate, firewall, privacy
│   │   │       ├── extraction.py   # extractor, ml_predictor
│   │   │       ├── reasoning.py    # supervisor scratchpad + reasoning
│   │   │       ├── consultation.py # consultation agent
│   │   │       ├── triage.py       # triage + diagnosed_info
│   │   │       └── postprocess.py  # compliance, assembler, persist
│   │   ├── harness/                # BaseAgent abstraction (not yet wired into graph)
│   │   ├── models/                 # Pydantic request/response models
│   │   ├── prompt_hub/             # Local JSON prompt store (cached in-memory)
│   │   │   └── local/              # firewall.json, extraction.json, triage.json, etc.
│   │   ├── services/               # Business logic layer
│   │   │   ├── auth_service.py     # Password hashing, JWT, user lookup
│   │   │   ├── chat_service.py     # MongoDB chat CRUD
│   │   │   └── triage_service.py   # LangGraph invocation wrapper
│   │   ├── auth.py                 # Legacy auth utilities (still imported)
│   │   ├── compliance_agent.py     # Regex-based output filter
│   │   ├── db.py                   # AsyncIOMotorClient singleton
│   │   ├── disease_predictor.py    # Random Forest disease classifier
│   │   ├── healthcare_tools.py     # Native Python disease-info + symptom checker
│   │   ├── llm_client.py           # Together.ai client + mock mode + LangChain wrapper
│   │   ├── medical_firewall.py     # LLM-based medical query classifier
│   │   ├── ml_mcp_server.py        # MCP server + GuardianMLClient
│   │   ├── privacy_proxy.py        # Presidio + regex PII scrubber
│   │   ├── symptom_extractor.py    # LLM-based clinical entity extraction + keyword fallback
│   │   └── triage_agent.py         # Consultation, triage analysis, disease info
│   ├── data/                       # CSV/JSON data files
│   ├── model/                      # Jupyter-style model training script
│   │   ├── model.py                # Trains & saves Random Forest + artifacts
│   │   └── Training.csv            # Symptom-disease training data
│   ├── app/ml_models/              # Serialized joblib artifacts (loaded at runtime)
│   │   ├── best_model.joblib
│   │   ├── label_encoder.joblib
│   │   └── symptom_cols.json
│   ├── tests/
│   │   └── test_safety_evals.py    # Safety test suite (pytest)
│   ├── local_server.py             # FastAPI entry point + legacy routes + Lambda handler
│   ├── Dockerfile                  # AWS Lambda Python 3.12 image
│   ├── requirements.txt
│   ├── template.yaml               # AWS SAM template (Lambda + API Gateway + DynamoDB)
│   ├── .env.example                # Required environment variables
│   └── run_path_tests.py           # Standalone async path tester
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Root layout (header, sidebar, chat, audit log)
│   │   ├── main.tsx                # ReactDOM.createRoot entry
│   │   ├── index.css               # Tailwind directives + CSS variables (dark theme)
│   │   ├── components/             # React components (shadcn/ui + custom)
│   │   ├── context/AuthContext.tsx # JWT auth state + login/register/logout
│   │   ├── hooks/useTriage.ts      # Chat message state + API calls
│   │   ├── pages/Home.tsx          # Unused placeholder (App.tsx is the real entry)
│   │   └── utils/api.ts            # Axios instance with JWT interceptor
│   ├── package.json
│   ├── vite.config.ts              # Dev proxy: /api → localhost:8000
│   ├── tailwind.config.js
│   └── tsconfig.json               # Project references (app + node)
│
├── docker-compose.yml              # Backend + ChromaDB services
├── .github/workflows/deploy.yml    # Frontend GitHub Pages deploy on push to main
└── docs/                           # Project documentation
```

---

## 4. Build & Run Commands

### Backend (local)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg   # Required for Presidio NER
cp .env.example .env                      # Fill in your secrets
python local_server.py                    # → http://localhost:8000
```

The server auto-reloads in local mode. It runs both the `/v1/*` router and legacy root-level routes (`/triage`, `/login`, `/register`, `/chats`, `/health`) for backward compatibility with the existing frontend.

### Frontend (local)

```bash
cd frontend
npm install
npm run dev         # → http://localhost:5173
```

Vite proxies `/api` calls to `http://localhost:8000` during development.

### Docker Compose (backend + ChromaDB)

```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- ChromaDB: `http://localhost:8001`

> **Note:** LM Studio (local LLM) is expected to run on the host at `localhost:1234`; the backend container reaches it via `host.docker.internal:1234`.

### AWS Deployment (optional)

```bash
cd backend
sam build
sam deploy --guided
```

Deploys: Lambda (container image) + API Gateway + DynamoDB + CloudWatch.

### Frontend Deployment

The frontend auto-deploys to GitHub Pages on every push to `main` that touches `frontend/**` (see `.github/workflows/deploy.yml`).

Manual deploy:
```bash
cd frontend
npm run deploy      # Uses gh-pages, publishes ./dist
```

---

## 5. Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in real values. The app uses `pydantic-settings` (`app/core/config.py`) to load and validate them.

| Variable | Purpose | Default |
|----------|---------|---------|
| `MONGODB_URI` | MongoDB connection string | *required* |
| `MONGODB_DB` | Database name | `guardian_health` |
| `TOGETHER_API_KEY` | Together.ai API key | *required in production* |
| `TOGETHER_MODEL` | Together.ai model ID | `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| `SECRET_KEY` | JWT signing key | *required* |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173,...` |
| `GUARDIAN_ENV` | Environment marker | `production` |
| `MOCK_MODE` | Return simulated LLM responses | `false` (forbidden in production) |
| `LM_STUDIO_URL` | Local LLM fallback endpoint | `http://localhost:1234` |
| `CHROMA_HOST` / `CHROMA_PORT` | ChromaDB connection | `localhost` / `8000` |
| `NCBI_EMAIL` | PubMed / NCBI contact email | `guardian-health@example.com` |

> **Security:** `MOCK_MODE=true` is **only** allowed when `GUARDIAN_ENV` is `development`, `dev`, `test`, or `testing`. The `llm_client.py` enforces this gate explicitly.

---

## 6. Testing

### Safety Evaluations

```bash
cd backend
pytest tests/test_safety_evals.py -v
```

These tests run in **mock mode** (no real AI calls) and verify:
- PII is detected and flagged.
- Clean queries pass through.
- Chest pain / shortness of breath route to **Emergency Room**.
- Every response contains a disclaimer.
- No response contains prohibited diagnosis phrases ("you have", "diagnosis is", etc.).
- No response names specific prescription drugs.
- Every audit log has a SHA-256 hash and a unique interaction ID.

### Path Tests

```bash
cd backend
python run_path_tests.py
```

A standalone async script that exercises every graph routing path (firewall, emergency, privacy, consultation, diagnosed, triage, force-phrase, compliance, etc.) and prints a pass/fail summary.

### Adding New Tests

- Prefer `pytest` for unit tests.
- Set `MOCK_MODE=true` in test environment to avoid burning API credits.
- The `TriageGraph` is a singleton; call `reset_graph()` in test setup if you need a fresh instance.

---

## 7. Code Style Guidelines

### Python

- **PEP 8** with line-length tolerance ~100–120 characters.
- Use **type hints** for function signatures and `TypedDict` states.
- Use **Pydantic** models for API request/response validation.
- Log via `logging.getLogger(__name__)`; the JSON formatter in `app/core/logging.py` handles structured output.
- Graph node functions return `dict` partial state updates; never mutate the shared `TriageState` directly.
- Always strip markdown fences (`` ```json ``) before parsing LLM JSON output; the `BaseAgent.parse_json()` helper does this.
- Mock responses are context-aware and vary per call (see `llm_client.py::_mock_response`) to avoid identical canned answers.

### TypeScript / React

- **Functional components** with hooks; no class components.
- Use the `@/` path alias for imports (`@/components`, `@/hooks`, `@/utils/api`).
- shadcn/ui components live in `src/components/ui/` and are copy-paste styled.
- Tailwind utility classes preferred over custom CSS; custom animations live in `src/index.css` under `@layer utilities`.
- Dark theme is the **only** theme; colors are defined via CSS variables in `:root`.

---

## 8. Architecture Details

### LangGraph Pipeline

The triage pipeline is modeled as a `StateGraph` with 11 nodes and conditional edges:

```
input_gate → firewall → privacy → extractor → ml_predictor → reasoner
                                                              │
                                    ┌──────── emergency ──────┼──→ assembler
                                    │                         │
                                    ├── diagnosed ──→ diagnosed_info → compliance ──→ assembler
                                    │
                                    └── consultation ──┬── follow_up ──→ assembler
                                                       └── ready ──→ triage ──→ assembler

assembler → persist → END
```

- **`reasoner_node`** decides the routing branch (`emergency`, `diagnosed`, `consultation`).
- **`consultation_node`** may return `ready_for_triage=false`, causing a follow-up message instead of a triage result.
- **`assembler_node`** builds the final `response_data` dict that the frontend consumes.
- **`persist_node`** saves chat history to MongoDB only when both `user` and `chat_id` are present.

### Auth Flow

- **Registration / Login** → PBKDF2-SHA256 hashed passwords → JWT access token (1-week expiry).
- Token is stored in `localStorage` as `guardian_token`.
- Axios interceptor attaches `Authorization: Bearer <token>` on every request.
- 401 responses clear local storage and reload the page.
- **Anonymous users** can chat, but chats are **not persisted** (no `chat_id` → `persist_node` skips).

### ML Model

- A **Random Forest** classifier trained on `backend/model/Training.csv`.
- Artifacts are serialized with `joblib` to `backend/app/ml_models/`.
- The `GuardianMLClient` in `ml_mcp_server.py` attempts MCP transport first, then falls back to direct Python call.

---

## 9. Security Considerations

| Risk | Mitigation | File |
|------|------------|------|
| Non-medical misuse | Medical Firewall LLM classifier | `medical_firewall.py` |
| PII leakage to AI | Presidio + regex redaction | `privacy_proxy.py` |
| Illegal diagnosis / Rx | Compliance Agent regex filter + mandatory disclaimer | `compliance_agent.py` |
| Unauthorized access | JWT tokens + hashed passwords | `auth_service.py` |
| Tampered logs | SHA-256 audit hash per interaction | `postprocess.py` (assembler_node) |
| Safety regressions | Automated safety test suite | `tests/test_safety_evals.py` |
| Mock mode in prod | Hard gate in `llm_client.py` | `llm_client.py` |

**Fail-open policy:** The medical firewall and privacy proxy fail open (let the request through) rather than block a potentially urgent patient query when the classifier or scrubber errors out.

---

## 10. Common Tasks for Agents

### Adding a New Graph Node

1. Create the node function in the appropriate `app/graph/nodes/*.py` file.
2. Import it in `app/graph/nodes/__init__.py`.
3. Register it in `app/graph/builder.py` (`add_node` + `add_edge` / `add_conditional_edges`).
4. Update `TriageState` in `app/graph/state.py` if new fields are needed.
5. Add a path test in `run_path_tests.py`.

### Adding a New API Endpoint

1. Add Pydantic models to `app/models/` if needed.
2. Add the route to the relevant `app/api/v1/*.py` router.
3. The route is automatically included under `/v1/*` via `app/api/router.py`.
4. If the frontend needs it on the legacy root path, add a mirror route in `local_server.py`.

### Changing LLM Prompts

1. Edit the JSON file in `app/prompt_hub/local/`.
2. Call `clear_cache()` from `app/prompt_hub/hub.py` if you need cache invalidation in tests.
3. Prompts are loaded once and cached in-memory for performance.

### Updating the ML Model

1. Run `backend/model/model.py` to retrain.
2. It automatically overwrites artifacts in `backend/app/ml_models/`.
3. Restart the backend to load the new model.

---

## 11. Important Notes

- **This is a portfolio demonstration project.** It is not a certified medical device. The disclaimer is enforced on every response.
- The frontend homepage is `https://Kartik-soni18.github.io/Guardian-health` (see `frontend/package.json` `homepage` and `vite.config.ts` `base`).
- The backend CORS configuration always appends `https://kartik-soni18.github.io` to the allowed origins list.
- MongoDB is used for user accounts, chat history, and interactions. DynamoDB is referenced in the SAM template for AWS deployments but the active code paths use MongoDB.
- ChromaDB is optional; the pipeline works without it if `CHROMA_HOST` is unreachable.

---

*Last updated: 2026-06-01*
