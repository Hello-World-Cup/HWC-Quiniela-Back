# HWC Quiniela — Backend Documentation

World Cup 2026 sports predictions API. Python/FastAPI, async SQLAlchemy, PostgreSQL.

---

## Stack

| Layer | Tech |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 async |
| DB | PostgreSQL 16 |
| Migrations | Alembic |
| Package manager | uv |
| Runtime | Docker + Docker Compose |

---

## Project structure

```
src/
  main.py              # FastAPI app, CORS, router registration
  core/
    config.py          # Settings via pydantic-settings (.env)
    database.py        # Async engine + session factory + Base
    dependencies.py    # get_current_user dependency
    security.py        # JWT create / decode (python-jose)
  auth/
    models.py          # User
    schemas.py         # GoogleLoginRequest, TokenResponse
    services.py        # AuthService — Google OAuth2 token verify + upsert user
    routers.py         # POST /auth/google
  matches/
    models.py          # Team, Match, MatchStatus enum
    schemas.py         # TeamResponse, MatchResponse
    services.py        # MatchService — list + get by id
    routers.py         # GET /matches
  predictions/
    models.py          # Prediction
    schemas.py         # PredictionCreate, PredictionResponse
    services.py        # PredictionService — upsert + list user predictions
    routers.py         # POST /predictions, GET /predictions/me
alembic/
  versions/
    0001_add_prediction_deadline_to_matches.py
```

---

## Authentication

- Google OAuth2 only. Client sends a Google ID token to `POST /auth/google`.
- Server validates it with `google-auth` library against `GOOGLE_CLIENT_ID`.
- Returns a signed JWT (HS256). All protected routes require `Authorization: Bearer <token>`.
- Token TTL: 7 days (`ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7`).

---

## Domain: Matches

### Model — `Match`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| team_a_id | FK → teams | |
| team_b_id | FK → teams | |
| start_time | timestamptz | Actual kick-off time |
| prediction_deadline | timestamptz NULL | Optional cutoff for predictions. If NULL, `start_time` is used as deadline |
| result_a | int NULL | Set after match ends |
| result_b | int NULL | Set after match ends |
| status | enum | `pending` / `in_progress` / `finished` |
| venue | str NULL | |
| group | str(1) NULL | A–H |
| round | str(50) NULL | e.g. "Group Stage", "Round of 16" |

### Model — `Team`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| name | str(100) | |
| code | str(3) unique | ISO 3-letter code |
| group | str(1) NULL | |
| flag_url | str(500) NULL | |

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | /matches | No | List matches. Query params: `date` (YYYY-MM-DD), `group` (A-H), `status` |

---

## Domain: Predictions

### Model — `Prediction`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| user_id | FK → users | |
| match_id | FK → matches | |
| predicted_score_a | int | ≥ 0 |
| predicted_score_b | int | ≥ 0 |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Unique constraint: `uq_user_match (user_id, match_id)` — one prediction per user per match.

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /predictions | Required | Create or update a prediction (upsert) |
| GET | /predictions/me | Required | List authenticated user's predictions |

### Deadline security rule

`PredictionService._assert_deadline` is called on every upsert (create **and** update):

```
cutoff = match.prediction_deadline  if set
         match.start_time           otherwise

if now(UTC) >= cutoff → HTTP 403 "El periodo para realizar pronósticos ha cerrado"
```

This means:
- If `prediction_deadline` is `NULL`, predictions close at kick-off.
- If `prediction_deadline` is set (e.g., 1 hour before kick-off), predictions close at that earlier time.
- The check runs on every write — you cannot bypass it by creating the prediction early and then editing it.

---

## Domain: Auth

### Model — `User`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| email | str(255) unique | |
| google_id | str(255) unique | Google `sub` claim |
| full_name | str(255) | |
| is_active | bool | Default true. Inactive users are rejected at auth |
| created_at | timestamptz | |

---

## Configuration (`.env`)

| Variable | Default | Notes |
|---|---|---|
| DATABASE_URL | postgresql+asyncpg://quiniela:quiniela_secret@localhost:5432/quiniela | |
| SECRET_KEY | change-me-in-production | **Must be changed in prod** |
| ALGORITHM | HS256 | |
| ACCESS_TOKEN_EXPIRE_MINUTES | 10080 (7 days) | |
| GOOGLE_CLIENT_ID | *(empty)* | Required for Google login |
| GOOGLE_CLIENT_SECRET | *(empty)* | Currently unused by the server |

---

## Running locally

```bash
# Start only the DB
docker compose up db

# Apply migrations
uv run alembic upgrade head

# Start API with hot-reload
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Running with Docker

```bash
docker compose up --build
```

Migrations run automatically on container startup (see `Dockerfile`).

---

## Migrations

Migrations live in `alembic/versions/`. To create a new one after a model change:

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

### History

| Rev | Description |
|---|---|
| 0001 | Add `prediction_deadline` column to `matches` table |

---

## Architecture decisions

- **Screaming / DDD layout**: each domain folder (`auth`, `matches`, `predictions`) is self-contained with its own `models`, `schemas`, `services`, `routers`. Cross-domain imports are explicit (predictions imports from matches).
- **Upsert pattern**: select-then-update-or-insert instead of `ON CONFLICT` to stay ORM-clean and keep business logic readable.
- **Deadline as match field**: `prediction_deadline` lives on `Match` so admins can configure per-match cutoffs without touching application code. Falls back to `start_time` when `NULL`.
- **No password auth**: only Google OAuth2 to reduce auth surface area.
