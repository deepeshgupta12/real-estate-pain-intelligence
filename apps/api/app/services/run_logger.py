"""
Per-run file logger utility.

Every pipeline stage (scraping, normalization, multilingual, intelligence,
human-review, retrieval indexing, notion sync) can call `get_run_logger(run_id)`
at the start of its work and `teardown_run_logger(run_id, fh)` at the end.
All calls append to the same  logs/run_{run_id}.log  file, so the entire
lifecycle of a run is captured in one place for easy sharing and debugging.

Usage in any pipeline service:

    from app.services.run_logger import get_run_logger, teardown_run_logger

    run_logger, fh = get_run_logger(run_id)
    try:
        run_logger.info("=== Normalization started for run %d ===", run_id)
        # ... do work ...
    finally:
        teardown_run_logger(run_id, fh)
"""

import logging
from pathlib import Path

# logs/ directory lives at apps/api/logs/ relative to this file:
# apps/api/app/services/run_logger.py  →  parents[2] = apps/api/
_LOGS_DIR = Path(__file__).resolve().parents[2] / "logs"


def get_run_logger(run_id: int) -> tuple[logging.Logger, logging.FileHandler]:
    """
    Return (logger, file_handler) that writes to logs/run_{run_id}.log.

    The FileHandler is returned so the caller can pass it to
    teardown_run_logger() when work is done.  Multiple pipeline stages
    can open and close the handler in sequence — they all append to the
    same file.
    """
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOGS_DIR / f"run_{run_id}.log"

    run_logger = logging.getLogger(f"scrape_run.{run_id}")
    run_logger.setLevel(logging.DEBUG)
    run_logger.propagate = True  # also shows in uvicorn terminal

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")
    )

    # Attach to the common "app" ancestor so all app.* loggers write here,
    # and to the run-specific logger itself.  Do NOT attach to individual
    # child loggers — propagation from "app" covers them without duplicates.
    for name in ["app", f"scrape_run.{run_id}"]:
        lg = logging.getLogger(name)
        # Avoid duplicate handlers if the same run is re-entered within one process
        if not any(
            isinstance(h, logging.FileHandler)
            and getattr(h, "baseFilename", None) == str(log_path)
            for h in lg.handlers
        ):
            lg.addHandler(fh)

    return run_logger, fh


def teardown_run_logger(run_id: int, fh: logging.FileHandler) -> None:
    """Close and detach the FileHandler from loggers wired to this run."""
    for name in ["app", f"scrape_run.{run_id}"]:
        lg = logging.getLogger(name)
        if fh in lg.handlers:
            lg.removeHandler(fh)
    fh.close()
