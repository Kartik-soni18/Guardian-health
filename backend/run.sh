#!/bin/bash
# Lambda Web Adapter entrypoint — runs uvicorn for FastAPI on port 8080.
set -euo pipefail

: "${PORT:=8080}"

exec python -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 1 \
  --timeout-keep-alive 30 \
  --proxy-headers \
  --forwarded-allow-ips='*'
