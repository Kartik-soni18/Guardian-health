# GuardianHealth v2

> Zero-cost health record intelligence. AI-powered clinical analysis with absolutely zero infrastructure spend -- only AWS DynamoDB free tier.

GuardianHealth v2 is a modern, serverless-first healthcare intelligence platform that analyzes patient records, detects clinical insights, anonymizes PII, and surfaces evidence-backed recommendations -- all without incurring infrastructure costs.

---

## Architecture

```
+---------------------+        +-----------------------+
|   React 19 + Vite   |        |   FastAPI (Python 3.12)|
|   (Nginx / Port 80) |------->|   (Uvicorn / Port 8000)|
|   SPA Static Assets |        |                       |
+----------+----------+        | - BackgroundTasks     |
           |                   | - cachetools (memory) |
           |                   | - slowapi (rate limit)|
           |                   | - LangGraph AI        |
           |                   +----------+------------+
           |                              |
           |                     +--------+--------+
           |                     |                 |
           v                     v                 v
+----------+-----------+  +------+------+  +-------+-------+
| DynamoDB Local       |  | Together.ai |  | NCBI / PubMed |
| (dev: port 4569)     |  | (LLM calls) |  | (evidence)    |
+----------------------+  +-------------+  +---------------+

PRODUCTION (100% AWS Free Tier):
+---------------------+        +-----------------------------+
|   CloudFront        |        |   API Gateway (HTTP)        |
|   (static site)     |        |   Lambda Proxy Integration  |
+----------+----------+        +--------------+--------------+
           |                                  |
           v                                  v
+---------------------------+  +----------------------------+
|  S3 (React build)         |  |  Lambda (FastAPI container)|
|  OAC private              |  |  3GB RAM / ARM64           |
+---------------------------+  +--------------+-------------+
                                                |
                                     +----------+----------+
                                     | DynamoDB (on-demand) |
                                     | 25 GB read/write FREE |
                                     +----------------------+
```

---

## Tech Stack

| Layer | Technology | Purpose | Cost |
|---|---|---|---|
| **Frontend** | React 19 + Vite + TypeScript | Modern SPA development | Free |
| **Web Server** | Nginx (Alpine) | Static asset serving, API proxy | Free |
| **Backend** | FastAPI + Python 3.12 | High-performance async API | Free |
| **Background Tasks** | `BackgroundTasks` + `asyncio` | Built-in, no Celery | Free |
| **Cache** | `cachetools` (in-memory) | Zero external dependency | Free |
| **Rate Limiting** | `slowapi` (memory) | Request throttling | Free |
| **Database** | DynamoDB (on-demand) | 25 GB storage, 200M reads/writes FREE / month | **Free** |
| **Auth** | JWT + `python-jose` + `passlib` | Stateless authentication | Free |
| **AI Engine** | LangGraph + Together.ai (Llama 3.3 70B) | Clinical reasoning & analysis | Free tier |
| **PII Protection** | Microsoft Presidio | Automated de-identification | Free |
| **Evidence** | NCBI E-utilities | PubMed literature search | Free |
| **Observability** | Prometheus client | `/metrics` endpoint | Free |
| **Deployment** | Docker + Docker Compose | Local & CI/CD | Free |

---

