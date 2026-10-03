# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.12.15 AS uv

FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_SYNC=1

WORKDIR /app

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/output/uploads \
    && chown -R app:app /app/output

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

USER app

EXPOSE 8000

CMD []
