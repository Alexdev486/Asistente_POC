"""Tests for SessionUseCases.

Covers start_session, process_message, get_session, save_feedback,
decision logging, state updates, and error paths.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.application.orchestrator.langgraph_flow import ConversationGraphResult
from app.application.use_cases.session_use_cases import SessionUseCases
from app.schemas.requests import SessionFeedbackRequest, SessionMessageRequest, StartSessionRequest
from helpers import sample_state_json, make_persisted


# ---------------------------------------------------------------------------
# Fixture: uses mock repos from conftest.py
# ---------------------------------------------------------------------------


@pytest.fixture
def use_cases(
    mock_session_repo,
    mock_message_repo,
    mock_decision_log_repo,
    mock_feedback_repo,
    mock_knowledge_repo,
) -> SessionUseCases:
    return SessionUseCases(
        session_repository=mock_session_repo,
        feedback_repository=mock_feedback_repo,
        decision_log_repository=mock_decision_log_repo,
        knowledge_repository=mock_knowledge_repo,
        message_repository=mock_message_repo,
    )


# ===================================================================
# start_session
# ===================================================================


class TestStartSession:
    def test_creates_session_and_returns_welcome(self, use_cases: SessionUseCases):
        result = use_cases.start_session(StartSessionRequest())
        assert result.session_id is not None
        assert "bastidor" in result.message.lower()

    def test_saves_welcome_message(self, use_cases: SessionUseCases, mock_message_repo: MagicMock):
        use_cases.start_session(StartSessionRequest())
        mock_message_repo.save_message.assert_called_once()
        args = mock_message_repo.save_message.call_args[0]
        assert args[1] == "assistant"


# ===================================================================
# process_message
# ===================================================================


class TestProcessMessage:
    def test_raises_on_unknown_session(self, use_cases: SessionUseCases):
        with pytest.raises(KeyError, match="no encontrada"):
            use_cases.process_message(SessionMessageRequest(session_id=uuid4(), message="test"))

    def test_saves_user_message(self, use_cases: SessionUseCases, mock_session_repo: MagicMock, mock_message_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid)
        with patch.object(use_cases._graph, "run_turn") as mock_run:
            mock_run.return_value = ConversationGraphResult(
                route="out_of_scope", entry_point=None,
                assistant_message="Fuera de alcance.",
                confidence=0.2, decision_output={}, state_updates={}, quick_replies=[],
            )
            use_cases.process_message(SessionMessageRequest(session_id=sid, message="Hola"))
            # User message saved
            user_calls = [c for c in mock_message_repo.save_message.call_args_list if c.args[1] == "user"]
            assert len(user_calls) >= 1
            assert user_calls[0].args[2] == "Hola"

    def test_saves_assistant_message(self, use_cases: SessionUseCases, mock_session_repo: MagicMock, mock_message_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid)
        with patch.object(use_cases._graph, "run_turn") as mock_run:
            mock_run.return_value = ConversationGraphResult(
                route="out_of_scope", entry_point=None,
                assistant_message="Fuera de alcance.",
                confidence=0.2, decision_output={}, state_updates={}, quick_replies=[],
            )
            use_cases.process_message(SessionMessageRequest(session_id=sid, message="Hola"))
            asst_calls = [c for c in mock_message_repo.save_message.call_args_list if c.args[1] == "assistant"]
            assert len(asst_calls) >= 1

    def test_logs_decision(self, use_cases: SessionUseCases, mock_session_repo: MagicMock, mock_decision_log_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid)
        with patch.object(use_cases._graph, "run_turn") as mock_run:
            mock_run.return_value = ConversationGraphResult(
                route="vin_lookup", entry_point=None,
                assistant_message="Identificado.",
                confidence=1.0,
                decision_output={"result": "vin_identified", "vin": "VIN123"},
                state_updates={"vin": "VIN123", "model": "AK550"},
                quick_replies=[],
            )
            use_cases.process_message(SessionMessageRequest(session_id=sid, message="VIN123"))
            assert mock_decision_log_repo.save_log.call_count >= 1

    def test_saves_turn_on_each_message(self, use_cases: SessionUseCases, mock_session_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid, steps=0)
        with patch.object(use_cases._graph, "run_turn") as mock_run:
            mock_run.return_value = ConversationGraphResult(
                route="menu_selection", entry_point=None,
                assistant_message="Menu", confidence=0.6,
                decision_output={}, state_updates={}, quick_replies=[],
            )
            use_cases.process_message(SessionMessageRequest(session_id=sid, message="test"))
            mock_session_repo.save_turn.assert_called_once()

    def test_returns_full_response(self, use_cases: SessionUseCases, mock_session_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid)
        with patch.object(use_cases._graph, "run_turn") as mock_run:
            mock_run.return_value = ConversationGraphResult(
                route="vin_lookup", entry_point=None,
                assistant_message="Vehiculo identificado AK550.",
                confidence=1.0,
                decision_output={
                    "result": "vin_identified",
                    "diagnostic_output": {
                        "primary_hypothesis": "Bateria descargada",
                        "alternatives": [],
                        "next_check": "Revisar bateria.",
                        "short_explanation": "Arbol de diagnostico.",
                        "confidence": 0.97,
                    },
                },
                state_updates={"vin": "V", "model": "AK550"},
                quick_replies=["Sintomas frecuentes", "Consultas frecuentes", "Otros"],
            )
            resp = use_cases.process_message(SessionMessageRequest(session_id=sid, message="VIN"))
            assert resp.session_id == sid
            assert "AK550" in resp.message
            assert resp.diagnostic_output is not None
            assert resp.state is not None


# ===================================================================
# get_session
# ===================================================================


class TestGetSession:
    def test_returns_detail(self, use_cases: SessionUseCases, mock_session_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid, vin="VIN123", model="AK550")
        result = use_cases.get_session(sid)
        assert result.session_id == sid
        assert result.state.vin == "VIN123"
        assert result.state.model == "AK550"

    def test_raises_on_missing(self, use_cases: SessionUseCases):
        with pytest.raises(KeyError):
            use_cases.get_session(uuid4())


# ===================================================================
# save_feedback
# ===================================================================


class TestSaveFeedback:
    def test_saves_and_completes(self, use_cases: SessionUseCases, mock_session_repo: MagicMock, mock_feedback_repo: MagicMock, mock_decision_log_repo: MagicMock):
        sid = uuid4()
        mock_session_repo.get_session.return_value = make_persisted(session_id=sid)
        result = use_cases.save_feedback(sid, SessionFeedbackRequest(useful=True, comment="Todo bien"))
        assert result.saved is True
        mock_feedback_repo.save_feedback.assert_called_once_with(sid, True, "Todo bien")
        mock_session_repo.complete_session.assert_called_once_with(sid)
        assert mock_decision_log_repo.save_log.call_count >= 1

    def test_raises_on_missing_session(self, use_cases: SessionUseCases):
        with pytest.raises(KeyError):
            use_cases.save_feedback(uuid4(), SessionFeedbackRequest(useful=True, comment=""))


# ===================================================================
# State update logic (_update_diagnostic_state)
# ===================================================================


class TestUpdateDiagnosticState:
    def test_asked_questions_appended_on_question_result(self):
        state_json = sample_state_json(asked_questions=[])
        SessionUseCases._update_diagnostic_state(state_json, {
            "result": "question",
            "current_node": "n1",
            "current_symptom": "Paradas de motor",
        })
        assert "Paradas de motor:n1" in state_json["asked_questions"]

    def test_asked_questions_no_duplicates(self):
        state_json = sample_state_json(asked_questions=["Paradas de motor:n1"])
        SessionUseCases._update_diagnostic_state(state_json, {
            "result": "question",
            "current_node": "n1",
            "current_symptom": "Paradas de motor",
        })
        assert state_json["asked_questions"] == ["Paradas de motor:n1"]

    def test_facts_accumulate(self):
        state_json = sample_state_json(facts={})
        SessionUseCases._update_diagnostic_state(state_json, {
            "result": "question",
            "answered_node": "n1",
            "answer": "Si",
        })
        assert state_json["facts"]["n1"] == "si"

    def test_active_hypotheses_set_from_diagnostic_output(self):
        state_json = sample_state_json(active_hypotheses=[])
        SessionUseCases._update_diagnostic_state(state_json, {
            "diagnostic_output": {
                "primary_hypothesis": "Bateria descargada",
                "confidence": 0.97,
            }
        })
        assert len(state_json["active_hypotheses"]) == 1
        assert state_json["active_hypotheses"][0]["label"] == "Bateria descargada"

    def test_tags_persisted_when_present(self):
        """Fase 5.3: tags from free_text_parser must be stored in state_json."""
        state_json = sample_state_json()
        SessionUseCases._update_diagnostic_state(state_json, {
            "result": "weak_evidence",
            "tags": ["hot_engine", "stalling"],
            "parser_source": "llm",
        })
        assert state_json.get("last_tags") == ["hot_engine", "stalling"]
        assert state_json.get("last_parser_source") == "llm"

    def test_tags_not_persisted_when_absent(self):
        state_json = sample_state_json()
        SessionUseCases._update_diagnostic_state(state_json, {
            "result": "question",
            "current_node": "n1",
        })
        assert "last_tags" not in state_json


# ===================================================================
# Final result extraction
# ===================================================================


class TestExtractFinalResult:
    def test_extracts_primary_hypothesis(self):
        result = SessionUseCases._extract_final_result({
            "diagnostic_output": {"primary_hypothesis": "Bateria descargada", "confidence": 0.97},
        })
        assert result == "Bateria descargada"

    def test_returns_none_without_hypothesis(self):
        result = SessionUseCases._extract_final_result({})
        assert result is None

    def test_returns_none_with_empty_hypothesis(self):
        result = SessionUseCases._extract_final_result({
            "diagnostic_output": {"primary_hypothesis": "", "confidence": 0.0},
        })
        assert result is None
