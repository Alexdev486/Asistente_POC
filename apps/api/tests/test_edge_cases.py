"""Edge case and error handling tests.

Covers VIN validation, LLM failures, payload edge cases, and schema validation.
"""

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.requests import SessionMessageRequest, SessionFeedbackRequest, StartSessionRequest
from app.schemas.responses import (
    StartSessionResponse,
    SessionMessageResponse,
    SessionStateResponse,
    FeedbackResponse,
    MessagesListResponse,
    MessageResponse,
    SessionDetailResponse,
)


# ===================================================================
# Schema / Contract validation
# ===================================================================


class TestRequestSchemas:
    def test_message_request_valid(self):
        req = SessionMessageRequest(session_id=uuid4(), message="Hola")
        assert req.message == "Hola"

    def test_message_request_empty_message_raises(self):
        with pytest.raises(ValidationError):
            SessionMessageRequest(session_id=uuid4(), message="")

    def test_message_request_too_long_raises(self):
        with pytest.raises(ValidationError):
            SessionMessageRequest(session_id=uuid4(), message="x" * 2000)

    def test_feedback_request_valid(self):
        req = SessionFeedbackRequest(useful=True, comment="Bien")
        assert req.useful is True

    def test_feedback_request_no_comment(self):
        req = SessionFeedbackRequest(useful=False)
        assert req.comment is None

    def test_feedback_request_too_long_comment(self):
        with pytest.raises(ValidationError):
            SessionFeedbackRequest(useful=True, comment="x" * 2000)

    def test_start_request_empty_body(self):
        req = StartSessionRequest()
        assert req.metadata == {}


class TestResponseSchemas:
    def test_start_session_response(self):
        sid = uuid4()
        resp = StartSessionResponse(session_id=sid, message="Bienvenido")
        assert resp.session_id == sid

    def test_session_state_response_defaults(self):
        state = SessionStateResponse()
        assert state.vin is None
        assert state.model is None
        assert state.current_symptom is None
        assert state.current_node is None

    def test_session_message_response_minimal(self):
        resp = SessionMessageResponse(
            session_id=uuid4(),
            message="Test",
            state=SessionStateResponse(),
        )
        assert resp.message == "Test"
        assert resp.diagnostic_output is None

    def test_message_response_schema(self):
        msg = MessageResponse(message_id=1, role="user", content="Hola", created_at="2024-01-01T00:00:00")
        assert msg.role == "user"

    def test_messages_list_response(self):
        sid = uuid4()
        msgs = [
            MessageResponse(message_id=1, role="user", content="Hola", created_at=None),
            MessageResponse(message_id=2, role="assistant", content="Adios", created_at=None),
        ]
        resp = MessagesListResponse(session_id=sid, messages=msgs)
        assert len(resp.messages) == 2

    def test_feedback_response(self):
        resp = FeedbackResponse(session_id=uuid4(), saved=True, message="OK")
        assert resp.saved is True

    def test_session_detail_response(self):
        sid = uuid4()
        resp = SessionDetailResponse(
            session_id=sid,
            status="active",
            entry_point=None,
            steps=0,
            state=SessionStateResponse(),
            state_json={},
        )
        assert resp.status == "active"


# ===================================================================
# VIN edge cases
# ===================================================================


class TestVINEdgeCases:
    def test_vin_with_spaces(self):
        """VIN should be stripped of spaces."""
        from app.modules.vin_lookup.service import VINLookupService
        service = VINLookupService()
        # Using internal mock DB
        result = service.resolve("  AK550-POC-0001  ")
        assert result is not None
        assert result.vin == "AK550-POC-0001"

    def test_vin_lowercase(self):
        """VIN should be uppercased."""
        from app.modules.vin_lookup.service import VINLookupService
        service = VINLookupService()
        result = service.resolve("ak550-poc-0001")
        assert result is not None
        assert result.vin == "AK550-POC-0001"

    def test_vin_not_found(self):
        from app.modules.vin_lookup.service import VINLookupService
        service = VINLookupService()
        result = service.resolve("NO-EXISTE-12345")
        assert result is None

    def test_vin_empty(self):
        from app.modules.vin_lookup.service import VINLookupService
        service = VINLookupService()
        result = service.resolve("")
        assert result is None

    def test_vin_with_special_chars(self):
        from app.modules.vin_lookup.service import VINLookupService
        service = VINLookupService()
        result = service.resolve("AK550-POC-0001!@#")
        # After strip().upper() this becomes "AK550-POC-0001!@#", won't match
        assert result is None


