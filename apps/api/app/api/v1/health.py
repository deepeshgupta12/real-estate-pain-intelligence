from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.dependencies.common import get_app_settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
        api_prefix=settings.api_v1_prefix,
    )