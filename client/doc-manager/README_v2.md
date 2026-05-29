# Propylon Document Manager — Backend

Document versioning API built with Django REST Framework.

## Features

- Token-based authentication with email + password
- Upload files of any type to user-defined URL paths
- Automatic versioning (v0, v1, v2 …) per URL per user
- Retrieve any version: `GET /api/documents/{path}?revision=N`
- Content Addressable Storage: `GET /api/cas/{sha256}/`
- Per-version read permissions (private / public)
- Full user isolation — users can only access their own files

## Requirements

- Python 3.11
- GNU Make

## Setup

```bash
make build      # create venv and install dependencies
make migrate    # apply database migrations
make serve      # start dev server on http://localhost:8001
make test       # run test suite
```

## Auth

### Register

```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Propylon2026","name":"You"}'
# → {"user": {...}, "token": "abc123..."}
```

### Login

```bash
curl -X POST http://localhost:8001/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Propylon2026"}'
# → {"token": "abc123...", "user_id": 1, "email": "..."}
```

All subsequent requests require `Authorization: Token <your_token>`.

## API Endpoints

| Method | URL | Auth | Description                   |
|--------|-----|------|-------------------------------|
| `POST` | `/api/auth/register/` | No | Create user + return token    |
| `POST` | `/api/auth/login/` | No | Email + password = token      |
| `GET`  | `/api/file_versions/` | Yes | List my file versions         |
| `GET`  | `/api/file_versions/{id}/` | Yes | Detail one version            |
| `POST` | `/api/file_versions/upload/` | Yes | Upload file (auto-versioned)  |
| `GET`  | `/api/documents/{path}` | Yes | Retrieve latest version       |
| `GET`  | `/api/documents/{path}?revision=N` | Yes | Retrieve specific revision    |
| `GET`  | `/api/cas/{sha256}/` | Yes | Retrieve file by content hash |

## Upload

```bash
curl -X POST http://localhost:8001/api/file_versions/upload/ \
  -H "Authorization: Token abc123..." \
  -F "file=@review.pdf" \
  -F "file_url=documents/reviews/review.pdf" \
  -F "read_permission=public"   # optional, default is "private"
```

## Retrieve by URL

```bash
# latest version
curl -H "Authorization: Token abc123..." \
  http://localhost:8001/api/documents/documents/reviews/review.pdf

# specific revision
curl -H "Authorization: Token abc123..." \
  "http://localhost:8001/api/documents/documents/reviews/review.pdf?revision=0"
```

## Retrieve by Hash (CAS)

```bash
curl -H "Authorization: Token abc123..." \
  http://localhost:8001/api/cas/<sha256_hex>/
```

## Read Permissions

Each uploaded version has a `read_permission` field:

- `private` (default) — only the owner can read
- `public` — any authenticated user can read via document URL or CAS

Write access (uploading new versions) is always restricted to the owner.
