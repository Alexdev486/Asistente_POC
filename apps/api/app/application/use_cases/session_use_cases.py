from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.orchestrator.langgraph_flow import ConversationRouter, ConversationSnapshot
from app.modules.vin_lookup.service import VINLookupService
from app.schemas.requests import SessionFeedbackRequest, SessionMessageRequest, StartSessionRequest
from app.schemas.responses import (
    FeedbackResponse,
    SessionDetailResponse,
    SessionMessageResponse,
    SessionStateResponse,
    StartSessionResponse,
)


@dataclass
class SessionRecord:
    session_id: UUID
    status: str
    entry_point: str | None
    steps: int
    state: SessionStateResponse
    state_json: dict


class SessionUseCases:
    """
    Bootstrapping in-memory use case.
    In fase siguiente se reemplaza por repositorios SQL.
    """

    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionRecord] = {}
        self._feedback: dict[UUID, SessionFeedbackRequest] = {}
        self._router = ConversationRouter()
        self._vin_lookup = VINLookupService()

    def start_session(self, _: StartSessionRequest) -> StartSessionResponse:
        session_id = uuid4()
        self._sessions[session_id] = SessionRecord(
            session_id=session_id,
            status="active",
            entry_point=None,
            steps=0,
            state=SessionStateResponse(),
            state_json={"facts": {}, "active_hypotheses": [], "asked_questions": []},
        )
        return StartSessionResponse(
            session_id=session_id,
            message=(
                "Hola. Indicame el bastidor para identificar el vehiculo y ayudarte con "
                "el diagnostico."
            ),
        )

    def process_message(self, payload: SessionMessageRequest) -> SessionMessageResponse:
        record = self._sessions.get(payload.session_id)
        if record is None:
            raise KeyError(f"Sesion no encontrada: {payload.session_id}")

        record.steps += 1
        user_message = payload.message.strip()

        if not record.state.vin:
            vehicle = self._vin_lookup.resolve(user_message)
            if not vehicle:
                return SessionMessageResponse(
                    session_id=payload.session_id,
                    message="No he podido identificar ese bastidor. Intenta de nuevo.",
                    state=record.state,
                )
            record.state.vin = vehicle.vin
            record.state.model = vehicle.model
            return SessionMessageResponse(
                session_id=payload.session_id,
                message=(
                    f"He identificado el vehiculo como {vehicle.model} ({vehicle.model_year}). "
                    "Selecciona una opcion: Sintomas frecuentes, Consultas frecuentes u Otros."
                ),
                state=record.state,
            )

        route = self._router.route_turn(
            ConversationSnapshot(
                vin=record.state.vin,
                model=record.state.model,
                entry_point=record.entry_point,
                current_symptom=record.state.current_symptom,
            ),
            user_message,
        )
        if route == "tree_engine":
            record.entry_point = "tree"
            return SessionMessageResponse(
                session_id=payload.session_id,
                message=(
                    "Vamos por Sintomas frecuentes. Selecciona: Paradas de motor o "
                    "Testigo CELP encendido."
                ),
                state=record.state,
            )
        if route == "faq_matcher":
            record.entry_point = "faq"
            return SessionMessageResponse(
                session_id=payload.session_id,
                message="Estoy buscando la FAQ mas relevante para tu consulta.",
                state=record.state,
            )
        if route == "free_text_parser":
            record.entry_point = "other"
            return SessionMessageResponse(
                session_id=payload.session_id,
                message="Describe el problema con tus palabras para analizarlo en la via Otros.",
                state=record.state,
            )

        return SessionMessageResponse(
            session_id=payload.session_id,
            message="Selecciona una opcion valida: Sintomas frecuentes, Consultas frecuentes u Otros.",
            state=record.state,
        )

    def get_session(self, session_id: UUID) -> SessionDetailResponse:
        record = self._sessions.get(session_id)
        if record is None:
            raise KeyError(f"Sesion no encontrada: {session_id}")
        return SessionDetailResponse(
            session_id=record.session_id,
            status=record.status,
            entry_point=record.entry_point,
            steps=record.steps,
            state=record.state,
            state_json=record.state_json,
        )

    def save_feedback(self, session_id: UUID, payload: SessionFeedbackRequest) -> FeedbackResponse:
        record = self._sessions.get(session_id)
        if record is None:
            raise KeyError(f"Sesion no encontrada: {session_id}")
        self._feedback[session_id] = payload
        record.status = "completed"
        return FeedbackResponse(
            session_id=session_id,
            saved=True,
            message="Feedback guardado correctamente.",
        )

