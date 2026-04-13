"""Sentry error tracking integration."""
import logging

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry if SENTRY_DSN is configured."""
    import os
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        from app.core.config import get_settings
        settings = get_settings()

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
            environment=settings.app_env,
            release=settings.app_version,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
        logger.info(f"Sentry initialized for environment: {settings.app_env}")
    except ImportError:
        logger.warning("sentry-sdk not installed, error tracking disabled")
    except Exception as exc:
        logger.warning(f"Sentry initialization failed: {exc}")
