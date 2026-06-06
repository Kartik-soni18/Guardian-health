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
  "chat_id": "optional-session-id"
}
```

When the request is **authenticated** and includes `chat_id`, the server loads conversation history from MongoDB and **ignores** any client-sent `conversation_history`. Without `chat_id`, triage runs as a single-turn request.

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

## Chats

All chat endpoints require authentication.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/chats` | List current user's chats |
| `POST` | `/api/v1/chats` | Create a new chat |
| `GET` | `/api/v1/chats/{chat_id}` | Get chat with messages |
| `DELETE` | `/api/v1/chats/{chat_id}` | Delete chat and its messages |

### Create chat body

```json
{
  "initialMessage": "I have a fever"
}
```

`initialMessage` is optional and sets the chat title.

Messages are persisted automatically when triage runs with a `chat_id`. User message content is PII-scrubbed before storage.

## Rate Limits

| Endpoint group | Limit |
|---|---|
| Health | 100/minute |
| Register | 5/minute |
| Login | 10/minute |
| Refresh | 20/minute |
| Triage | 10/minute |
| Chats | 30/minute |
