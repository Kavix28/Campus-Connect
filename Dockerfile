# =====================================================================
# ENTERPRISE PRODUCTION DOCKERFILE — Oudience Chatbot
# =====================================================================
# Multi-stage build optimized for minimal image size and layer caching.
# Stage 1 (deps):    Install Python dependencies into a venv
# Stage 2 (models):  Download ML models into a dedicated layer
# Stage 3 (final):   Slim runtime with only what's needed
# =====================================================================

# ---------------------------
# Stage 1: Dependency Builder
# ---------------------------
FROM python:3.10-slim-bookworm AS deps

WORKDIR /build

# Install only the build-time system packages needed for pip compiles
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Create isolated venv so we can COPY it cleanly into the final stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python deps (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn


# ---------------------------
# Stage 2: Model Downloader
# ---------------------------
FROM deps AS models

ENV HF_HOME=/model_cache

# Copy only the download script — keeps the layer cache narrow
COPY scripts/download_models.py /build/scripts/
RUN python /build/scripts/download_models.py


# ---------------------------
# Stage 3: Production Runtime
# ---------------------------
FROM python:3.10-slim-bookworm AS final

# OCI image metadata labels
LABEL org.opencontainers.image.title="Oudience Chatbot" \
    org.opencontainers.image.description="AI Customer Support Chatbot with RAG" \
    org.opencontainers.image.vendor="Oudience" \
    org.opencontainers.image.source="https://github.com/kavix28/oudience-chatbot"

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Runtime-only system dependency (curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy venv from deps stage (no build-essential bloat)
COPY --from=deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy cached models from models stage (separate layer — rarely changes)
COPY --from=models /model_cache /app/model_cache
ENV HF_HOME=/app/model_cache \
    TRANSFORMERS_CACHE=/app/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Copy application source
COPY . .

# Create runtime directories with correct ownership
RUN mkdir -p /app/flask_sessions /app/uploads /app/logs /app/data && \
    chown -R appuser:appgroup /app

# Drop to non-root
USER appuser

# Python runtime tuning
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py

# Healthcheck (longer start_period for model loading)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/test/system/health || exit 1

EXPOSE 5001

# Gunicorn with preload to share model memory across workers
CMD ["gunicorn", \
    "--bind", "0.0.0.0:5001", \
    "--workers", "2", \
    "--threads", "4", \
    "--timeout", "120", \
    "--preload", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "app:app"]
