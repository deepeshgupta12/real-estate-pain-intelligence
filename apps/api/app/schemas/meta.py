from pydantic import BaseModel


class MetaResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    api_prefix: str
    frontend_url: str
    docs_url: str
    openapi_url: str