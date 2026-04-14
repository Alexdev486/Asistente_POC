from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.application.use_cases.session_use_cases import SessionUseCases
from app.schemas.requests import (
    SessionFeedbackRequest,
    SessionMessageRequest,
    StartSessionRequest,
)
from app.schemas.responses import (
    FeedbackResponse,
    SessionDetailResponse,
    SessionMessageResponse,
    StartSessionResponse,
)

router = APIRouter()
session_use_cases = SessionUseCases()


@router.post("/session/start", response_model=StartSessionResponse)
def start_session(payload: StartSessionRequest) -> StartSessionResponse:
    return session_use_cases.start_session(payload)


@router.post("/session/message", response_model=SessionMessageResponse)
def process_message(payload: SessionMessageRequest) -> SessionMessageResponse:
    try:
        return session_use_cases.process_message(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/session/{session_id}", response_model=SessionDetailResponse)
def get_session(session_id: UUID) -> SessionDetailResponse:
    try:
        return session_use_cases.get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/session/{session_id}/feedback", response_model=FeedbackResponse)
def save_feedback(session_id: UUID, payload: SessionFeedbackRequest) -> FeedbackResponse:
    try:
        return session_use_cases.save_feedback(session_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

