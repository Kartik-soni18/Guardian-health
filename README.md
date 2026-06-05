# GuardianHealth

AI-powered symptom triage for Indian healthcare contexts. LangGraph clinical reasoning backed by structured symptom-disease data, MongoDB auth, Upstash Redis caching, and a React frontend.

## Overview

GuardianHealth helps patients describe symptoms and receive triage guidance — emergent, urgent, routine, or self-care — with regional disease context from the Indian healthcare dataset. The backend runs as a FastAPI app (deployable on AWS Lambda) and the frontend ships to GitHub Pages.

Copy `.env.example` to `.env` at the project root before running locally.

## Documentation

| Guide | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design and data flow |
| [Quick Start](docs/quick-start.md) | Run locally with Docker Compose |
| [Environment](docs/environment.md) | Required and optional variables |
| [API Reference](docs/api.md) | Endpoints and request formats |
| [Deployment](docs/deployment.md) | AWS Lambda backend + GitHub Pages frontend |
| [Backend AWS Deploy](docs/deploy-backend-aws.md) | Step-by-step Lambda deployment guide |
| [Development](docs/development.md) | Testing, linting, and contribution workflow |
| [Design Decisions](docs/design-decisions.md) | Technology choices and trade-offs |

## Stack

- **Frontend** — React 19, Vite, TypeScript, Tailwind CSS
- **Backend** — FastAPI, LangGraph, Together.ai (Llama 3.3 70B)
- **Database** — MongoDB (auth)
- **Cache** — Upstash Redis
- **Data** — Indian Healthcare Symptom-Disease Dataset
- **Deploy** — AWS Lambda Function URL (streaming) + GitHub Pages (SPA)

## License

MIT
