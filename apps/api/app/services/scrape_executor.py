from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.scrapers.registry import ScraperRegistry
from app.scrapers.utils import build_dedupe_key
from app.services.orchestrator import OrchestratorService


class ScrapeExecutionService:
    @staticmethod
    def execute_run(
        db: Session, run_id: int
    ) -> tuple[ScrapeRun, int, int, int, int, bool, bool]:
        settings = get_settings()

        run = OrchestratorService.dispatch_run(db, run_id)
        run = OrchestratorService.start_run(db, run.id)

        scraper = ScraperRegistry.get_scraper(run.source_name)

        try:
            scraped_items = scraper.scrape(run.target_brand)
        except Exception as exc:
            OrchestratorService.fail_run(
                db=db,
                run_id=run.id,
                error_message=str(exc),
                orchestrator_notes="Source scraper execution failed",
            )
            raise

        discovered_count = len(scraped_items)

        live_items_count = 0
        stub_items_count = 0

        for item in scraped_items:
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

        for item in scraped_items:
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

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run.id,
            pipeline_stage="source_collection_completed",
            items_discovered=discovered_count,
            items_processed=persisted_count,
            orchestrator_notes=(
                "Source scraper execution completed and evidence persisted "
                f"(persisted={persisted_count}, deduplicated={deduplicated_count}, {mode_summary})"
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