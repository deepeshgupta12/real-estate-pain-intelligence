import logging
import logging.handlers
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.scrapers.registry import ScraperRegistry
from app.scrapers.utils import build_dedupe_key
from app.services.orchestrator import OrchestratorService

_module_logger = logging.getLogger(__name__)

# Directory where per-run log files are written.  Created on first use.
_LOGS_DIR = Path(__file__).resolve().parents[3] / "logs"


def _get_run_logger(run_id: int) -> tuple[logging.Logger, logging.FileHandler]:
    """
    Return a logger that writes to logs/run_{run_id}.log.
    The FileHandler is returned so the caller can close it when done.
    """
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOGS_DIR / f"run_{run_id}.log"

    run_logger = logging.getLogger(f"scrape_run.{run_id}")
    run_logger.setLevel(logging.DEBUG)
    run_logger.propagate = True  # also shows in main uvicorn log

    # Avoid duplicate handlers if logger is reused within a process
    if not any(
        isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(log_path)
        for h in run_logger.handlers
    ):
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")
        )
        run_logger.addHandler(fh)

    # Also wire root scraper loggers to this file for the duration of this run
    for name in [
        "app.scrapers.sources.app_reviews",
        "app.scrapers.sources.review_sites",
        "app.scrapers.sources.reddit",
        "app.scrapers.sources.youtube",
        "app.scrapers.sources.x_posts",
        "app.scrapers",
        __name__,
    ]:
        scraper_logger = logging.getLogger(name)
        if not any(
            isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", None) == str(log_path)
            for h in scraper_logger.handlers
        ):
            scraper_logger.addHandler(fh)

    return run_logger, fh


def _teardown_run_logger(run_id: int, fh: logging.FileHandler) -> None:
    """Close and detach the file handler from all loggers wired to this run."""
    for name in [
        "app.scrapers.sources.app_reviews",
        "app.scrapers.sources.review_sites",
        "app.scrapers.sources.reddit",
        "app.scrapers.sources.youtube",
        "app.scrapers.sources.x_posts",
        "app.scrapers",
        f"scrape_run.{run_id}",
        __name__,
    ]:
        lg = logging.getLogger(name)
        if fh in lg.handlers:
            lg.removeHandler(fh)
    fh.close()


