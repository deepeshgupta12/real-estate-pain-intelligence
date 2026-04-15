"""
ARQ background task definitions for pipeline stages.
Each task wraps a synchronous service call and updates job status.
"""
import logging
from typing import Any

from arq import ArqRedis

logger = logging.getLogger(__name__)


async def task_execute_scrape(ctx: dict, run_id: int) -> dict[str, Any]:
    """Background task: execute scrape for a run."""
    from app.db.session import SessionLocal
    from app.services.scrape_executor import ScrapeExecutionService

    logger.info(f"[arq] Starting scrape task for run {run_id}")
    db = SessionLocal()
    try:
        result = ScrapeExecutionService.execute_run(db=db, run_id=run_id)
        logger.info(f"[arq] Scrape completed for run {run_id}: {result}")
        return {"status": "completed", "run_id": run_id, "result": str(result)}
    except Exception as exc:
        logger.error(f"[arq] Scrape failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_normalize_run(ctx: dict, run_id: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.normalization import NormalizationService

    db = SessionLocal()
    try:
        result = NormalizationService.normalize_run(db=db, run_id=run_id)
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Normalization failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_multilingual_run(ctx: dict, run_id: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.multilingual import MultilingualService

    db = SessionLocal()
    try:
        result = MultilingualService.process_run(db=db, run_id=run_id)
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Multilingual failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_intelligence_run(ctx: dict, run_id: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.intelligence import IntelligenceService
    from app.services.trending import TrendingService
    from app.services.topic_modeling import TopicModelingService
    from app.core.config import get_settings

    settings = get_settings()
    db = SessionLocal()
    try:
        result = IntelligenceService.process_run(db=db, run_id=run_id)
        logger.info(f"[arq] Intelligence completed for run {run_id}")

        # Auto-trigger trending fingerprint update after intelligence
        try:
            TrendingService.update_fingerprints_for_run(db=db, run_id=run_id)
            logger.info(f"[arq] Trending fingerprints updated for run {run_id}")
        except Exception as trend_exc:
            logger.warning(f"[arq] Trending update failed (non-fatal) for run {run_id}: {trend_exc}")

        # Auto-trigger topic modeling after intelligence (if enabled)
        if settings.topic_modeling_enabled:
            try:
                TopicModelingService.run_topic_modeling(db=db, run_id=run_id)
                logger.info(f"[arq] Topic modeling completed for run {run_id}")
            except Exception as topic_exc:
                logger.warning(f"[arq] Topic modeling failed (non-fatal) for run {run_id}: {topic_exc}")

        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Intelligence failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_retrieval_index(ctx: dict, run_id: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.retrieval import RetrievalService

    db = SessionLocal()
    try:
        result = RetrievalService.index_run(db=db, run_id=run_id)
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Retrieval indexing failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_generate_review_queue(ctx: dict, run_id: int) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.human_review import HumanReviewService

    db = SessionLocal()
    try:
        result = HumanReviewService.generate_review_queue(db=db, run_id=run_id)
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Review queue generation failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


async def task_generate_exports(ctx: dict, run_id: int, formats: list[str]) -> dict[str, Any]:
    from app.db.session import SessionLocal
    from app.services.export import ExportService

    db = SessionLocal()
    try:
        result = ExportService.generate_export_jobs(db=db, run_id=run_id, export_formats=formats)
        return {"status": "completed", "run_id": run_id}
    except Exception as exc:
        logger.error(f"[arq] Export generation failed for run {run_id}: {exc}")
        raise
    finally:
        db.close()


# ARQ worker settings
class WorkerSettings:
    functions = [
        task_execute_scrape,
        task_normalize_run,
        task_multilingual_run,
        task_intelligence_run,
        task_retrieval_index,
        task_generate_review_queue,
        task_generate_exports,
    ]
    redis_settings = None  # Set dynamically from config
    max_jobs = 10
    job_timeout = 300
    keep_result = 3600  # Keep results for 1 hour
    max_tries = 3
