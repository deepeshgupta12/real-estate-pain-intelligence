"""ARQ Redis connection pool and job dispatch utilities."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_arq_pool = None


async def get_arq_pool():
    """Get or create the ARQ Redis pool."""
    global _arq_pool
    if _arq_pool is None:
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            from app.core.config import get_settings

            settings = get_settings()
            redis_settings = RedisSettings.from_dsn(settings.redis_url)
            _arq_pool = await create_pool(redis_settings)
            logger.info("ARQ Redis pool created successfully")
        except Exception as exc:
            logger.warning(f"ARQ Redis pool creation failed: {exc}. Background tasks will run synchronously.")
            _arq_pool = None
    return _arq_pool


async def enqueue_task(task_name: str, *args: Any, **kwargs: Any) -> str | None:
    """
    Enqueue a background task. Returns job_id if enqueued, None if sync fallback.
    Falls back gracefully if Redis is unavailable.
    """
    pool = await get_arq_pool()
    if pool is None:
        logger.warning(f"No ARQ pool available, skipping background enqueue for {task_name}")
        return None

    try:
        job = await pool.enqueue_job(task_name, *args, **kwargs)
        logger.info(f"Enqueued task {task_name} with job_id={job.job_id}")
        return job.job_id
    except Exception as exc:
        logger.error(f"Failed to enqueue task {task_name}: {exc}")
        return None


async def get_job_status(job_id: str) -> dict[str, Any]:
    """Get the status of a background job."""
    pool = await get_arq_pool()
    if pool is None:
        return {"job_id": job_id, "status": "unknown", "error": "Redis not available"}

    try:
        from arq.jobs import Job, JobStatus
        job = Job(job_id=job_id, redis=pool)
        status = await job.status()
        result = None
        if status == JobStatus.complete:
            result = await job.result()
        return {
            "job_id": job_id,
            "status": status.value if hasattr(status, "value") else str(status),
            "result": result,
        }
    except Exception as exc:
        return {"job_id": job_id, "status": "error", "error": str(exc)}
