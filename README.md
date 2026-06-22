# Notification Service

A FastAPI microservice for real-time notifications — built as a companion service to the [JobBoard API](https://github.com/Apurvastha/jobboard).

## Live Demo

> Deployment coming on Day 7 — Railway

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
- [ ] WebSocket real-time push (Day 6)
- [ ] Background tasks (Day 4)
- [ ] Docker + Railway deployment (Day 7)

---

## Project Structure

```
notification-service/
├── app/
│   ├── main.py           # FastAPI app, routers, lifespan
│   ├── config.py         # Pydantic settings — reads from .env
│   ├── database.py       # Async SQLAlchemy engine + session
│   ├── models.py         # SQLAlchemy models (User, Notification)
│   ├── schemas.py        # Pydantic schemas — request/response
│   ├── auth.py           # Password hashing + JWT utilities
│   ├── dependencies.py   # Shared dependencies (get_current_user)
│   └── routers/
│       ├── auth.py       # POST /auth/register, /auth/token, /auth/me
│       └── notifications.py  # CRUD notification endpoints
├── alembic/              # Alembic migration config
│   ├── env.py
│   └── versions/         # Migration files
├── tests/
│   └── test_notifications.py
├── .env.example
├── requirements.txt
└── Dockerfile            # coming Day 7
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
- Swagger UI: http://127.0.0.1:8001/docs
- ReDoc: http://127.0.0.1:8001/redoc
- Health: http://127.0.0.1:8001/health

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
  POST  /notifications/             # create notification (service-to-service)
  GET   /notifications/             # list user's notifications (requires auth)
  GET   /notifications/unread-count # count unread (requires auth)
  GET   /notifications/{id}         # get single notification (requires auth)
  PATCH /notifications/{id}/read    # mark as read (requires auth)
  PATCH /notifications/mark-all-read # mark all as read (requires auth)
  DELETE /notifications/{id}        # delete notification (requires auth)

System
  GET   /health                     # health check
```

---

## Quick Start (Swagger UI)

1. Open http://127.0.0.1:8001/docs
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

This service is designed as a microservice companion to JobBoard:

```
JobBoard API (Django)
    ↓ POST /notifications/ (internal call)
Notification Service (FastAPI)
    ↓ stores in PostgreSQL
    ↓ pushes via WebSocket (Day 6)
Frontend / Mobile client
```

JobBoard calls `POST /notifications/` when:
- A candidate applies to a job → notify the company
- A company changes application status → notify the candidate
- A new job matches a candidate's profile → notify the candidate

---

## Project Status

Actively in development — Week 6 of backend engineering roadmap.

**Roadmap:**
- [x] Day 1: FastAPI setup, async SQLAlchemy, Pydantic
- [x] Day 2: Alembic migrations, query patterns, bulk operations
- [x] Day 3: JWT auth, bcrypt, protected endpoints
- [ ] Day 4: Background tasks, middleware
- [ ] Day 5: pytest + httpx testing
- [ ] Day 6: WebSocket real-time push
- [ ] Day 7: Docker + Railway deployment