from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SessionStateResponse(BaseModel):
    vin: str | None = None
    model: str | None = None
    current_symptom: str | None = None
    current_node: str | None = None


class StartSessionResponse(BaseModel):
    session_id: UUID
    message: str


class SessionMessageResponse(BaseModel):
    session_id: UUID
    message: str
    state: SessionStateResponse | None = None


class SessionDetailResponse(BaseModel):
    session_id: UUID
    status: str
    entry_point: str | None = None
    steps: int = 0
    state: SessionStateResponse
    state_json: dict[str, Any] = Field(default_factory=dict)


class FeedbackResponse(BaseModel):
    session_id: UUID
    saved: bool
    message: str


class MetricsSummaryResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    avg_steps_per_session: float
    faq_usage: int
    tree_usage: int
    other_usage: int
    positive_feedback: int
    negative_feedback: int


class DiagnosticOutputResponse(BaseModel):
    primary_hypothesis: str
    alternatives: list[str] = Field(default_factory=list)
    next_check: str
    short_explanation: str
    confidence: float = Field(ge=0.0, le=1.0)

