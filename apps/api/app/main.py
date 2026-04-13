from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.schemas.common import MessageResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.api_key_enabled:
            return await call_next(request)

        exempt_paths = {"/", "/health", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in exempt_paths:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != settings.api_key_secret:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )
        return await call_next(request)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for the Real Estate Pain Point Intelligence Platform",
    lifespan=lifespan,
)

app.add_middleware(APIKeyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", response_model=MessageResponse, tags=["root"])
def root() -> MessageResponse:
    return MessageResponse(message="Real Estate Pain Point Intelligence API")


app.include_router(api_router, prefix=settings.api_v1_prefix)