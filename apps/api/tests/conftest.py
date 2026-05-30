"""Shared fixtures and mocks for all test modules.

NOTE: This file is also the single source of truth for shared test constants
and factory functions. helpers.py re-exports from here.
"""

import os
import sys
from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

# Ensure helpers.py is importable regardless of working directory.
_tests_dir = os.path.dirname(__file__)
if _tests_dir not in sys.path:
    sys.path.insert(0, _tests_dir)

from app.application.orchestrator.langgraph_flow import ConversationGraph, ConversationGraphResult
from app.modules.faq_matcher.service import FAQItem, FAQMatch
from app.modules.free_text_parser.service import ParsedFreeText
from app.modules.historical_retrieval.service import RetrievalCandidate
from app.modules.hybrid_ranking.service import RankedHypothesis, HybridRankingService
from app.modules.tree_engine.service import DiagnosticTreeEngine, TreeStepResult
from app.modules.vin_lookup.service import VehicleInfo
from app.schemas.responses import SessionStateResponse


# ---------------------------------------------------------------------------
# Sample data constants (single source of truth)
# ---------------------------------------------------------------------------

SAMPLE_VEHICLE = VehicleInfo(
    vin="AK550-POC-0001",
    model="AK550",
    family="Scooter GT",
    model_year=2022,
    market="ES",
)

SAMPLE_TREE = {
    "start_node": "n1",
    "nodes": {
        "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "n2", "no": "n3"}},
        "n2": {"type": "question", "text": "Hace ruido?", "answers": {"si": "n4", "no": "n5"}},
        "n3": {"type": "diagnosis", "result": "Bateria descargada"},
        "n4": {"type": "diagnosis", "result": "Motor arranque defectuoso"},
        "n5": {"type": "diagnosis", "result": "Mal contacto"},
    },
}

SAMPLE_FAQS = [
    FAQItem(faq_id=1, model="AK550", category="Testigo", question="Por que se enciende el testigo CELP?", answer="Puede ser un sensor de oxigeno."),
    FAQItem(faq_id=2, model="AK550", category="Motor", question="Por que se para el motor?", answer="Revisar bomba de gasolina."),
    FAQItem(faq_id=3, model=None, category="General", question="Que mantenimiento necesita?", answer="Mantenimiento segun manual."),
]


def sample_state_json(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "facts": {},
        "active_hypotheses": [],
        "asked_questions": [],
        "orchestration": {"last_route": "vin_lookup", "entry_point": None, "last_confidence": 0.0},
    }
    defaults.update(overrides)
    return defaults


def sample_session_state(**overrides: Any) -> SessionStateResponse:
    kwargs = {"vin": None, "model": None, "current_symptom": None, "current_node": None}
    kwargs.update(overrides)
    return SessionStateResponse(**kwargs)


def make_persisted(
    *,
    session_id: UUID | None = None,
    status: str = "active",
    entry_point: str | None = None,
    steps: int = 0,
    vin: str | None = None,
    model: str | None = None,
    current_symptom: str | None = None,
    current_node: str | None = None,
    **state_json_overrides: Any,
) -> "PersistedSession":
    """Build a PersistedSession with defaults or provided overrides."""
    from app.infrastructure.db.repositories.session_repository import PersistedSession
    return PersistedSession(
        session_id=session_id or uuid4(),
        status=status,
        entry_point=entry_point,
        steps=steps,
        state=sample_session_state(vin=vin, model=model, current_symptom=current_symptom, current_node=current_node),
        state_json=sample_state_json(**state_json_overrides),
    )


# ---------------------------------------------------------------------------
# Mock repository builders
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_knowledge_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_vehicle_by_vin.return_value = SAMPLE_VEHICLE
    repo.list_active_faqs.return_value = SAMPLE_FAQS
    repo.list_active_tree_symptoms.return_value = ["Paradas de motor", "Testigo CELP encendido"]
    repo.get_active_tree_by_symptom.return_value = SAMPLE_TREE
    repo.build_symptom_taxonomy.return_value = {
        "tree_symptoms": ["Paradas de motor", "Testigo CELP encendido"],
        "faq_categories": ["Testigo", "Motor"],
        "case_categories": [],
    }
    repo.search_hybrid.return_value = [
        RetrievalCandidate(
            case_id="C1", diagnosis="Bomba combustible",
            vector_score=0.8, lexical_score=0.7, model_match=1.0,
            base_confidence=0.9, frequency=5,
            source_type="historical_case", source_id="C1",
        ),
        RetrievalCandidate(
            case_id="C2", diagnosis="Inyector sucio",
            vector_score=0.6, lexical_score=0.5, model_match=1.0,
            base_confidence=0.7, frequency=3,
            source_type="historical_case", source_id="C2",
        ),
    ]
    return repo


@pytest.fixture
def mock_session_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_session.return_value = None  # override per test
    return repo


@pytest.fixture
def mock_message_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_decision_log_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_feedback_repo() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# Mock service / engine instances
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_embedder() -> MagicMock:
    m = MagicMock()
    m.embed.return_value = [0.1] * 128
    return m


@pytest.fixture
def mock_hybrid_ranker() -> HybridRankingService:
    return HybridRankingService()


@pytest.fixture
def mock_faq_match() -> MagicMock:
    m = MagicMock()
    m.match.return_value = FAQMatch(item=SAMPLE_FAQS[0], score=0.85, scope="model")
    return m


@pytest.fixture
def mock_free_text_parser() -> MagicMock:
    m = MagicMock()
    m.parse.return_value = ParsedFreeText(
        normalized_text="se me para en caliente",
        tags=["hot_engine", "stalling"],
        symptom_category="Paradas de motor",
        reasoning_short="Coincide con patron de parada en caliente.",
        parser_source="llm",
    )
    return m


@pytest.fixture
def mock_vin_resolver() -> MagicMock:
    m = MagicMock()
    m.return_value = SAMPLE_VEHICLE
    return m


@pytest.fixture
def real_tree_engine() -> DiagnosticTreeEngine:
    return DiagnosticTreeEngine()


# ---------------------------------------------------------------------------
# ConversationGraph factory
# ---------------------------------------------------------------------------


@pytest.fixture
def graph_with_mocks(
    mock_vin_resolver: MagicMock,
    mock_knowledge_repo: MagicMock,
    mock_free_text_parser: MagicMock,
    mock_faq_match: MagicMock,
    mock_embedder: MagicMock,
    mock_hybrid_ranker: HybridRankingService,
    real_tree_engine: DiagnosticTreeEngine,
) -> ConversationGraph:
    return ConversationGraph(
        resolve_vin=mock_vin_resolver,
        list_active_faqs=mock_knowledge_repo.list_active_faqs,
        list_active_tree_symptoms=mock_knowledge_repo.list_active_tree_symptoms,
        get_active_tree_by_symptom=mock_knowledge_repo.get_active_tree_by_symptom,
        parse_free_text=mock_free_text_parser.parse,
        faq_match=mock_faq_match.match,
        embed_text=mock_embedder.embed,
        hybrid_search=mock_knowledge_repo.search_hybrid,
        rank_hypotheses=mock_hybrid_ranker.rank,
        tree_engine=real_tree_engine,
    )
