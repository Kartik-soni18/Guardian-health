# Quick Start

## Prerequisites

- Docker 24+ and Docker Compose v2.20+
- Together.ai API key (or `MOCK_MODE=true` for offline tests)
- Optional: Upstash Redis credentials for caching

## Setup

```bash
git clone https://github.com/your-org/guardian-health.git
cd guardian-health

openssl rand -hex 32   # paste into SECRET_KEY

cp .env.example .env
```

Edit the root `.env` with your `SECRET_KEY`, MongoDB Atlas password in `MONGODB_URI`, `TOGETHER_API_KEY`, and `VITE_API_URL`. Upstash Redis is optional — leave those fields blank if you do not have them.

## Run

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API docs (debug mode) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## Stop

```bash
docker compose down        # stop containers
docker compose down -v     # stop and remove volumes
```

## Local Frontend Dev (without Docker)

```bash
cd frontend
npm ci
npm run dev
```

The Vite dev server proxies `/api/v1` to `http://localhost:8000`.
