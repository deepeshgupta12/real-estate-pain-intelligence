from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.dependencies.common import get_app_settings
from app.schemas.system import SystemInfoResponse
from app.scrapers.circuit_breaker import CircuitBreaker

router = APIRouter()


@router.get("/system/info", response_model=SystemInfoResponse, tags=["system"])
def get_system_info(
    settings: Settings = Depends(get_app_settings),
) -> SystemInfoResponse:
    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        database_configured=bool(settings.database_url),
    )


@router.get("/scraper/circuit-status", tags=["system"])
def get_circuit_status() -> list[dict]:
    """Get circuit breaker status for all scrapers."""
    return [cb.get_status() for cb in CircuitBreaker._registry.values()]