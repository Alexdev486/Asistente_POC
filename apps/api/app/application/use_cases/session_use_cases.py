from typing import Any
from uuid import UUID, uuid4

from app.application.orchestrator.langgraph_flow import ConversationGraph, ConversationSnapshot
from app.infrastructure.db.repositories import (
    DecisionLogRepository,
    FeedbackRepository,
    KnowledgeRepository,
    MessageRepository,
    SessionRepository,
)
from app.infrastructure.llm.gateway import LLMGateway
from app.infrastructure.llm.providers.groq import GroqProvider
from app.infrastructure.llm.providers.openrouter import OpenRouterProvider
from app.modules.faq_matcher.service import FAQMatcherService
from app.modules.free_text_parser.service import FreeTextParserService
from app.modules.hybrid_ranking.service import HybridRankingService
from app.modules.tree_engine.service import DiagnosticTreeEngine
from app.modules.vin_lookup.service import VINLookupService
from app.infrastructure.retrieval.embeddings import EmbeddingService
from app.schemas.requests import SessionFeedbackRequest, SessionMessageRequest, StartSessionRequest
from app.schemas.responses import (
    FeedbackResponse,
    SessionDetailResponse,
    SessionMessageResponse,
    SessionStateResponse,
    StartSessionResponse,
)