## Quick Start (Docker Compose)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24.0+
- [Docker Compose](https://docs.docker.com/compose/) v2.20+
- `openssl` (for key generation)

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/guardian-health.git
cd guardian-health

# Generate a secure secret key
openssl rand -hex 32
# -> paste the output into SECRET_KEY below

# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Start Everything

```bash
# Full stack: Nginx + FastAPI + DynamoDB Local
docker compose up --build

# Or detached
docker compose up -d --build
```

### 3. Verify Services

| Service | URL | Notes |
|---|---|---|
| Frontend (Nginx) | http://localhost | React SPA |
| API Docs (Swagger) | http://localhost/api/docs | Auto-generated |
| Health Check | http://localhost:8000/health | Backend liveness |
| DynamoDB Local | http://localhost:4569 | Local AWS-compatible DB |

### 4. Stop

```bash
docker compose down          # stop
docker compose down -v       # stop + remove volumes
```

---

## Environment Setup

### Required Variables

| Variable | Default | How to Obtain |
|---|---|---|
| `SECRET_KEY` | *(none)* | `openssl rand -hex 32` |
| `TOGETHER_API_KEY` | *(none)* | [api.together.xyz](https://api.together.xyz/) -- free tier includes $5 credit |
| `NCBI_EMAIL` | *(none)* | Your email for NCBI E-utilities compliance |
| `NCBI_API_KEY` | *(none)* | Optional; increases rate limits. [Get one here](https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/) |
| `AWS_REGION` | `us-east-1` | Must be a [DynamoDB always-free region](https://aws.amazon.com/dynamodb/pricing/on-demand/) |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `DYNAMODB_TABLE_PREFIX` | `guardian-local` | Prefixes all table names for env isolation |
| `MOCK_MODE` | `false` | When `true`, skips external API calls (safe for CI) |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `ALLOWED_ORIGINS` | `http://localhost,...` | Comma-separated CORS origins |

---

## Project Structure

```
guardian-health/
  docker-compose.yml           # Full local stack
  README.md                    # This file
  backend/
    Dockerfile                 # Multi-stage production build
    Dockerfile.dev             # Hot-reload development build
    .env.example               # Environment variable template
    pyproject.toml             # Project metadata & dependencies
    requirements.txt           # Pinned runtime dependencies
    app/
      __init__.py
      main.py                  # FastAPI app factory
      config.py                # Pydantic settings
      routers/                 # API route modules
      services/                # Business logic
      models/                  # Pydantic schemas
      db/                      # DynamoDB client & tables
      ai/                      # LangGraph workflows
      auth/                    # JWT & password utils
      cache.py                 # cachetools wrapper
      telemetry.py             # Prometheus metrics
    scripts/
      init_tables.py           # DynamoDB table creation
  frontend/
    Dockerfile                 # Node build + nginx
    nginx.conf                 # SPA & proxy configuration
    .env.example               # VITE_API_URL template
    src/                       # React 19 + Vite source
    public/
    index.html
    vite.config.ts
    package.json
```

---

## API Documentation

FastAPI auto-generates interactive documentation:

- **Swagger UI**: `http://localhost/api/docs`
- **ReDoc**: `http://localhost/api/redoc`
- **OpenAPI Schema**: `http://localhost/api/openapi.json`

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe (200 + JSON) |
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Obtain JWT token |
| `POST` | `/api/v1/records` | Upload health record for analysis |
| `GET` | `/api/v1/records/{id}` | Retrieve record + analysis |
| `DELETE` | `/api/v1/records/{id}` | Soft-delete record |
| `GET` | `/api/v1/records` | List user's records |
| `POST` | `/api/v1/analyze` | Run AI clinical analysis |
| `GET` | `/api/v1/analyze/{id}/status` | Poll async analysis status |
| `GET` | `/api/v1/evidence` | Search PubMed evidence |
| `GET` | `/metrics` | Prometheus metrics |

---

## Testing

### Local Development Tests

```bash
cd backend

# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests (fast, no external services)
pytest -m unit -v

# Run integration tests (uses mock mode, no API keys needed)
pytest -m integration -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Lint & format
black app/ tests/
ruff check app/ tests/
mypy app/
```

### CI Test Mode

Set `MOCK_MODE=true` in CI environments. All external calls (Together.ai, NCBI) are replaced with deterministic fixtures, so tests pass without API keys.

---

## AWS Deployment Guide

### Design Goal: ZERO Infrastructure Cost

GuardianHealth v2 is designed to run entirely within AWS free tier limits. The only paid-adjacent service is DynamoDB, whose on-demand free tier is permanently free (not a 12-month trial).

### AWS Free Tier Limits Used

| Service | Free Tier | Our Usage |
|---|---|---|
| **DynamoDB** | 25 GB storage, 200M read/write requests/month | Primary database |
| **Lambda** | 1M requests + 400,000 GB-seconds/month | API compute |
| **API Gateway (HTTP)** | 1M requests/month | API routing |
| **CloudFront** | 1M requests + 50 GB transfer/month | Static site CDN |
| **S3** | 5 GB standard storage | React build artifacts |
| **ECR** | 500 MB storage/month | Lambda container image |

### Deployment Option A: SAM (Recommended)

Use AWS SAM for Infrastructure-as-Code deployment in minutes.

#### 1. Install SAM CLI

```bash
# macOS
brew tap aws/tap && brew install aws-sam-cli

# Linux
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
```

#### 2. SAM Template (`template.yaml`)

Create a `template.yaml` in your project root:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: GuardianHealth v2 - Zero-cost health intelligence

Globals:
  Api:
    Cors:
      AllowMethods: "'*'"
      AllowHeaders: "'*'"
      AllowOrigin: "'*'"
    BinaryMediaTypes:
      - multipart/form-data

Parameters:
  SecretKey:
    Type: AWS::SSM::Parameter::Value<String>
    Default: /guardian/prod/secret-key
  TogetherApiKey:
    Type: AWS::SSM::Parameter::Value<String>
    Default: /guardian/prod/together-api-key
  NcbiEmail:
    Type: AWS::SSM::Parameter::Value<String>
    Default: /guardian/prod/ncbi-email
  TablePrefix:
    Type: String
    Default: guardian-prod

Resources:
  # --- DynamoDB Tables (on-demand = pay-per-request = free tier) ---
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "${TablePrefix}-users"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
        - AttributeName: email
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: email-index
          KeySchema:
            - AttributeName: email
              KeyType: HASH
          Projection:
            ProjectionType: ALL
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true

  RecordsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "${TablePrefix}-records"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
        - AttributeName: created_at
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: user-created-index
          KeySchema:
            - AttributeName: user_id
              KeyType: HASH
            - AttributeName: created_at
              KeyType: RANGE
          Projection:
            ProjectionType: ALL

  AnalysesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "${TablePrefix}-analyses"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: id
          AttributeType: S
        - AttributeName: record_id
          AttributeType: S
      KeySchema:
        - AttributeName: id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: record-index
          KeySchema:
            - AttributeName: record_id
              KeyType: HASH
          Projection:
            ProjectionType: ALL

  # --- Lambda Function (FastAPI container) ---
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: guardian-api
      PackageType: Image
      ImageUri: !Sub "${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/guardian-api:latest"
      Architectures:
        - arm64
      MemorySize: 3008
      Timeout: 30
      Environment:
        Variables:
          ENVIRONMENT: production
          SECRET_KEY: !Ref SecretKey
          TOGETHER_API_KEY: !Ref TogetherApiKey
          NCBI_EMAIL: !Ref NcbiEmail
          DYNAMODB_TABLE_PREFIX: !Ref TablePrefix
          AWS_REGION: !Ref AWS::Region
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
        - DynamoDBCrudPolicy:
            TableName: !Ref RecordsTable
        - DynamoDBCrudPolicy:
            TableName: !Ref AnalysesTable
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /{proxy+}
            Method: ANY
            TimeoutInMillis: 25000
            PayloadFormatVersion: "2.0"

  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: prod
      AutoDeploy: true
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
          - OPTIONS
        AllowHeaders:
          - Authorization
          - Content-Type
          - X-Request-ID

  # --- S3 Bucket (private, CloudFront only) ---
  StaticBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "guardian-static-${AWS::AccountId}-${AWS::Region}"
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # --- CloudFront Distribution ---
  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        DefaultRootObject: index.html
        Origins:
          - Id: s3-origin
            DomainName: !GetAtt StaticBucket.RegionalDomainName
            S3OriginConfig:
              OriginAccessIdentity: ""
            OriginAccessControlId: !Ref CloudFrontOAC
          - Id: api-origin
            DomainName: !Sub "${HttpApi}.execute-api.${AWS::Region}.amazonaws.com"
            CustomOriginConfig:
              OriginProtocolPolicy: https-only
        DefaultCacheBehavior:
          TargetOriginId: s3-origin
          ViewerProtocolPolicy: redirect-to-https
          CachePolicyId: 658327ea-f89d-4fab-a63d-7e88639e58f6  # Managed-CachingOptimized
          OriginRequestPolicyId: 88a5eaf4-2fd4-4709-b370-b4c650ea3fcf  # Managed-CORS-S3Origin
        CacheBehaviors:
          - PathPattern: /api/*
            TargetOriginId: api-origin
            ViewerProtocolPolicy: https-only
            CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # Managed-CachingDisabled
            OriginRequestPolicyId: b689b0a8-53d0-40ab-baf2-68738e2966ac  # Managed-AllViewerExceptHostHeader
        CustomErrorResponses:
          - ErrorCode: 403
            ResponseCode: 200
            ResponsePagePath: /index.html
          - ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /index.html

  CloudFrontOAC:
    Type: AWS::CloudFront::OriginAccessControl
    Properties:
      OriginAccessControlOriginType: s3
      SigningBehavior: always
      SigningProtocol: sigv4

  # --- ECR Repository ---
  ApiRepository:
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: guardian-api
      ImageTagMutability: MUTABLE
      ImageScanningConfiguration:
        ScanOnPush: true

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint
    Value: !Sub "https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com/prod/"
  CloudFrontUrl:
    Description: CloudFront distribution URL
    Value: !GetAtt CloudFrontDistribution.DomainName
```

#### 3. Deploy Steps

```bash
# 1. Login to AWS
eval $(aws configure export-credentials --format env)

# 2. Build & push container to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t guardian-api -f backend/Dockerfile .
docker tag guardian-api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/guardian-api:latest

# 3. Build & upload frontend to S3
cd frontend
npm ci && npm run build
aws s3 sync dist/ s3://guardian-static-$AWS_ACCOUNT_ID-$AWS_REGION/ --delete

# 4. Deploy with SAM
cd ..
sam deploy \
  --stack-name guardian-health \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    "SecretKey=arn:aws:ssm:us-east-1:$AWS_ACCOUNT_ID:parameter/guardian/prod/secret-key" \
    "TogetherApiKey=arn:aws:ssm:us-east-1:$AWS_ACCOUNT_ID:parameter/guardian/prod/together-api-key" \
    "NcbiEmail=arn:aws:ssm:us-east-1:$AWS_ACCOUNT_ID:parameter/guardian/prod/ncbi-email" \
  --no-confirm-changeset

# 5. Get outputs
sam list stack-outputs --stack-name guardian-health
```

### Deployment Option B: Docker Compose on VPS

For a self-hosted option on any VPS (DigitalOcean, Hetzner, etc.):

```bash
# On your server
git clone https://github.com/your-org/guardian-health.git
cd guardian-health

# Configure production .env
cp backend/.env.example backend/.env
# Edit backend/.env with real credentials and:
#   DYNAMODB_ENDPOINT_URL=  (leave empty for real AWS)

# Start
docker compose -f docker-compose.yml up -d --build
```

### Deployment Option C: Render / Railway / Fly.io

The containerized backend can deploy to any platform supporting Docker:

```yaml
# render.yaml
services:
  - type: web
    name: guardian-api
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: DYNAMODB_TABLE_PREFIX
        value: guardian-render
      - key: SECRET_KEY
        generateValue: true
```

---

## Design Decisions

### Why NO Redis?

Redis is excellent but adds infrastructure cost and operational complexity. GuardianHealth v2 uses:

- **`cachetools.TTLCache`** for hot-path caching (in-memory, per-process)
- **`slowapi`** with in-memory storage for rate limiting
- **`BackgroundTasks`** for async work instead of Celery + Redis
- **DynamoDB `PAY_PER_REQUEST`** for persistent state and job tracking

This keeps the architecture to **exactly one external service** (DynamoDB).

### Why DynamoDB over MongoDB Atlas?

| Criteria | DynamoDB | MongoDB Atlas |
|---|---|---|
| Always-free tier | **25 GB forever** | 512 MB M0 cluster |
| Serverless scaling | Yes (on-demand) | No (fixed cluster) |
| Cold start | Milliseconds | Seconds (M0 sleeps) |
| IAM integration | Native | Custom |
| Connection strings | None (HTTP API) | Required |

### Why LangGraph over raw LLM calls?

LangGraph provides structured, multi-step clinical reasoning workflows:

1. **PII Detection** -> anonymize patient data
2. **Entity Extraction** -> identify conditions, medications, labs
3. **Risk Stratification** -> compute clinical risk scores
4. **Evidence Retrieval** -> query PubMed for supporting literature
5. **Report Generation** -> synthesize findings into clinician-friendly output

Each step is observable, retryable, and cacheable independently.

---

## Monitoring & Observability

Prometheus metrics are exposed at `/metrics`:

| Metric | Type | Description |
|---|---|---|
| `guardian_requests_total` | Counter | Total HTTP requests by method/endpoint/status |
| `guardian_request_duration_seconds` | Histogram | Request latency distribution |
| `guardian_analyses_total` | Counter | Total AI analyses run |
| `guardian_pii_entities_detected` | Counter | PII entities found/redacted |
| `guardian_pubmed_queries_total` | Counter | NCBI API calls made |
| `guardian_cache_hit_ratio` | Gauge | In-memory cache hit percentage |

No external observability stack required -- scrape with Prometheus or any compatible monitoring tool.

---

## Security Considerations

- **Non-root containers**: Both backend (`guardian` user) and frontend (`nginx` user) run unprivileged
- **PII anonymization**: Microsoft Presidio redacts all patient identifiers before LLM processing
- **JWT stateless auth**: No session storage needed; tokens signed with `SECRET_KEY`
- **DynamoDB encryption**: AWS-managed KMS encryption at rest (enabled by default)
- **CSP headers**: Strict Content Security Policy via nginx configuration
- **Rate limiting**: `slowapi` prevents abuse on all endpoints

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome. Please open an issue first to discuss changes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make changes + add tests
5. Run checks: `black app/ tests/ && ruff check app/ tests/ && pytest`
6. Submit a pull request

---

## Support

- Issues: [GitHub Issues](https://github.com/your-org/guardian-health/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/guardian-health/discussions)

---

> **GuardianHealth v2** -- Clinical intelligence, zero infrastructure cost. Built for developers who ship.
