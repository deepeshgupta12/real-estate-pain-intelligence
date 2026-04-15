# ── Stage 1: Build dependencies ──────────────────────────────────────────────
# Pin to bookworm (Debian stable). python:3.11-slim now resolves to trixie
# (Debian testing) whose apt mirrors are unreliable inside Docker builds.
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install build tools — use --fix-missing and retry to handle transient apt failures
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/* \
    || (sleep 5 && apt-get update --fix-missing && apt-get install -y --no-install-recommends \
        build-essential libpq-dev gcc curl \
        && rm -rf /var/lib/apt/lists/*)

# Copy dependency file
COPY pyproject.toml ./

# Install dependencies into a prefix
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-warn-script-location .

# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Runtime system deps only — with retry on transient network failure
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    || (sleep 5 && apt-get update --fix-missing && apt-get install -y --no-install-recommends \
        libpq5 curl \
        && rm -rf /var/lib/apt/lists/*)

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
