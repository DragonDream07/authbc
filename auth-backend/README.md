# auth-backend

FastAPI authentication service providing JWT-based login, registration, password reset, and token refresh.

---

## Overview

This service exposes a self-contained REST API for all authentication operations. It is designed to be consumed by the `auth-frontend` React application but is fully decoupled and usable by any HTTP client.

**Stack**

- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy (async-compatible) + psycopg (PostgreSQL)
- python-jose (JWT)
- passlib / bcrypt (password hashing)
- Pydantic v2 (request / response schemas)

---

## Endpoints

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/auth/register` | `register` | Create a new user account |
| POST | `/auth/login` | `login` | Authenticate and receive tokens |
| GET | `/auth/me` | `me` | Return the current authenticated user |
| POST | `/auth/logout` | `logout` | Revoke the current refresh token |
| POST | `/auth/refresh` | `refresh` | Rotate the refresh token and issue a new access token |
| POST | `/auth/forgot-password` | `forgotPassword` | Send a password-reset email |
| POST | `/auth/reset-password` | `resetPassword` | Consume a reset token and set a new password |

---

## Database tables

| Table | Model class | Purpose |
|-------|-------------|--------|
| `users` | `User` | Core user records |
| `password_resets` | `PasswordReset` | Single-use password reset tokens (stored hashed) |
| `refresh_tokens` | `RefreshToken` | Refresh token registry (stored hashed, rotated on use) |

---

## Prerequisites

- Docker + Docker Compose **or** Python 3.12 + a running PostgreSQL instance
- An SMTP server (or a local mail catcher such as MailHog) for password-reset emails

---

## Quick start with Docker Compose

From the repository root:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.
Interactive docs are at `http://localhost:8000/docs`.

---

## Local development setup

1. **Clone and enter the service directory**

   ```bash
   cd auth-backend
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env and fill in real values
   ```

5. **Apply database migrations** (run the schema script against your PostgreSQL instance)

   ```bash
   psql "$DATABASE_URL" -f ../schema.sql
   ```

6. **Start the development server**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## Running tests

```bash
pytest
```

Tests cover the full authentication flow: register → login → refresh → forgot-password → reset-password → logout, plus negative cases (duplicate email, weak password, password mismatch, expired/used reset token).

---

## Environment variables

Copy `.env.example` to `.env` and set each variable before starting the server. Every variable is **required** unless a default is noted.

### Database

| Variable | Description | Example |
|----------|-------------|--------|
| `DATABASE_URL` | Full SQLAlchemy connection URL for PostgreSQL via psycopg | `postgresql+psycopg://user:password@localhost:5432/auth_db` |

### JWT

| Variable | Description | Example |
|----------|-------------|--------|
| `JWT_SECRET_KEY` | Long random secret used to sign access tokens — **keep secret** | `change-me-to-a-long-random-secret` |
| `JWT_ALGORITHM` | Signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | Access token lifetime in minutes | `15` |

### Password hashing

| Variable | Description | Example |
|----------|-------------|--------|
| `BCRYPT_ROUNDS` | bcrypt work factor (minimum 12) | `12` |

### Password reset

| Variable | Description | Example |
|----------|-------------|--------|
| `RESET_TOKEN_TTL_MINUTES` | How long a password-reset link remains valid | `60` |

### Refresh tokens

| Variable | Description | Example |
|----------|-------------|--------|
| `REFRESH_TOKEN_TTL_DAYS` | Default refresh token lifetime in days | `7` |
| `REFRESH_TOKEN_TTL_DAYS_REMEMBER_ME` | Refresh token lifetime when "remember me" is selected | `30` |

### SMTP

| Variable | Description | Example |
|----------|-------------|--------|
| `SMTP_HOST` | Mail server hostname | `smtp.example.com` |
| `SMTP_PORT` | Mail server port | `587` |
| `SMTP_USERNAME` | SMTP authentication username | `no-reply@example.com` |
| `SMTP_PASSWORD` | SMTP authentication password — **keep secret** | `change-me` |
| `SMTP_FROM_ADDRESS` | Envelope / display From address | `no-reply@example.com` |
| `SMTP_USE_TLS` | Enable STARTTLS (`true` / `false`) | `true` |

### Rate limiting

| Variable | Description | Example |
|----------|-------------|--------|
| `RATE_LIMIT_LOGIN_MAX_ATTEMPTS` | Maximum login attempts per window | `5` |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS` | Login rate-limit window duration in seconds | `60` |
| `RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS` | Maximum forgot-password requests per window | `3` |
| `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS` | Forgot-password rate-limit window duration in seconds | `300` |

### Application

| Variable | Description | Example |
|----------|-------------|--------|
| `APP_BASE_URL` | Public base URL of the frontend — used in reset-password email links | `http://localhost:3000` |
| `CORS_ORIGIN` | Allowed CORS origin for the frontend | `http://localhost:3000` |

---

## Project structure

```
auth-backend/
├── app/
│   ├── main.py               # FastAPI application factory, CORS, router inclusion
│   ├── config.py             # Pydantic settings (reads .env)
│   ├── database.py           # SQLAlchemy engine and session factory
│   ├── auth/
│   │   ├── router.py         # FastAPI router — all /auth/* endpoints
│   │   ├── service.py        # Business logic (login, register, reset, refresh, …)
│   │   └── schemas.py        # Pydantic request / response models
│   └── models/
│       ├── user.py           # User ORM model
│       ├── password_reset.py # PasswordReset ORM model
│       └── refresh_token.py  # RefreshToken ORM model
├── tests/
│   └── test_auth.py          # pytest integration tests
├── .env.example              # Environment variable template
├── Dockerfile
└── requirements.txt
```

---

## Security notes

- Passwords are hashed with **bcrypt** at the configured work factor; plaintext passwords are never stored or logged.
- Password-reset and refresh tokens are stored as **SHA-256 hashes**; the raw token is sent only once (in the email or response) and never persisted.
- Login and forgot-password endpoints are **rate-limited** (configurable via env).
- Forgot-password always returns HTTP 202 regardless of whether the email exists (**enumeration resistance**).
- Login failures always return `"Invalid email or password."` without distinguishing unknown email from wrong password.
- Refresh tokens **rotate on use**; the previous token is revoked immediately.
- All tokens must be transmitted over HTTPS in production.
