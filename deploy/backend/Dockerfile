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

# SPEC-0023: OCR de imagem (Tesseract, idioma pt) e normalização de DOC/PPT/XLS
# (LibreOffice headless). São binários de sistema, não dependências Python.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-por \
        libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

# HOME do usuário `app` é /app: o LibreOffice grava o perfil em ~/.config.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/output/uploads /app/.config /app/.cache \
    && chown -R app:app /app/output /app/.config /app/.cache

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./

USER app

EXPOSE 8000

CMD []
