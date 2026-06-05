# Deployment

> **Do not deploy until credentials and infrastructure are configured.** This guide describes the intended setup only.

## Overview

| Layer | Target | Config |
|---|---|---|
| Frontend | GitHub Pages | `.github/workflows/deploy.yml` |
| Backend | AWS Lambda | `template.yaml` + ECR container image |

## Frontend — GitHub Pages

1. Enable GitHub Pages on the repository (source: `gh-pages` branch).
2. Set repository variable `VITE_API_URL` to your Lambda API URL with `/api/v1` suffix:
   ```
   https://your-api.execute-api.ap-southeast-2.amazonaws.com/prod/api/v1
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

### Lambda handler

The container entry point for Lambda is `handler.handler` (Mangum wrapping the FastAPI app). For local uvicorn, use `app.main:app` as usual.

### CORS

Add your GitHub Pages origin to `ALLOWED_ORIGINS` on the Lambda function. The SAM template passes this via the `AllowedOrigins` parameter.

## Connecting Frontend to Backend

1. Deploy Lambda and note the API Gateway URL from SAM outputs.
2. Set `VITE_API_URL` in GitHub repo variables.
3. Re-run the frontend deploy workflow (or push a frontend change).
4. Verify: open the GitHub Pages site, register/login, submit a triage query.
