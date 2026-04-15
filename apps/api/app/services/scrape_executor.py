from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.scrapers.context_utils import extract_context_keywords
from app.scrapers.registry import ScraperRegistry
from app.scrapers.utils import build_dedupe_key
from app.services.orchestrator import OrchestratorService


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
        """
        settings = get_settings()

        run = OrchestratorService.dispatch_run(db, run_id)
        run = OrchestratorService.start_run(db, run.id)

        # Parse comma-separated source list (backward-compatible with single-source runs)
        source_names = [s.strip() for s in run.source_name.split(",") if s.strip()]

        # Extract context from session_notes (user-owned field, never touched by pipeline).
        # If session_notes is blank / None, context_str is None → broad scraping.
        context_kws = extract_context_keywords(run.session_notes)
        context_str: str | None = " ".join(context_kws) if context_kws else None

        # Collect evidence from every selected source
        all_scraped_items = []
        failed_sources: list[str] = []

        for source_name in source_names:
            try:
                scraper = ScraperRegistry.get_scraper(source_name)
                items = scraper.scrape(run.target_brand, context=context_str)
                all_scraped_items.extend(items)
            except Exception as exc:
                # Record failure but continue with remaining sources so a single bad
                # source does not abort the entire multi-source run.
                failed_sources.append(f"{source_name}: {exc}")

        if not all_scraped_items and failed_sources:
            # Every source failed — fail the run
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

        source_summary = (
            f"sources=[{run.source_name}]"
            if "," in run.source_name
            else f"source={run.source_name}"
        )

        partial_failure_note = (
            f" | partial_failures=[{'; '.join(failed_sources)}]"
            if failed_sources
            else ""
        )

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run.id,
            pipeline_stage="source_collection_completed",
            items_discovered=discovered_count,
            items_processed=persisted_count,
            orchestrator_notes=(
                f"Scrape completed ({source_summary}): "
                f"persisted={persisted_count}, deduplicated={deduplicated_count}, "
                f"{mode_summary}{partial_failure_note}"
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
