from sqlalchemy.orm import Session

from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.scrapers.registry import ScraperRegistry
from app.services.orchestrator import OrchestratorService


class ScrapeExecutionService:
    @staticmethod
    def execute_run(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        run = OrchestratorService.dispatch_run(db, run_id)
        run = OrchestratorService.start_run(db, run.id)

        scraper = ScraperRegistry.get_scraper(run.source_name)
        scraped_items = scraper.scrape(run.target_brand)

        discovered_count = len(scraped_items)

        for item in scraped_items:
            evidence = RawEvidence(
                scrape_run_id=run.id,
                source_name=item.source_name,
                platform_name=item.platform_name,
                content_type=item.content_type,
                external_id=item.external_id,
                author_name=item.author_name,
                source_url=item.source_url,
                published_at=item.published_at,
                raw_text=item.raw_text,
                cleaned_text=item.cleaned_text,
                language=item.language,
                is_relevant=item.is_relevant,
                metadata_json=item.metadata_json,
            )
            db.add(evidence)

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run.id,
            pipeline_stage="source_collection_completed",
            items_discovered=discovered_count,
            items_processed=discovered_count,
            orchestrator_notes="Source scraper execution completed and evidence persisted",
        )

        run = OrchestratorService.complete_run(db, run.id)
        return run, discovered_count