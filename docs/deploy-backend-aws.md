# Deploy Backend to AWS Lambda

Step-by-step guide for GuardianHealth FastAPI on AWS Lambda + API Gateway.

## Architecture

```
GitHub Pages frontend  →  API Gateway (HTTP)  →  Lambda (container)  →  MongoDB Atlas + Together.ai
```

## Prerequisites

1. **AWS account** with CLI configured (`aws configure`)
2. **Docker** running locally
3. **AWS SAM CLI** — [install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
4. **MongoDB Atlas** — cluster running, password set in root `.env`
5. **Together.ai API key** in root `.env`

```bash
# Verify tools
aws sts get-caller-identity
sam --version
docker --version
```

## Step 1 — Allow Lambda to reach MongoDB Atlas

Lambda has no fixed IP. In [MongoDB Atlas](https://cloud.mongodb.com):

1. Open your cluster → **Network Access**
2. Add IP address: `0.0.0.0/0` (allow from anywhere)

For production you can tighten this later with a VPC; for first deploy this is simplest.

## Step 2 — Choose AWS region

Pick a region close to you and Atlas (e.g. `ap-south-1` Mumbai):

```bash
export AWS_REGION=ap-south-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

## Step 3 — Create ECR repository (first time only)

```bash
aws ecr create-repository \
  --repository-name guardian-api \
  --region $AWS_REGION \
  --image-scanning-configuration scanOnPush=true
```

## Step 4 — Build and push the Lambda image

From the **project root**:

```bash
cd "/Users/kartiksoni/Desktop/guardian health"

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build --platform linux/arm64 \
  -f backend/Dockerfile.lambda \
  -t guardian-api .

docker tag guardian-api:latest \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest

docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest
```

> Use `Dockerfile.lambda` (Mangum handler), not `Dockerfile` (uvicorn for docker-compose).

## Step 5 — Deploy with SAM

Load values from your root `.env` (do not commit secrets):

```bash
export SECRET_KEY="your-secret-from-env"
export TOGETHER_API_KEY="your-together-key"
export MONGODB_URI="mongodb+srv://kartik-medical:PASSWORD@cluster0.jzylktb.mongodb.net/?appName=Cluster0"
export ALLOWED_ORIGINS="https://kartik-soni18.github.io"

sam deploy \
  --template-file template.yaml \
  --stack-name guardian-health \
  --region $AWS_REGION \
  --capabilities CAPABILITY_IAM \
  --resolve-image-repos \
  --parameter-overrides \
    SecretKey="$SECRET_KEY" \
    TogetherApiKey="$TOGETHER_API_KEY" \
    MongoDbUri="$MONGODB_URI" \
    UpstashRedisRestUrl="" \
    UpstashRedisRestToken="" \
    AllowedOrigins="$ALLOWED_ORIGINS"
```

First deploy may take 5–10 minutes.

## Step 6 — Get your API URL

```bash
aws cloudformation describe-stacks \
  --stack-name guardian-health \
  --region $AWS_REGION \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

Example output:

```
https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod
```

Your frontend API base URL is that value **plus** `/api/v1`:

```
https://abc123xyz.execute-api.ap-southeast-2.amazonaws.com/api/v1
```

> The API uses the `$default` stage — there is no `/prod` prefix in the URL.

## Step 7 — Connect the frontend

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Add `VITE_API_URL` = `https://YOUR-API.execute-api.REGION.amazonaws.com/prod/api/v1`
3. Push to `main` or re-run the **Deploy Frontend to GitHub Pages** workflow

## Step 8 — Verify

```bash
# Health check
curl https://YOUR-API.execute-api.REGION.amazonaws.com/prod/health

# Register (optional)
curl -X POST https://YOUR-API.execute-api.REGION.amazonaws.com/prod/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser1","email":"test@example.com","password":"TestPass123!","full_name":"Test User"}'
```

Then open [https://kartik-soni18.github.io/Guardian-health/](https://kartik-soni18.github.io/Guardian-health/) and test login + triage.

## Updating after code changes

```bash
# Rebuild and push image
docker build --platform linux/arm64 -f backend/Dockerfile.lambda -t guardian-api .
docker tag guardian-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest

# Redeploy (same sam deploy command as Step 5)
sam deploy --template-file template.yaml --stack-name guardian-health ...
```

Or use SAM build (builds image automatically):

```bash
sam build --template-file template.yaml
sam deploy --guided
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `502` from API Gateway | Check CloudWatch Logs for `guardian-api` Lambda |
| MongoDB connection timeout | Atlas Network Access must include `0.0.0.0/0` |
| CORS error in browser | `AllowedOrigins` must be `https://kartik-soni18.github.io` (no path) |
| Triage fails | Confirm `TOGETHER_API_KEY` is set on Lambda env vars |
| Cold start slow | Normal for container Lambda (~3–8s first request) |

View logs:

```bash
aws logs tail /aws/lambda/guardian-api --region $AWS_REGION --follow
```

## Cost reminder

For light usage, AWS (Lambda + API Gateway + ECR) is typically **~$0/month** within free tier. Main cost is **Together.ai** per triage request.
