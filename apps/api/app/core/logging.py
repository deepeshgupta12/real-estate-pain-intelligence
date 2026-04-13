"""
Enhanced structured logging with correlation ID injection.
Outputs JSON in production, colored text in development.
"""
import logging
import sys
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get() or str(uuid.uuid4())[:8]


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def setup_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """Configure root logger with optional JSON output."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    if json_format:
        try:
            import json_log_formatter
            formatter = json_log_formatter.JSONFormatter()
        except ImportError:
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s [%(request_id)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)

    # Suppress noisy libraries
    for noisy in ["httpx", "httpcore", "urllib3", "passlib"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def configure_logging() -> None:
    """Legacy function for backward compatibility."""
    from app.core.config import get_settings
    settings = get_settings()
    json_mode = settings.app_env == "production"
    setup_logging(log_level=settings.log_level, json_format=json_mode)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
