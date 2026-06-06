# Deploy Backend to AWS Lambda

Step-by-step guide for GuardianHealth FastAPI on AWS Lambda with a Function URL.

## Architecture

```
GitHub Pages frontend  →  Lambda Function URL (RESPONSE_STREAM)  →  uvicorn + Web Adapter  →  MongoDB Atlas + Together.ai
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

Pick a region close to you and Atlas (e.g. `ap-southeast-2` Sydney):

```bash
export AWS_REGION=ap-southeast-2
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

## Step 3 — Build and deploy with SAM

Use the deploy script (recommended) from the **project root**:

```bash
./scripts/deploy-aws.sh
```

This loads secrets from `.env`, cleans local `.aws-sam/` artifacts and old ECR images, runs `sam build` + `sam deploy`, and verifies `/health`.

Options:

```bash
./scripts/deploy-aws.sh --clean-only          # cleanup only, no deploy
./scripts/deploy-aws.sh --skip-ecr            # skip ECR image cleanup
./scripts/deploy-aws.sh --trigger-frontend    # also run GitHub Pages workflow via gh
AWS_REGION=ap-southeast-2 ./scripts/deploy-aws.sh
```

Manual deploy (equivalent):

Load values from your root `.env` (do not commit secrets):

```bash
export SECRET_KEY="your-secret-from-env"
export TOGETHER_API_KEY="your-together-key"
export MONGODB_URI="mongodb+srv://kartik-medical:PASSWORD@cluster0.jzylktb.mongodb.net/?appName=Cluster0"
export ALLOWED_ORIGINS="https://kartik-soni18.github.io"

sam build --template-file template.yaml

sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name guardian-health \
  --region $AWS_REGION \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
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

## Step 4 — Get your Function URL

```bash
aws cloudformation describe-stacks \
  --stack-name guardian-health \
  --region $AWS_REGION \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

Example output:

```
https://abc123xyz.lambda-url.ap-southeast-2.on.aws
```

Your frontend API base URL is that value **plus** `/api/v1`:

```
https://abc123xyz.lambda-url.ap-southeast-2.on.aws/api/v1
```

## Step 5 — Connect the frontend

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **Variables**
2. Add `VITE_API_URL` = `https://YOUR-FUNCTION-URL.lambda-url.REGION.on.aws/api/v1`
3. Add `VITE_STREAM_API_URL` = same value
4. Push to `main` or re-run the **Deploy Frontend to GitHub Pages** workflow

## Step 6 — Verify

```bash
FUNCTION_URL=$(aws cloudformation describe-stacks \
  --stack-name guardian-health \
  --region $AWS_REGION \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text)

# Health check
curl "$FUNCTION_URL/health"

# CORS preflight (should return exactly one Access-Control-Allow-Origin)
curl -s -D - -o /dev/null -X OPTIONS \
  -H "Origin: https://kartik-soni18.github.io" \
  -H "Access-Control-Request-Method: POST" \
  "$FUNCTION_URL/api/v1/auth/login"
```

Then open [https://kartik-soni18.github.io/Guardian-health/](https://kartik-soni18.github.io/Guardian-health/) and test login + triage.

## Updating after code changes

```bash
./scripts/deploy-aws.sh
```

Or manually:

```bash
sam build --template-file template.yaml
sam deploy --template-file template.yaml --stack-name guardian-health \
  --region $AWS_REGION --capabilities CAPABILITY_IAM --resolve-image-repos \
  --parameter-overrides SecretKey="$SECRET_KEY" TogetherApiKey="$TOGETHER_API_KEY" ...
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `502` from Function URL | Check CloudWatch Logs for `guardian-api` Lambda |
| MongoDB connection timeout | Atlas Network Access must include `0.0.0.0/0` |
| CORS error: "cannot contain more than one origin" | Remove `Cors` from `FunctionUrlConfig` in `template.yaml`; let FastAPI handle CORS |
| CORS error: origin blocked | `AllowedOrigins` must be `https://kartik-soni18.github.io` (no path) |
| Triage fails | Confirm `TOGETHER_API_KEY` is set on Lambda env vars |
| Cold start slow | Normal for container Lambda (~3–8s first request) |

View logs:

```bash
aws logs tail /aws/lambda/guardian-api --region $AWS_REGION --follow
```

## Cost reminder

For light usage, AWS (Lambda + ECR) is typically **~$0/month** within free tier. Main cost is **Together.ai** per triage request.
