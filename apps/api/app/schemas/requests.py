from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionMessageRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=1200)


class SessionFeedbackRequest(BaseModel):
    useful: bool
    comment: str | None = Field(default=None, max_length=1000)

