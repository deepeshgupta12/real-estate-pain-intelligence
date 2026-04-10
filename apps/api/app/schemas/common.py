from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class NotFoundResponse(BaseModel):
    detail: str