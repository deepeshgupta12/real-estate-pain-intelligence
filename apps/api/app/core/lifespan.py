from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.sentry import init_sentry
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_sentry()
    settings = get_settings()
    logger = get_logger("app.lifecycle")

    logger.info(
        "Starting application: name=%s env=%s version=%s",
        settings.app_name,
        settings.app_env,
        settings.app_version,
    )

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection check succeeded")
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)

    yield

    logger.info("Shutting down application: name=%s", settings.app_name)