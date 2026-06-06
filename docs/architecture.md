# Architecture

## High-Level Flow

```
React SPA (GitHub Pages)
        │
        ▼  HTTPS /api/v1/*
Lambda Function URL (RESPONSE_STREAM)
        │
        ▼
Lambda container (uvicorn + Lambda Web Adapter)
        │
        ├── MongoDB Atlas (users, chats, messages)
        ├── Upstash Redis (cache, rate limits)
        ├── Together.ai (LLM triage)
        └── Indian Symptom-Disease Dataset (local CSV)
```

## Triage Pipeline

1. **Input gate** — validates query, detects emergency phrases
2. **Firewall** — classifies medical vs non-medical queries
3. **Privacy** — scrubs PII from input (regex-based)
4. **Extraction** — LLM extracts symptoms, duration, severity
5. **Dataset lookup** — matches symptoms to Indian healthcare reference data (cached in Redis)
6. **Reasoning** — builds clinical scratchpad with dataset hints
7. **Routing** — triage, consultation, disease info, or emergency path
8. **Compliance** — safety review before response assembly
9. **Persist** — when authenticated with `chat_id`, user and assistant turns are saved to MongoDB (server-authoritative history)

## Chat Persistence

- Chats and messages live in separate MongoDB collections keyed by `user_id`.
- The frontend creates chats via `/api/v1/chats` and sends triage requests with `chat_id`.
- The backend loads prior messages from MongoDB for multi-turn context; client-sent `conversation_history` is ignored for authenticated chat sessions.
- User messages are PII-scrubbed before persistence.

## Streaming

The `/api/v1/triage/stream` endpoint returns Server-Sent Events (SSE):

- **status** events during LangGraph preprocessing (input gate, firewall, privacy, etc.)
- **token** events for the final LLM response text
- **done** / **error** events when the pipeline completes or fails

Lambda Web Adapter runs uvicorn with `AWS_LWA_INVOKE_MODE=response_stream` so SSE works through the Function URL.

## Deployment Topology

| Component | Host | Notes |
|---|---|---|
| Frontend | GitHub Pages | Static Vite build; `VITE_API_URL` and `VITE_STREAM_API_URL` point to Function URL + `/api/v1` |
| Backend | AWS Lambda | Container image via ECR; uvicorn + Lambda Web Adapter (not Mangum) |
| API entry | Lambda Function URL | `InvokeMode: RESPONSE_STREAM`; no API Gateway |
| Auth DB | MongoDB Atlas | Users, chats, and messages via `MONGODB_URI` |
| Cache | Upstash | REST API for Lambda compatibility |

## CORS

CORS is handled solely by FastAPI `CORSMiddleware` in `backend/app/main.py`, driven by the `ALLOWED_ORIGINS` environment variable. The Lambda Function URL does **not** set CORS headers — configuring CORS on both layers causes duplicate `Access-Control-Allow-Origin` headers that browsers reject.
