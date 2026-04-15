#!/usr/bin/env bash
# install-extras.sh — Install packages that cannot live in pyproject.toml
# due to dependency conflicts.
#
# Usage:
#   cd apps/api
#   bash ../../scripts/install-extras.sh
#
# Why this is needed:
#   app-store-scraper==0.3.5 depends on requests==2.23.0 which pins urllib3<1.26.
#   This conflicts with sentry-sdk>=1.40.0 (requires urllib3>=1.26.2).
#   Installing with --no-deps bypasses the conflict; urllib3 from the main venv
#   (which satisfies sentry-sdk) is used at runtime and is fully compatible.
#
# This script is idempotent — safe to run multiple times.

set -euo pipefail

echo "==> Installing extras (dependency-conflict packages) ..."

# Detect active virtualenv or use the project .venv
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
    PIP="$VIRTUAL_ENV/bin/pip"
elif [[ -f ".venv/bin/pip" ]]; then
    PIP=".venv/bin/pip"
elif command -v pip &>/dev/null; then
    PIP="pip"
else
    echo "ERROR: pip not found. Activate your virtualenv or run from apps/api/."
    exit 1
fi

echo "==> Using pip: $PIP"

# app-store-scraper — iOS App Store review fetcher
# Must be installed with --no-deps to avoid urllib3 conflict.
echo "==> Installing app-store-scraper==0.3.5 (--no-deps) ..."
"$PIP" install --no-deps "app-store-scraper==0.3.5"

echo ""
echo "✓ Extras installed successfully."
echo ""
echo "Installed packages:"
"$PIP" show app-store-scraper 2>/dev/null | grep -E "^(Name|Version):" || true