class ScrapeExecutionService:
    @staticmethod
    def execute_run(
        db: Session, run_id: int
    ) -> tuple[ScrapeRun, int, int, int, int, bool, bool]:
        """
        Execute a scrape run, supporting both single and multi-source configurations.

        `run.source_name` may be a comma-separated list of source names
        (e.g. "reddit,youtube,app_reviews").  Each source is scraped in sequence and
        all evidence is collected into the same run, so downstream pipeline steps
        (normalisation, intelligence, indexing, export, etc.) receive the full
        multi-source corpus automatically — they all query by run_id, not source_name.

        Per-run log file: logs/run_{run_id}.log — all scraper output is written here
        so you can share it for debugging.
        """
        settings = get_settings()

        # Set up per-run file logger FIRST so every subsequent log line is captured
        run_logger, run_fh = _get_run_logger(run_id)

        run = OrchestratorService.dispatch_run(db, run_id)
        run = OrchestratorService.start_run(db, run.id)

        run_logger.info(
            "=== Run %d started — brand='%s' sources=[%s] live_fetch=%s fail_open_stub=%s ===",
            run_id, run.target_brand, run.source_name,
            settings.scraper_enable_live_fetch, settings.scraper_fail_open_to_stub,
        )

        # Parse comma-separated source list (backward-compatible with single-source runs)
        source_names = [s.strip() for s in run.source_name.split(",") if s.strip()]

        # Pass session_notes raw to each scraper so they can call extract_context_keywords()
        # internally with the original "[CONTEXT: ...]" format.  Pre-joining keywords here
        # caused double-parsing: scrapers calling extract_context_keywords(joined_string) would
        # tokenise by whitespace and lose multi-word keywords like "mobile app", "fake listing".
        context_str: str | None = run.session_notes if run.session_notes else None
        if context_str:
            run_logger.info("Context (session_notes): %s", context_str[:200])

        # Collect evidence from every selected source
        all_scraped_items = []
        failed_sources: list[str] = []

        for source_name in source_names:
            run_logger.info("--- Scraping source: %s ---", source_name)
            try:
                scraper = ScraperRegistry.get_scraper(source_name)
                items = scraper.scrape(run.target_brand, context=context_str)
                run_logger.info("Source '%s': returned %d items", source_name, len(items))
                # Log fetch_mode breakdown
                mode_counts: dict[str, int] = {}
                for it in items:
                    mode = str((it.metadata_json or {}).get("fetch_mode") or "unknown")
                    mode_counts[mode] = mode_counts.get(mode, 0) + 1
                if mode_counts:
                    run_logger.info("  fetch_mode breakdown: %s", mode_counts)
                all_scraped_items.extend(items)
            except Exception as exc:
                # Record failure but continue with remaining sources so a single bad
                # source does not abort the entire multi-source run.
                run_logger.warning("Source '%s' raised exception: %s", source_name, exc, exc_info=True)
                failed_sources.append(f"{source_name}: {exc}")

        if not all_scraped_items and failed_sources:
            # Every source failed — fail the run
            run_logger.error("All sources failed: %s", "; ".join(failed_sources))
            _teardown_run_logger(run_id, run_fh)
            OrchestratorService.fail_run(
                db=db,
                run_id=run.id,
                error_message="; ".join(failed_sources),
                orchestrator_notes="All source scrapers failed",
            )
            raise RuntimeError(
                f"All source scrapers failed for run {run_id}: {'; '.join(failed_sources)}"
            )

        discovered_count = len(all_scraped_items)

        live_items_count = 0
        stub_items_count = 0

        for item in all_scraped_items:
            fetch_mode = str((item.metadata_json or {}).get("fetch_mode") or "").strip().lower()
            if fetch_mode == "live":
                live_items_count += 1
            elif fetch_mode == "stub":
                stub_items_count += 1

        fallback_to_stub_used = stub_items_count > 0

        run_logger.info(
            "Total scraped: %d items (live=%d, stub=%d, other=%d)",
            discovered_count, live_items_count, stub_items_count,
            discovered_count - live_items_count - stub_items_count,
        )

        existing_dedupe_keys = {
            key
            for key in db.scalars(
                select(RawEvidence.dedupe_key).where(RawEvidence.scrape_run_id == run.id)
            ).all()
            if key
        }
        batch_dedupe_keys: set[str] = set()

        persisted_count = 0
        deduplicated_count = 0

        for item in all_scraped_items:
            dedupe_key = item.dedupe_key or build_dedupe_key(
                source_name=item.source_name,
                external_id=item.external_id,
                source_url=item.source_url,
                raw_text=item.raw_text,
            )

            if dedupe_key in existing_dedupe_keys or dedupe_key in batch_dedupe_keys:
                deduplicated_count += 1
                continue

            batch_dedupe_keys.add(dedupe_key)

            evidence = RawEvidence(
                scrape_run_id=run.id,
                source_name=item.source_name,
                platform_name=item.platform_name,
                content_type=item.content_type,
                external_id=item.external_id,
                author_name=item.author_name,
                source_url=item.source_url,
                published_at=item.published_at,
                fetched_at=item.fetched_at or datetime.now(timezone.utc),
                source_query=item.source_query or run.target_brand,
                parser_version=item.parser_version or f"{item.source_name}-v1",
                dedupe_key=dedupe_key,
                raw_payload_json=item.raw_payload_json or {},
                raw_text=item.raw_text,
                cleaned_text=item.cleaned_text,
                normalized_text=None,
                normalized_language=None,
                normalization_status="pending",
                normalization_hash=None,
                resolved_language=None,
                language_family=None,
                script_label=None,
                multilingual_status="pending",
                multilingual_notes=None,
                bridge_text=None,
                language=item.language,
                is_relevant=item.is_relevant,
                metadata_json=item.metadata_json,
            )
            db.add(evidence)
            persisted_count += 1

        db.commit()

        mode_summary = (
            f"live={live_items_count}, stub={stub_items_count}, "
            f"live_fetch_enabled={settings.scraper_enable_live_fetch}"
        )

        source_summary_str = (
            f"sources=[{run.source_name}]"
            if "," in run.source_name
            else f"source={run.source_name}"
        )

        partial_failure_note = (
            f" | partial_failures=[{'; '.join(failed_sources)}]"
            if failed_sources
            else ""
        )

        log_path = str(_LOGS_DIR / f"run_{run_id}.log")
        run_logger.info(
            "=== Run %d complete — persisted=%d, deduplicated=%d, %s%s ===",
            run_id, persisted_count, deduplicated_count, mode_summary, partial_failure_note,
        )
        run_logger.info("Log file: %s", log_path)

        _teardown_run_logger(run_id, run_fh)

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run.id,
            pipeline_stage="source_collection_completed",
            items_discovered=discovered_count,
            items_processed=persisted_count,
            orchestrator_notes=(
                f"Scrape completed ({source_summary_str}): "
                f"persisted={persisted_count}, deduplicated={deduplicated_count}, "
                f"{mode_summary}{partial_failure_note} | log={log_path}"
            ),
        )

        run = OrchestratorService.complete_run(db, run.id)
        return (
            run,
            persisted_count,
            deduplicated_count,
            live_items_count,
            stub_items_count,
            settings.scraper_enable_live_fetch,
            fallback_to_stub_used,
        )
