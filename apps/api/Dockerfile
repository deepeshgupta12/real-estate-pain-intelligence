# ── Stage 1: Build dependencies ──────────────────────────────────────────────
# Use the full python:3.11 image for the builder — it already ships with
# gcc, build-essential, and libpq-dev, so zero apt-get calls are needed.
# This avoids the deb.debian.org connectivity failures seen in slim builds.
FROM python:3.11 AS builder

WORKDIR /build

# Copy the package descriptor and source — setuptools needs the app/ directory
# to build the wheel (declared in [tool.setuptools] packages = ["app"])
COPY pyproject.toml ./
COPY app/ ./app/

# Install all declared dependencies into an isolated prefix
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-warn-script-location .

# app-store-scraper pins requests==2.23.0 which conflicts with sentry-sdk's
# urllib3 requirement. Install it WITHOUT its dependencies — requests is
# already present at a compatible newer version from the main install above.
RUN pip install --prefix=/install --no-deps app-store-scraper==0.3.5

# ── Stage 2: Runtime image ────────────────────────────────────────────────────
# python:3.11-slim for a lean runtime image.
# psycopg[binary] bundles its own libpq, so no apt-get install needed.
# The healthcheck uses Python's built-in urllib — no curl dependency.
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser

# Health check — uses Python stdlib, no curl needed
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, sys; urllib.request.urlopen('http://localhost:8000/health'); sys.exit(0)" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
