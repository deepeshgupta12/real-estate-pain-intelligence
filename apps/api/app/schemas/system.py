from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    database_configured: bool