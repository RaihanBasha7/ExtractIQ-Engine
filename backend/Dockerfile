# ============================================================================
# Stage 1: Build dependencies
# ============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/requirements.txt .

# Install to user site-packages for cleaner copy
RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================================================
# Stage 2: Runtime image
# ============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r extractiq && useradd -r -g extractiq -d /app -s /sbin/nologin extractiq

# Copy installed packages from builder
COPY --from=builder /root/.local /home/extractiq/.local

# Copy application code
COPY backend/app/ ./app/
COPY backend/data/ ./data/
COPY backend/scripts/ ./scripts/

# Create data directory with proper permissions
RUN mkdir -p /app/data && chown -R extractiq:extractiq /app/data

# Set environment
ENV PATH=/home/extractiq/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Switch to non-root user
USER extractiq

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
