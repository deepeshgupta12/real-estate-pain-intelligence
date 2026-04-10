from fastapi import APIRouter, Depends

from app.core.config import Settings
from app.dependencies.common import get_app_settings
from app.schemas.meta import MetaResponse

router = APIRouter()


@router.get("/meta", response_model=MetaResponse, tags=["meta"])
def get_meta(settings: Settings = Depends(get_app_settings)) -> MetaResponse:
    return MetaResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        api_prefix=settings.api_v1_prefix,
        frontend_url=settings.frontend_url,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )