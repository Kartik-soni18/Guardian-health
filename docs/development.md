# Development

## Backend Tests

```bash
cd backend
pip install -e ".[dev]"

# All tests (mock mode, no API keys needed)
MOCK_MODE=true pytest -v

# With coverage
pytest --cov=app --cov-report=term-missing
```

## Linting

```bash
black app/ tests/
ruff check app/ tests/
```

## Frontend

```bash
cd frontend
npm ci
npm run build
npm run dev
```

## Mock Mode

Set `MOCK_MODE=true` to skip Together.ai calls. Tests use deterministic LLM fixtures so they pass without external API keys.

## Adding Prompt Changes

Prompts live in `backend/app/agents/prompts/`. Keep them concise — the pipeline passes compact context to reduce token usage.

## Dataset Updates

Place updated CSV files in `backend/data/`. The symptom dataset service loads `Indian-Healthcare-Symptom-Disease-Dataset.csv` at startup and caches lookups in Redis.
