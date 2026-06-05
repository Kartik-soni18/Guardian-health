# Deployment

> **Do not deploy until credentials and infrastructure are configured.** This guide describes the intended setup only.

## Overview

| Layer | Target | Config |
|---|---|---|
| Frontend | GitHub Pages | `.github/workflows/deploy.yml` |
| Backend | AWS Lambda Function URL | `template.yaml` + ECR container image (Lambda Web Adapter) |

## Frontend — GitHub Pages

1. Enable GitHub Pages on the repository (source: `gh-pages` branch).
2. Set repository variables:
   - `VITE_API_URL` — Lambda Function URL + `/api/v1`
   - `VITE_STREAM_API_URL` — same value (streaming uses the same endpoint)
   ```
   https://<id>.lambda-url.ap-southeast-2.on.aws/api/v1
   ```
3. Push to `main` — the workflow builds and publishes `frontend/dist`.

The Vite `base` path is set to `/Guardian-health/` for GitHub Pages project sites. Adjust in `frontend/vite.config.ts` if your repo name differs.

## Backend — AWS Lambda

### Prerequisites

- AWS CLI and SAM CLI
- MongoDB Atlas cluster
- Upstash Redis instance (optional)
- Together.ai API key

SAM creates and manages the ECR repository automatically when you use `--resolve-image-repos`.

### Deploy with SAM

```bash
sam build --template-file template.yaml
sam deploy \
  --template-file template.yaml \
  --stack-name guardian-health \
  --capabilities CAPABILITY_IAM \
  --resolve-image-repos \
  --parameter-overrides \
    SecretKey=... \
    TogetherApiKey=... \
    MongoDbUri=... \
    UpstashRedisRestUrl=... \
    UpstashRedisRestToken=... \
    AllowedOrigins=https://your-user.github.io
```

### Lambda runtime

The container runs **uvicorn** via Lambda Web Adapter (`backend/run.sh`) with `AWS_LWA_INVOKE_MODE=response_stream` for SSE streaming. A Lambda Function URL (`InvokeMode: RESPONSE_STREAM`) is the sole API entry point — there is no API Gateway.

For local development, use `uvicorn app.main:app --reload` from the `backend/` directory.

### CORS

Add your GitHub Pages origin to `ALLOWED_ORIGINS` on the Lambda function. The SAM template passes this via the `AllowedOrigins` parameter. FastAPI `CORSMiddleware` is the only layer that sets CORS headers — do not add a `Cors` block to `FunctionUrlConfig` in `template.yaml`.

## Connecting Frontend to Backend

1. Deploy Lambda and note the Function URL from SAM outputs (`ApiEndpoint`).
2. Set `VITE_API_URL` and `VITE_STREAM_API_URL` in GitHub repo variables (both = Function URL + `/api/v1`).
3. Re-run the frontend deploy workflow (or push a frontend change).
4. Verify: open the GitHub Pages site, register/login, submit a triage query.
