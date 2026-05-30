"""Tests for FastAPI endpoints using TestClient.

Covers health, session start, message, get, feedback, get_messages, and metrics.
"""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


# ===================================================================
# Health
# ===================================================================


class TestHealth:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ===================================================================
# Session start
# ===================================================================


class TestStartSession:
    @patch("app.application.use_cases.session_use_cases.SessionUseCases.start_session")
    def test_start_returns_session_id(self, mock_start, client: TestClient):
        sid = uuid4()
        mock_start.return_value = type("R", (), {"session_id": sid, "message": "Hola"})()
        resp = client.post("/api/v1/session/start", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data

    def test_start_with_empty_body_works(self, client: TestClient):
        resp = client.post("/api/v1/session/start", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] is not None
        assert "bastidor" in data["message"].lower()


# ===================================================================
# Session message
# ===================================================================


class TestSendMessage:
    def test_message_without_session_returns_422(self, client: TestClient):
        resp = client.post("/api/v1/session/message", json={})
        assert resp.status_code == 422  # missing fields

    def test_message_invalid_session_returns_500_or_404(self, client: TestClient):
        sid = uuid4()
        resp = client.post("/api/v1/session/message", json={"session_id": str(sid), "message": "test"})
        # Session doesn't exist → KeyError → 500 (no custom handler for session use cases)
        assert resp.status_code in (404, 500)

    def test_empty_message_returns_422(self, client: TestClient):
        sid = uuid4()
        resp = client.post("/api/v1/session/message", json={"session_id": str(sid), "message": ""})
        assert resp.status_code == 422

    def test_too_long_message_returns_422(self, client: TestClient):
        sid = uuid4()
        resp = client.post("/api/v1/session/message", json={"session_id": str(sid), "message": "x" * 2000})
        assert resp.status_code == 422

    def test_full_flow_ak550(self, client: TestClient):
        """Complete VIN → Tree → FAQ → Otros → Feedback flow via API."""
        # ── Start ──────────────────────────────────────────────
        r = client.post("/api/v1/session/start", json={})
        assert r.status_code == 200
        sid = r.json()["session_id"]

        # ── VIN lookup ─────────────────────────────────────────
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "AK550-POC-0001"})
        assert r.status_code == 200
        d = r.json()
        assert d["state"]["vin"] == "AK550-POC-0001"
        assert d["state"]["model"] == "AK550"
        assert d["quick_replies"] is not None

        # ── Tree engine: symptom selection ─────────────────────
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Sintomas frecuentes"})
        assert r.status_code == 200
        d = r.json()
        assert d["message"] is not None

        # Select a symptom (Paradas de motor is a valid tree for AK550)
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Paradas de motor"})
        assert r.status_code == 200
        d = r.json()
        assert d["state"]["current_symptom"] is not None
        assert d["state"]["current_node"] is not None

        # Answer tree question
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "si"})
        assert r.status_code == 200
        d = r.json()
        # May get another question or a diagnosis — both are valid
        assert "diagnostic_output" not in d or d["diagnostic_output"] is None or "primary_hypothesis" in d["diagnostic_output"]

        # ── FAQ ────────────────────────────────────────────────
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Consultas frecuentes"})
        assert r.status_code == 200
        d = r.json()
        assert d["quick_replies"] is not None or "FAQ" in d["message"] or "consulta" in d["message"].lower()

        # Ask FAQ question
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Por que se enciende el testigo CELP?"})
        assert r.status_code == 200
        d = r.json()
        # FAQ should return diagnostic_output or a message
        assert d["message"] is not None

        # ── Otros / free text ──────────────────────────────────
        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Otros"})
        assert r.status_code == 200
        d = r.json()
        assert "describe" in d["message"].lower() or "palabras" in d["message"].lower()

        # Describe a problem (free text)
        r = client.post("/api/v1/session/message", json={
            "session_id": sid,
            "message": "La moto se calienta mucho y se para en semaforos",
        })
        assert r.status_code == 200
        d = r.json()
        # Should get some kind of response
        assert d["message"] is not None

        # ── Feedback ───────────────────────────────────────────
        r = client.post(f"/api/v1/session/{sid}/feedback", json={"useful": True, "comment": "Funciona muy bien la POC"})
        assert r.status_code == 200
        assert r.json()["saved"] is True

        # ── Verify session is completed ────────────────────────
        r = client.get(f"/api/v1/session/{sid}")
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

        # ── Verify messages are accessible ─────────────────────
        r = client.get(f"/api/v1/session/{sid}/messages")
        assert r.status_code == 200
        assert len(r.json()["messages"]) >= 5  # welcome + vin + tree + faq + otros + feedback


