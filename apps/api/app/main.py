from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.schemas.common import MessageResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for the Real Estate Pain Point Intelligence Platform",
    lifespan=lifespan,
)


@app.get("/", response_model=MessageResponse, tags=["root"])
def root() -> MessageResponse:
    return MessageResponse(message="Real Estate Pain Point Intelligence API")


app.include_router(api_router, prefix=settings.api_v1_prefix)