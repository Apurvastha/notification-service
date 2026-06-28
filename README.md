# Notification Service

A FastAPI microservice for real-time notifications — built as a companion service to the [JobBoard API](https://github.com/Apurvastha/jobboard).

## Live Demo
[![CI](https://github.com/Apurvastha/notification-service/actions/workflows/ci.yml/badge.svg)](https://github.com/Apurvastha/notification-service/actions/workflows/ci.yml)
> [Notification-Service](https://notification-service-production-ae8f.up.railway.app/docs)

---

## Tech Stack

- **Backend:** Python 3.11, FastAPI
- **Database:** PostgreSQL 15 (async SQLAlchemy 2.0)
- **Migrations:** Alembic
- **Auth:** JWT (python-jose) + bcrypt password hashing
- **Validation:** Pydantic v2
- **Server:** Uvicorn (ASGI)

---

## Features

- [x] Async SQLAlchemy 2.0 with PostgreSQL
- [x] Alembic migrations with autogenerate
- [x] JWT authentication with custom claims
- [x] bcrypt password hashing
- [x] User registration and login
- [x] Create notifications (service-to-service)
- [x] List notifications with filtering (unread, type)
- [x] Mark single notification as read
- [x] Bulk mark all as read
- [x] Unread count endpoint
- [x] Delete notification
- [x] Pydantic v2 request/response validation
- [x] Dependency injection via Depends()
- [x] CORS middleware
- [x] Health check endpoint
- [x] WebSocket real-time push
- [x] Background tasks
- [x] Docker + Railway deployment

---

## Project Structure

```
notification-service/
├── app/
│   ├── main.py               # FastAPI app, routers, lifespan
│   ├── config.py             # Pydantic settings — reads from .env
│   ├── database.py           # Async SQLAlchemy engine + session
│   ├── models.py             # SQLAlchemy models (User, Notification)
│   ├── schemas.py            # Pydantic schemas — request/response
│   ├── auth.py               # Password hashing + JWT utilities
│   ├── dependencies.py       # Shared dependencies (get_current_user)
│   ├── middleware.py         # Custom middleware(Audit, Response time)
│   ├── tasks.py              # Background tasks
│   ├── test_config.py        # Pytest config
│   ├── websocket_manager.py  # Websocket connection
│   └── routers/
│       ├── auth.py           # POST /auth/register, /auth/token, /auth/me
│       └── notifications.py  # CRUD notification endpoints
│       └── websocket.py      # websocket endpoints
├── alembic/              # Alembic migration config
│   ├── env.py
│   └── versions/         # Migration files
├── tests/
│   └── __init__.py
│   └── conftest.py
│   └── test_auth.py
│   └── test_middleware.py
│   └── test_notifications.py
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── pytest.ini
├── railway.toml
├── Dockerfile
├── .gitignore
├── .dockerignore
└── README.md          
           
            
```

---

## Local Setup

```bash
git clone https://github.com/Apurvastha/notification-service.git
cd notification-service
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # fill in your values
```

Create the PostgreSQL database:

```bash
psql -U postgres -c "CREATE DATABASE notifications;"
```

Run migrations:

```bash
export PYTHONPATH=.
alembic upgrade head
```

Start the server:

```bash
uvicorn app.main:app --reload --port 8001
```

Visit:
- Swagger UI: http://localhost:8001/docs
- Health: http://localhost:8001/health

---

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/notifications
SECRET_KEY=your-secret-key-here
DEBUG=True
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## API Endpoints

```
Authentication
  POST  /auth/register              # create user account
  POST  /auth/token                 # login — returns JWT access token
  GET   /auth/me                    # current user info (requires auth)

Notifications
  POST  /notifications/                          # create notification (service-to-service)
  GET   /notifications/                          # list user's notifications (requires auth)
  GET   /notifications/unread-count              # count unread (requires auth)
  GET   /notifications/{notification_id}         # get single notification (requires auth)
  PATCH /notifications/{notification_id}/read    # mark as read (requires auth)
  PATCH /notifications/read-all                  # mark all as read (requires auth)
  DELETE /notifications/{id}                     # delete notification (requires auth)

System
  GET   /health                                  # health check
```

---

## Quick Start (Swagger UI)

1. Open https://notification-service-production-ae8f.up.railway.app/docs
2. `POST /auth/register` with email, username, password
3. `POST /auth/token` with username and password
4. Click **Authorize** → paste the `access_token`
5. `POST /notifications/` to create a notification for your user_id
6. `GET /notifications/` to see your notifications

---

## Filtering

```bash
# unread only
GET /notifications/?unread_only=true

# by type
GET /notifications/?notification_type=application

# pagination
GET /notifications/?skip=0&limit=10

# combined
GET /notifications/?unread_only=true&notification_type=status_change&limit=5
```

---

## Migrations

```bash
# generate new migration after model changes
alembic revision --autogenerate -m "describe the change"

# apply all pending migrations
alembic upgrade head

# rollback one migration
alembic downgrade -1

# see migration history
alembic history

# check current state
alembic current
```

---

## Architecture

This service is the real-time delivery layer for [JobBoard](https://github.com/Apurvastha/jobboard).
Company changes application status in JobBoard

```
→ Django signal detects old vs new status

→ Celery fires POST /notifications/ to this service

→ Notification stored in PostgreSQL

→ WebSocket push to candidate's active connection

→ Candidate sees update instantly without refreshing
```

**Shared JWT** — both services use the same signing secret. A token issued by JobBoard is valid here. Candidates connect to the WebSocket using their JobBoard token — no separate registration required.

## Quick Start with JobBoard

1. Login to [JobBoard](https://jobboard-production-aae7.up.railway.app/api/schema/swagger-ui/) and get your access token
2. Connect WebSocket using that token:
```bash
wscat -c "wss://notification-service-production-ae8f.up.railway.app/ws/notifications?token=<your_jobboard_token>"
```
3. Trigger a status change in JobBoard — notification arrives in real time
---

## Project Status

Actively in development

