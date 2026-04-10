from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger = get_logger("app.lifecycle")

    logger.info(
        "Starting application: name=%s env=%s version=%s",
        settings.app_name,
        settings.app_env,
        settings.app_version,
    )

    yield

    logger.info("Shutting down application: name=%s", settings.app_name)