class SessionUseCases:
    def __init__(
        self,
        session_repository: SessionRepository,
        feedback_repository: FeedbackRepository,
        decision_log_repository: DecisionLogRepository,
        knowledge_repository: KnowledgeRepository,
        message_repository: MessageRepository,
    ) -> None:
        self._session_repository = session_repository
        self._feedback_repository = feedback_repository
        self._decision_log_repository = decision_log_repository
        self._knowledge_repository = knowledge_repository
        self._message_repository = message_repository
        self._vin_lookup = VINLookupService(vehicle_resolver=self._knowledge_repository.get_vehicle_by_vin)
        self._faq_matcher = FAQMatcherService()
        self._llm_gateway = LLMGateway(primary=GroqProvider(), fallback=OpenRouterProvider())
        self._free_text_parser = FreeTextParserService(llm_gateway=self._llm_gateway)
        self._embedding_service = EmbeddingService()
        self._hybrid_ranking = HybridRankingService()
        self._tree_engine = DiagnosticTreeEngine()
        self._graph = ConversationGraph(
            resolve_vin=self._vin_lookup.resolve,
            list_active_faqs=self._knowledge_repository.list_active_faqs,
            list_active_tree_symptoms=self._knowledge_repository.list_active_tree_symptoms,
            get_active_tree_by_symptom=self._knowledge_repository.get_active_tree_by_symptom,
            parse_free_text=self._free_text_parser.parse,
            faq_match=self._faq_matcher.match,
            embed_text=self._embedding_service.embed,
            hybrid_search=self._knowledge_repository.search_hybrid,
            rank_hypotheses=self._hybrid_ranking.rank,
            tree_engine=self._tree_engine,
        )

    def start_session(self, _: StartSessionRequest) -> StartSessionResponse:
        session_id = uuid4()
        self._session_repository.create_session(
            session_id=session_id,
            state_json={
                "facts": {},
                "active_hypotheses": [],
                "asked_questions": [],
                "orchestration": {"last_route": "vin_lookup", "entry_point": None, "last_confidence": 0.0},
            },
        )
        response = StartSessionResponse(
            session_id=session_id,
            message=(
                "Hola. Indicame el bastidor para identificar el vehiculo y ayudarte con "
                "el diagnostico."
            ),
        )
        self._message_repository.save_message(session_id, "assistant", response.message)
        return response

    def process_message(self, payload: SessionMessageRequest) -> SessionMessageResponse:
        persisted = self._session_repository.get_session(payload.session_id)
        if persisted is None:
            raise KeyError(f"Sesion no encontrada: {payload.session_id}")

        steps = persisted.steps + 1
        user_message = payload.message.strip()
        self._message_repository.save_message(payload.session_id, "user", user_message)

        asked_questions = persisted.state_json.get("asked_questions")
        if not isinstance(asked_questions, list):
            asked_questions = []

        graph_result = self._graph.run_turn(
            ConversationSnapshot(
                vin=persisted.state.vin,
                model=persisted.state.model,
                entry_point=persisted.entry_point,
                current_symptom=persisted.state.current_symptom,
                current_node=persisted.state.current_node,
                asked_questions=[str(item) for item in asked_questions],
            ),
            user_message,
        )
        persisted.entry_point = graph_result.entry_point
        self._apply_state_updates(persisted.state, graph_result.state_updates)
        self._merge_orchestration_state(
            persisted.state_json,
            route=graph_result.route,
            entry_point=graph_result.entry_point,
            confidence=graph_result.confidence,
        )
        self._update_diagnostic_state(persisted.state_json, graph_result.decision_output)
        final_result = self._extract_final_result(graph_result.decision_output)
        self._session_repository.save_turn(
            payload.session_id,
            steps=steps,
            entry_point=persisted.entry_point,
            state=persisted.state,
            state_json=persisted.state_json,
        )
        if final_result:
            self._session_repository.set_final_result(payload.session_id, final_result)
        self._save_decision_log(
            session_id=payload.session_id,
            module_name=graph_result.route,
            input_data={"message": user_message},
            output_data=graph_result.decision_output,
            confidence=graph_result.confidence,
        )
        self._save_additional_logs(payload.session_id, graph_result.decision_output)
        self._message_repository.save_message(payload.session_id, "assistant", graph_result.assistant_message)
        return SessionMessageResponse(
            session_id=payload.session_id,
            message=graph_result.assistant_message,
            state=persisted.state,
            diagnostic_output=graph_result.decision_output.get("diagnostic_output"),
        )

    def get_session(self, session_id: UUID) -> SessionDetailResponse:
        persisted = self._session_repository.get_session(session_id)
        if persisted is None:
            raise KeyError(f"Sesion no encontrada: {session_id}")
        return SessionDetailResponse(
            session_id=persisted.session_id,
            status=persisted.status,
            entry_point=persisted.entry_point,
            steps=persisted.steps,
            state=persisted.state,
            state_json=persisted.state_json,
        )

    def save_feedback(self, session_id: UUID, payload: SessionFeedbackRequest) -> FeedbackResponse:
        persisted = self._session_repository.get_session(session_id)
        if persisted is None:
            raise KeyError(f"Sesion no encontrada: {session_id}")
        self._feedback_repository.save_feedback(session_id, payload.useful, payload.comment)
        self._session_repository.complete_session(session_id)
        self._save_decision_log(
            session_id=session_id,
            module_name="feedback",
            input_data={"useful": payload.useful, "comment": payload.comment},
            output_data={"result": "feedback_saved"},
            confidence=1.0,
        )
        self._message_repository.save_message(session_id, "system", "Feedback guardado correctamente.")
        return FeedbackResponse(
            session_id=session_id,
            saved=True,
            message="Feedback guardado correctamente.",
        )

    def _save_decision_log(
        self,
        *,
        session_id: UUID,
        module_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        confidence: float | None,
    ) -> None:
        self._decision_log_repository.save_log(
            session_id=session_id,
            module_name=module_name,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
        )

    def _save_additional_logs(self, session_id: UUID, decision_output: dict[str, Any]) -> None:
        if "sources" in decision_output:
            self._save_decision_log(
                session_id=session_id,
                module_name="historical_retrieval",
                input_data={"sources": decision_output.get("sources", [])},
                output_data={"result": "retrieved_candidates"},
                confidence=decision_output.get("top_score"),
            )
        if "top_hypotheses" in decision_output:
            self._save_decision_log(
                session_id=session_id,
                module_name="hybrid_ranking",
                input_data={"top_hypotheses": decision_output.get("top_hypotheses", [])},
                output_data={"top_score": decision_output.get("top_score")},
                confidence=decision_output.get("top_score"),
            )
        if "diagnostic_output" in decision_output:
            self._save_decision_log(
                session_id=session_id,
                module_name="response_builder",
                input_data={"source": decision_output.get("route")},
                output_data=decision_output.get("diagnostic_output", {}),
                confidence=decision_output.get("diagnostic_output", {}).get("confidence"),
            )

    @staticmethod
    def _apply_state_updates(state: SessionStateResponse, updates: dict[str, str | None]) -> None:
        if "vin" in updates:
            state.vin = updates["vin"]
        if "model" in updates:
            state.model = updates["model"]
        if "current_symptom" in updates:
            state.current_symptom = updates["current_symptom"]
        if "current_node" in updates:
            state.current_node = updates["current_node"]

    @staticmethod
    def _merge_orchestration_state(
        state_json: dict[str, Any],
        *,
        route: str,
        entry_point: str | None,
        confidence: float,
    ) -> None:
        orchestration = state_json.get("orchestration")
        if not isinstance(orchestration, dict):
            orchestration = {}
        orchestration.update(
            {
                "last_route": route,
                "entry_point": entry_point,
                "last_confidence": confidence,
            }
        )
        state_json["orchestration"] = orchestration

    @staticmethod
    def _update_diagnostic_state(state_json: dict[str, Any], decision_output: dict[str, Any]) -> None:
        asked_questions = state_json.get("asked_questions")
        if not isinstance(asked_questions, list):
            asked_questions = []

        if decision_output.get("result") == "question" and decision_output.get("current_node"):
            node_id = str(decision_output["current_node"])
            if node_id not in asked_questions:
                asked_questions.append(node_id)
        state_json["asked_questions"] = asked_questions

        facts = state_json.get("facts")
        if not isinstance(facts, dict):
            facts = {}
        answered_node = decision_output.get("answered_node")
        answer = decision_output.get("answer")
        if answered_node and answer:
            facts[str(answered_node)] = str(answer).strip().lower()
        state_json["facts"] = facts

        diagnostic_output = decision_output.get("diagnostic_output")
        if isinstance(diagnostic_output, dict):
            hypothesis = {
                "label": diagnostic_output.get("primary_hypothesis"),
                "score": diagnostic_output.get("confidence"),
            }
            state_json["active_hypotheses"] = [hypothesis]

    @staticmethod
    def _extract_final_result(decision_output: dict[str, Any]) -> str | None:
        diagnostic_output = decision_output.get("diagnostic_output")
        if isinstance(diagnostic_output, dict) and diagnostic_output.get("primary_hypothesis"):
            return str(diagnostic_output["primary_hypothesis"])
        return None
