# ==========================================
# Stage 1: Builder — install dependencies
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build essentials for packages with native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a virtual environment
COPY backend/pyproject.toml backend/requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime — lean production image
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime utilities (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r guardian && useradd -r -g guardian -d /app guardian

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code and reference data
COPY backend/app ./app
COPY backend/data ./data
COPY backend/handler.py ./handler.py
COPY backend/scripts ./scripts

# Set proper permissions
RUN chown -R guardian:guardian /app

# Switch to non-root user
USER guardian

# Expose application port
EXPOSE 8000

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn (single process, background tasks via asyncio)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
