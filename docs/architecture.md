# Architecture

## High-Level Flow

```
React SPA (GitHub Pages)
        │
        ▼  HTTPS /api/v1/*
AWS API Gateway → Lambda (FastAPI + Mangum)
        │
        ├── MongoDB Atlas (users, auth)
        ├── Upstash Redis (cache, rate limits)
        ├── Together.ai (LLM triage)
        └── Indian Symptom-Disease Dataset (local CSV)
```

## Triage Pipeline

1. **Input gate** — validates query, detects emergency phrases
2. **Firewall** — classifies medical vs non-medical queries
3. **Privacy** — scrubs PII from input
4. **Extraction** — LLM extracts symptoms, duration, severity
5. **Dataset lookup** — matches symptoms to Indian healthcare reference data (cached in Redis)
6. **Reasoning** — builds clinical scratchpad with dataset hints
7. **Routing** — triage, consultation, disease info, or emergency path
8. **Compliance** — safety review before response assembly

## Deployment Topology

| Component | Host | Notes |
|---|---|---|
| Frontend | GitHub Pages | Static Vite build, `VITE_API_URL` points to Lambda |
| Backend | AWS Lambda | Container image via ECR, Mangum ASGI adapter |
| Auth DB | MongoDB Atlas | Connection string via `MONGODB_URI` |
| Cache | Upstash | REST API for Lambda compatibility |
