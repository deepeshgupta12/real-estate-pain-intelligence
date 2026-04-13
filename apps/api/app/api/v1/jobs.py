"""Job status endpoint for background task tracking."""
from fastapi import APIRouter

from app.workers.queue import get_job_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
async def get_background_job_status(job_id: str) -> dict:
    """Get the status of a background pipeline job."""
    return await get_job_status(job_id)
