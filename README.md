# HWC-Quiniela-Back

## Install and compiler

```cmd
# 1. Reinstall deps with fixed pyproject.toml
uv sync

# 2. Start Docker Compose (DB + API, runs migrations automatically)
docker compose up --build

# ─── OR: run locally without Docker ───────────────────────────────
# Terminal 1 – start postgres
docker compose up db

# Terminal 2 – migrate + run
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

```