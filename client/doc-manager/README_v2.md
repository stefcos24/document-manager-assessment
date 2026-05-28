# Propylon Document Manager — Backend

Document versioning API built with Django Framework.

## Features

- Token-based authentication with email + password


## Auth flow

### 1. Register a user

```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersafe123","name":"You"}'
# → {"user": {...}, "token": "abc123..."}
```

### 2. Get a token later (login)

```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"supersafe123"}'
# → {"token": "abc123...", "user_id": 1, "email": "..."}
```
