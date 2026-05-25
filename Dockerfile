# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# copy mode = copy (not hardlink) so the venv survives the multi-stage COPY
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock* ./

# Install all production deps; skip installing the project wheel itself
RUN uv sync --no-dev --no-install-project

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the fully-built venv (files, not hardlinks → works across stages)
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY . .

ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Use absolute paths — no PATH dependency, no shell resolution issues
CMD ["/bin/sh", "-c", "/app/.venv/bin/alembic upgrade head && /app/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1"]
