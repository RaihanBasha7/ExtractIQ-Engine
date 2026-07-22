# ============================================================================
# ExtractIQ Engine - Production Dockerfile
# Multi-stage build for minimal final image size
# ============================================================================

# ── Builder Stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Runtime Stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv

RUN groupadd -r extractiq && \
    useradd -r -g extractiq -d /app -s /usr/sbin/nologin extractiq

WORKDIR /app

COPY app ./app
COPY data ./data
COPY scripts ./scripts

RUN chown -R extractiq:extractiq /app

USER extractiq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT:-8000}/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
