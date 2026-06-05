# API Reference

Base path: `/api/v1`

Interactive docs are available at `/docs` when `DEBUG=true`.

## Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness and dependency status |
| `GET` | `/health/ready` | Readiness probe |
| `GET` | `/health/live` | Simple alive check |

## Auth

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Obtain JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/me` | Current user profile |

### Register body

```json
{
  "username": "jane_doe",
  "email": "jane@example.com",
  "password": "SecurePass1!",
  "full_name": "Jane Doe"
}
```

### Triage

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/triage` | Run LangGraph triage pipeline |

### Triage request

```json
{
  "query": "I have had fever and joint pain for 3 days",
  "chat_id": "optional-session-id",
  "conversation_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

### Triage response

```json
{
  "response": "Triage guidance text...",
  "triage_level": "urgent",
  "routing": "triage",
  "symptoms": ["fever", "joint_pain"],
  "reasoning": "Clinical reasoning summary",
  "compliance_passed": true,
  "audit_hash": "abc123",
  "disclaimer": "Educational only..."
}
```

## Rate Limits

| Endpoint group | Limit |
|---|---|
| Health | 100/minute |
| Register | 5/minute |
| Login | 10/minute |
| Refresh | 20/minute |
| Triage | 10/minute |
