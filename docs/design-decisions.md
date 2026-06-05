# Design Decisions

## Upstash Redis over in-memory cache

Lambda containers are ephemeral. Upstash Redis provides a serverless-compatible cache via REST API, shared across Lambda invocations for symptom lookups and optional rate-limit storage.

## Indian healthcare dataset over ML model

The structured CSV in `backend/data/` provides region-aware symptom-disease mappings with severity and duration metadata. This replaces a separate ML inference service, reducing infrastructure cost and latency while keeping predictions explainable.

## MongoDB for auth

User accounts need persistent storage with indexed lookups by username and email. MongoDB Atlas offers a managed free tier suitable for this workload.

## LangGraph for triage

Multi-step clinical workflows (firewall → extraction → dataset lookup → reasoning → triage) benefit from explicit graph routing, observability per node, and independent retry/fallback paths.

## Shorter prompts

Each LLM node uses compressed system prompts and compact user context strings. This cuts input tokens per request without sacrificing structured JSON output requirements.

## GitHub Pages + Lambda split

The frontend is a static SPA ideal for GitHub Pages. The backend needs compute for LLM orchestration, making Lambda a cost-effective fit. CORS and `VITE_API_URL` connect the two at build time.
