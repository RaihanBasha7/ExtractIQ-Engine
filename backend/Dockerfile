# ============================================================================
# Stage 1: Build dependencies
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================================================
# Stage 2: Runtime image
# ============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN groupadd -r extractiq && useradd -r -g extractiq -d /app -s /sbin/nologin extractiq

COPY --from=builder /root/.local /home/extractiq/.local

COPY app ./app
COPY data ./data
COPY scripts ./scripts

RUN mkdir -p /app/data && chown -R extractiq:extractiq /app/data

ENV PATH=/home/extractiq/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

USER extractiq

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]