class TestFullFlowEdgeCases:
    """Complete flow with edge cases."""

    def test_full_flow_xciting(self, client: TestClient):
        """XCiting 400 VIN → FAQ → Feedback flow."""
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "XCITING-POC-0001"})
        assert r.status_code == 200
        assert r.json()["state"]["model"] == "Xciting 400"

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Consultas frecuentes"})
        assert r.status_code == 200

        r = client.post(f"/api/v1/session/{sid}/feedback", json={"useful": False, "comment": "No me ayudo"})
        assert r.status_code == 200
        assert r.json()["saved"] is True

    def test_full_flow_invalid_vin_then_valid(self, client: TestClient):
        """Invalid VIN then correct VIN."""
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "VIN-INVALIDO"})
        assert r.status_code == 200
        assert "no he podido identificar" in r.json()["message"].lower()

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "AK550-POC-0001"})
        assert r.status_code == 200
        assert r.json()["state"]["vin"] == "AK550-POC-0001"

    def test_full_flow_out_of_scope_then_menu(self, client: TestClient):
        """Out of scope message then valid menu command."""
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]

        client.post("/api/v1/session/message", json={"session_id": sid, "message": "AK550-POC-0001"})

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "blah blah blah"})
        assert r.status_code == 200

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "Sintomas frecuentes"})
        assert r.status_code == 200

    def test_vin_not_found_returns_error_message(self, client: TestClient):
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]

        r = client.post("/api/v1/session/message", json={"session_id": sid, "message": "VIN-INEXISTENTE"})
        assert r.status_code == 200
        data = r.json()
        assert "no he podido identificar" in data["message"].lower()


# ===================================================================
# Get messages
# ===================================================================


class TestGetMessages:
    def test_get_messages_returns_list(self, client: TestClient):
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]

        r = client.get(f"/api/v1/session/{sid}/messages")
        assert r.status_code == 200
        data = r.json()
        assert "messages" in data
        assert len(data["messages"]) >= 1  # welcome message
        assert data["messages"][0]["role"] is not None

    def test_get_messages_unknown_session(self, client: TestClient):
        r = client.get(f"/api/v1/session/{uuid4()}/messages")
        assert r.status_code == 404


# ===================================================================
# Feedback
# ===================================================================


class TestFeedback:
    def test_feedback_saves(self, client: TestClient):
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]
        # Send VIN first
        client.post("/api/v1/session/message", json={"session_id": sid, "message": "AK550-POC-0001"})

        r = client.post(f"/api/v1/session/{sid}/feedback", json={"useful": True, "comment": "Funciona bien"})
        assert r.status_code == 200
        assert r.json()["saved"] is True

    def test_feedback_invalid_session(self, client: TestClient):
        r = client.post(f"/api/v1/session/{uuid4()}/feedback", json={"useful": True, "comment": "test"})
        assert r.status_code in (404, 500)

    def test_feedback_upsert_allows_resubmission(self, client: TestClient):
        """Feedback ON CONFLICT upsert — second submission succeeds."""
        r = client.post("/api/v1/session/start", json={})
        sid = r.json()["session_id"]
        client.post("/api/v1/session/message", json={"session_id": sid, "message": "AK550-POC-0001"})

        r1 = client.post(f"/api/v1/session/{sid}/feedback", json={"useful": True, "comment": "Primero"})
        assert r1.status_code == 200

        r2 = client.post(f"/api/v1/session/{sid}/feedback", json={"useful": False, "comment": "Segundo"})
        assert r2.status_code == 200
        assert r2.json()["saved"] is True


# ===================================================================
# Metrics
# ===================================================================


class TestMetrics:
    def test_metrics_summary_returns_ok(self, client: TestClient):
        r = client.get("/api/v1/metrics/summary")
        assert r.status_code == 200
        data = r.json()
        # Schema validation: all expected fields present
        assert "total_sessions" in data
        assert "completed_sessions" in data
        assert "avg_steps_per_session" in data
        assert "avg_session_seconds" in data
        assert "faq_usage" in data
        assert "tree_usage" in data
        assert "other_usage" in data
        assert "positive_feedback" in data
        assert "negative_feedback" in data
        assert "most_frequent_final_result" in data

    def test_metrics_types(self, client: TestClient):
        """Verify types of metrics fields."""
        r = client.get("/api/v1/metrics/summary")
        data = r.json()
        assert isinstance(data["total_sessions"], int)
        assert isinstance(data["completed_sessions"], int)
        assert isinstance(data["avg_steps_per_session"], float | int)
        assert isinstance(data["faq_usage"], int)
