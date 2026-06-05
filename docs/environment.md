# Environment Variables

All configuration lives in a **single `.env` file at the project root**. Copy `.env.example` to `.env` and edit there. Docker Compose, the FastAPI backend, and the Vite frontend all read from this file.

## Backend (required)

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key, min 32 chars. Generate with `openssl rand -hex 32` |
| `MONGODB_URI` | MongoDB connection string |
| `TOGETHER_API_KEY` | Together.ai API key for LLM calls |

## Backend (optional)

| Variable | Default | Description |
|---|---|---|
| `MONGODB_DB_NAME` | `guardian` | Database name |
| `UPSTASH_REDIS_REST_URL` | — | Optional Upstash REST endpoint (leave blank to skip) |
| `UPSTASH_REDIS_REST_TOKEN` | — | Optional Upstash REST token |
| `UPSTASH_REDIS_URL` | — | Optional Redis URL for rate limiting |
| `CACHE_TTL_SECONDS` | `3600` | Default cache TTL |
| `MOCK_MODE` | `false` | Skip LLM calls (for CI/tests) |
| `ALLOWED_ORIGINS` | localhost origins | Comma-separated CORS origins |
| `TOGETHER_MODEL` | Llama 3.3 70B | LLM model slug |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Frontend

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL including `/api/v1` |
| `VITE_STREAM_API_URL` | Same as `VITE_API_URL` for SSE streaming (production) |

### Example values

**Local development:**
```
VITE_API_URL=http://localhost:8000/api/v1
```

**Production (GitHub Pages + Lambda Function URL):**

Frontend: [https://kartik-soni18.github.io/Guardian-health/](https://kartik-soni18.github.io/Guardian-health/)

```
VITE_API_URL=https://<id>.lambda-url.ap-southeast-2.on.aws/api/v1
VITE_STREAM_API_URL=https://<id>.lambda-url.ap-southeast-2.on.aws/api/v1
ALLOWED_ORIGINS=https://kartik-soni18.github.io
```

Set `VITE_API_URL` and `VITE_STREAM_API_URL` as GitHub repository variables. CORS uses the origin host only (`https://kartik-soni18.github.io`), not the `/Guardian-health/` path.