# ===================================================================
# Tree engine edge cases
# ===================================================================


class TestTreeEngineEdgeCases:
    def test_tree_direct_diagnosis(self):
        """Tree that goes directly to diagnosis (no questions)."""
        from app.modules.tree_engine.service import DiagnosticTreeEngine
        engine = DiagnosticTreeEngine()
        tree = {
            "start_node": "d1",
            "nodes": {
                "d1": {"type": "diagnosis", "result": "Fallo directo"},
            },
        }
        result = engine.start(tree)
        assert result.node_type == "diagnosis"
        assert result.diagnosis == "Fallo directo"

    def test_tree_invalid_answer_raises(self):
        from app.modules.tree_engine.service import DiagnosticTreeEngine
        engine = DiagnosticTreeEngine()
        tree = {
            "start_node": "n1",
            "nodes": {
                "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "d1", "no": "d2"}},
                "d1": {"type": "diagnosis", "result": "OK"},
                "d2": {"type": "diagnosis", "result": "Fallo"},
            },
        }
        engine.start(tree)
        with pytest.raises(ValueError):
            engine.advance(tree, "n1", "quizas")


# ===================================================================
# FAQ edge cases
# ===================================================================


class TestFAQEdgeCases:
    def test_no_faqs_returns_none(self):
        from app.modules.faq_matcher.service import FAQMatcherService
        matcher = FAQMatcherService()
        result = matcher.match("AK550", "pregunta", [])
        assert result is None

    def test_threshold_filtering(self):
        from app.modules.faq_matcher.service import FAQMatcherService, FAQItem
        matcher = FAQMatcherService()
        faqs = [FAQItem(faq_id=1, model="AK550", category="X", question="Pregunta completamente diferente", answer="Resp")]
        # Query "celp" to a faq about "Pregunta completamente diferente" should be low score
        result = matcher.match("AK550", "celp", faqs)
        # Should be below 0.25 threshold, so returns None
        assert result is None

    def test_substring_score_boost(self):
        from app.modules.faq_matcher.service import FAQMatcherService, FAQItem
        matcher = FAQMatcherService()
        faqs = [
            FAQItem(faq_id=1, model="AK550", category="X", question="Por que se enciende el testigo CELP?", answer="Sensor"),
        ]
        # Exact substring match should get boost
        result = matcher.match("AK550", "testigo CELP", faqs)
        assert result is not None


# ===================================================================
# Hybrid ranking edge cases
# ===================================================================


class TestHybridRankingEdgeCases:
    def test_empty_candidates(self):
        from app.modules.hybrid_ranking.service import HybridRankingService
        ranker = HybridRankingService()
        result = ranker.rank([], top_k=3)
        assert result == []

    def test_single_candidate(self):
        from app.modules.hybrid_ranking.service import HybridRankingService
        from app.modules.historical_retrieval.service import RetrievalCandidate
        ranker = HybridRankingService()
        candidates = [
            RetrievalCandidate(case_id="C1", diagnosis="Test", vector_score=0.8, lexical_score=0.5,
                               model_match=1.0, base_confidence=0.9, frequency=1),
        ]
        result = ranker.rank(candidates, top_k=3)
        assert len(result) == 1
        assert result[0].diagnosis == "Test"

    def test_scores_ordered_descending(self):
        from app.modules.hybrid_ranking.service import HybridRankingService
        from app.modules.historical_retrieval.service import RetrievalCandidate
        ranker = HybridRankingService()
        candidates = [
            RetrievalCandidate(case_id="C1", diagnosis="Low", vector_score=0.1, lexical_score=0.1,
                               model_match=0.1, base_confidence=0.1, frequency=1),
            RetrievalCandidate(case_id="C2", diagnosis="High", vector_score=0.9, lexical_score=0.9,
                               model_match=0.9, base_confidence=0.9, frequency=1),
        ]
        result = ranker.rank(candidates, top_k=2)
        assert result[0].diagnosis == "High"
        assert result[1].diagnosis == "Low"
        assert result[0].score > result[1].score


# ===================================================================
# Historical retrieval no longer has a service class.
# HistoricalCase and RetrievalCandidate dataclasses are tested
# implicitly via hybrid_ranking tests above.
# ===================================================================
