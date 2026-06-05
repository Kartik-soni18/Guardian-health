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
- ECR repository for the container image
- MongoDB Atlas cluster
- Upstash Redis instance
- Together.ai API key

### Build and push container

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com

docker build -t guardian-api -f backend/Dockerfile .
docker tag guardian-api:latest $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/guardian-api:latest
docker push $ACCOUNT.dkr.ecr.$REGION.amazonaws.com/guardian-api:latest
```

### Deploy with SAM

```bash
sam deploy \
  --template-file template.yaml \
  --stack-name guardian-health \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    SecretKey=... \
    TogetherApiKey=... \
    MongoDbUri=... \
    UpstashRedisRestUrl=... \
    UpstashRedisRestToken=... \
    AllowedOrigins=https://your-user.github.io
```

### Lambda runtime

The container runs **uvicorn** via Lambda Web Adapter (`backend/run.sh`) with `AWS_LWA_INVOKE_MODE=response_stream` for SSE streaming. A Lambda Function URL is created for streaming; API Gateway handles all other routes.

For local development, use `uvicorn app.main:app --reload` from the `backend/` directory.

### CORS

Add your GitHub Pages origin to `ALLOWED_ORIGINS` on the Lambda function. The SAM template passes this via the `AllowedOrigins` parameter.

## Connecting Frontend to Backend

1. Deploy Lambda and note the API Gateway URL from SAM outputs.
2. Set `VITE_API_URL` in GitHub repo variables.
3. Re-run the frontend deploy workflow (or push a frontend change).
4. Verify: open the GitHub Pages site, register/login, submit a triage query.
