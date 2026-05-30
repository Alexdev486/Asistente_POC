"""Tests for ConversationGraph (langgraph_flow.py).

Covers routing, all node handlers, state updates, and edge cases.
"""

from unittest.mock import MagicMock

import pytest

from app.application.orchestrator.langgraph_flow import ConversationGraph, ConversationSnapshot
from app.modules.hybrid_ranking.service import HybridRankingService
from app.modules.tree_engine.service import DiagnosticTreeEngine
from app.modules.vin_lookup.service import VehicleInfo
from app.modules.faq_matcher.service import FAQItem, FAQMatch
from app.modules.free_text_parser.service import ParsedFreeText
from helpers import SAMPLE_TREE, SAMPLE_FAQS, SAMPLE_VEHICLE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_graph(
    *,
    resolve_vin=None,
    list_active_faqs=None,
    list_active_tree_symptoms=None,
    get_active_tree_by_symptom=None,
    parse_free_text=None,
    faq_match=None,
    embed_text=None,
    hybrid_search=None,
    rank_hypotheses=None,
    tree_engine=None,
) -> ConversationGraph:
    """Build a ConversationGraph with sensible defaults or provided mocks."""
    return ConversationGraph(
        resolve_vin=resolve_vin or (lambda v: SAMPLE_VEHICLE),
        list_active_faqs=list_active_faqs or (lambda m: SAMPLE_FAQS),
        list_active_tree_symptoms=list_active_tree_symptoms or (lambda m: ["Paradas de motor"]),
        get_active_tree_by_symptom=get_active_tree_by_symptom or (lambda m, s: SAMPLE_TREE),
        parse_free_text=parse_free_text or (
            lambda t: ParsedFreeText(
                normalized_text=t.lower(),
                tags=[],
                symptom_category=None,
                reasoning_short="rules",
                parser_source="rules",
            )
        ),
        faq_match=faq_match or (lambda m, q, f: FAQMatch(item=SAMPLE_FAQS[0], score=0.85, scope="model")),
    embed_text=embed_text or (lambda t: [0.1] * 128),
    hybrid_search=hybrid_search or (lambda **kw: []),
    rank_hypotheses=rank_hypotheses or HybridRankingService().rank,
    tree_engine=tree_engine or DiagnosticTreeEngine(),
    )


def snapshot(**kwargs):
    defaults = dict(
        vin=None, model=None, entry_point=None,
        current_symptom=None, current_node=None, asked_questions=[],
    )
    defaults.update(kwargs)
    return ConversationSnapshot(**defaults)


# ===================================================================
# Routing tests
# ===================================================================


class TestRouting:
    def test_no_vin_routes_to_vin_lookup(self):
        graph = make_graph()
        result = graph.run_turn(snapshot(), "AK550-POC-0001")
        assert result.route == "vin_lookup"

    def test_menu_cmd_tree_routes_to_tree(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Sintomas frecuentes",
        )
        assert result.route == "tree_engine"

    def test_menu_cmd_faq_routes_to_faq(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Consultas frecuentes",
        )
        assert result.route == "faq_matcher"

    def test_menu_cmd_other_routes_to_free_text(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Otros",
        )
        assert result.route == "free_text_parser"

    def test_entry_point_faq_routes_to_faq(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="faq"),
            "mi pregunta de prueba",
        )
        assert result.route == "faq_matcher"

    def test_entry_point_tree_routes_to_tree(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree", current_symptom="Paradas de motor", current_node="n1"),
            "si",
        )
        assert result.route == "tree_engine"

    def test_entry_point_other_routes_to_free_text(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="other"),
            "descripcion del problema",
        )
        assert result.route == "free_text_parser"

    def test_unknown_text_routes_to_free_text_parser(self):
        """When no entry_point is set, any non-menu text routes to free_text_parser."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "cualquier cosa rara",
        )
        assert result.route == "free_text_parser"

    def test_tree_variants_are_normalized(self):
        graph = make_graph()
        for variant in ["sintomas", "sintoma", "sintomas frecuentes", "arbol"]:
            result = graph.run_turn(
                snapshot(vin="AK550-POC-0001", model="AK550"),
                variant,
            )
            assert result.route == "tree_engine", f"{variant!r} should route to tree"

    def test_faq_variants_are_normalized(self):
        graph = make_graph()
        for variant in ["faq", "faqs", "consultas frecuentes", "preguntas", "consulta"]:
            result = graph.run_turn(
                snapshot(vin="AK550-POC-0001", model="AK550"),
                variant,
            )
            assert result.route == "faq_matcher", f"{variant!r} should route to faq"

    def test_other_variants_are_normalized(self):
        graph = make_graph()
        for variant in ["otros", "texto libre", "otro", "libre"]:
            result = graph.run_turn(
                snapshot(vin="AK550-POC-0001", model="AK550"),
                variant,
            )
            assert result.route == "free_text_parser", f"{variant!r} should route to free_text_parser"
    
    def test_otra_consulta_contains_consulta_routes_to_faq(self):
        """'otra consulta' contains 'consulta' which matches FAQ first."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "otra consulta",
        )
        assert result.route == "faq_matcher"


# ===================================================================
# VIN Lookup node
# ===================================================================


class TestVinLookup:
    def test_identifies_vehicle(self):
        graph = make_graph()
        result = graph.run_turn(snapshot(), "AK550-POC-0001")
        assert result.route == "vin_lookup"
        assert "identificado" in result.assistant_message.lower()
        assert "AK550" in result.assistant_message
        assert result.confidence == 1.0
        assert result.state_updates["vin"] == "AK550-POC-0001"
        assert result.state_updates["model"] == "AK550"

    def test_vin_not_found(self):
        resolve = MagicMock(return_value=None)
        graph = make_graph(resolve_vin=resolve)
        result = graph.run_turn(snapshot(), "VIN-INEXISTENTE")
        assert result.route == "vin_lookup"
        assert "no he podido identificar" in result.assistant_message.lower()
        assert result.confidence == 0.0
        assert result.decision_output["result"] == "vin_not_found"

    def test_quick_replies_after_vin(self):
        graph = make_graph()
        result = graph.run_turn(snapshot(), "AK550-POC-0001")
        assert result.quick_replies is not None
        assert "Sintomas frecuentes" in result.quick_replies
        assert "Consultas frecuentes" in result.quick_replies
        assert "Otros" in result.quick_replies


# ===================================================================
# Tree Engine node
# ===================================================================


class TestTreeEngine:
    def test_shows_symptom_list_on_entry(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Sintomas frecuentes",
        )
        assert result.route == "tree_engine"
        assert "Selecciona" in result.assistant_message
        assert result.decision_output["result"] == "symptom_selection"

    def test_starts_tree_when_symptom_selected(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "Paradas de motor",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "question"
        assert result.state_updates.get("current_symptom") == "Paradas de motor"
        assert result.state_updates.get("current_node") is not None

    def test_advances_on_valid_answer(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(
                vin="AK550-POC-0001", model="AK550",
                entry_point="tree", current_symptom="Paradas de motor",
                current_node="n1", asked_questions=[],
            ),
            "no",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "diagnosis"
        assert "Bateria" in result.assistant_message

    def test_reports_invalid_answer(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(
                vin="AK550-POC-0001", model="AK550",
                entry_point="tree", current_symptom="Paradas de motor",
                current_node="n1", asked_questions=[],
            ),
            "quizas",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "invalid_answer"
        assert "no valida" in result.assistant_message.lower()

    def test_detects_repeated_question(self):
        graph = make_graph()
        # Advance from n1 with "si" goes to n2 (question "Hace ruido?").
        # If n2 is already in asked_questions, we get question_repeated.
        result = graph.run_turn(
            snapshot(
                vin="AK550-POC-0001", model="AK550",
                entry_point="tree", current_symptom="Paradas de motor",
                current_node="n1", asked_questions=["Paradas de motor:n2"],
            ),
            "si",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "question_repeated"

    def test_invalid_symptom_shows_error(self):
        symptoms_mock = MagicMock(return_value=["Paradas de motor"])
        graph = make_graph(list_active_tree_symptoms=symptoms_mock)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "Sintoma inexistente",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "invalid_symptom"

    def test_tree_not_found(self):
        get_tree = MagicMock(return_value=None)
        graph = make_graph(get_active_tree_by_symptom=get_tree)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "Paradas de motor",
        )
        assert result.route == "tree_engine"
        assert result.decision_output["result"] == "tree_not_found"


# ===================================================================
# FAQ Matcher node
# ===================================================================


class TestFAQMatcher:
    def test_suggests_faqs_on_entry(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Consultas frecuentes",
        )
        assert result.route == "faq_matcher"
        assert result.decision_output["result"] == "faq_suggestions"
        assert len(result.quick_replies or []) <= 3

    def test_matches_question(self):
        faq_match = MagicMock(return_value=FAQMatch(item=SAMPLE_FAQS[0], score=0.85, scope="model"))
        graph = make_graph(faq_match=faq_match)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="faq"),
            "Por que se enciende el testigo CELP?",
        )
        assert result.route == "faq_matcher"
        assert result.decision_output["faq_id"] == 1
        assert result.decision_output["diagnostic_output"] is not None
        assert "FAQ encontrada" in result.assistant_message

    def test_no_match_shows_suggestions(self):
        faq_match = MagicMock(return_value=None)
        graph = make_graph(faq_match=faq_match)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="faq"),
            "consulta sin respuesta",
        )
        assert result.route == "faq_matcher"
        assert result.decision_output["faq_id"] is None
        assert result.decision_output["score"] == 0.0
        assert "no encuentro" in result.assistant_message.lower()


# ===================================================================
# Free Text / Otros node
# ===================================================================


class TestFreeTextParser:
    def test_awaits_text_on_initial_entry(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Otros",
        )
        assert result.route == "free_text_parser"
        assert result.decision_output["result"] == "awaiting_free_text"

    def test_parses_text_and_returns_hypothesis(self):
        from app.modules.historical_retrieval.service import RetrievalCandidate
        parse = MagicMock(return_value=ParsedFreeText(
            normalized_text="se para en caliente",
            tags=["hot_engine"], symptom_category="Paradas de motor",
            reasoning_short="Test", parser_source="llm",
        ))
        hybrid_search = MagicMock(return_value=[
            RetrievalCandidate(
                case_id="C1", diagnosis="Bomba combustible",
                vector_score=0.8, lexical_score=0.7, model_match=1.0,
                base_confidence=0.9, frequency=5,
                source_type="historical_case", source_id="C1",
            ),
        ])
        graph = make_graph(parse_free_text=parse, hybrid_search=hybrid_search)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="other"),
            "Se me para en caliente",
        )
        assert result.route == "free_text_parser"
        assert result.decision_output["top_hypotheses"] is not None
        assert result.decision_output["diagnostic_output"] is not None
        assert "Hipotesis principal" in result.assistant_message

    def test_weak_evidence_guardrail(self):
        from app.modules.faq_matcher.service import FAQMatch
        parse = MagicMock(return_value=ParsedFreeText(
            normalized_text="ruido extrano",
            tags=[], symptom_category=None,
            reasoning_short="Sin clasificacion", parser_source="rules",
        ))
        # No FAQ match and no hybrid candidates → weak_evidence
        faq_match = MagicMock(return_value=None)
        graph = make_graph(parse_free_text=parse, hybrid_search=lambda **kw: [], faq_match=faq_match)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="other"),
            "ruido extrano",
        )
        assert result.route == "free_text_parser"
        assert result.decision_output["result"] == "weak_evidence"

    def test_faq_fallback_when_no_historical_cases(self):
        parse = MagicMock(return_value=ParsedFreeText(
            normalized_text="testigo celp",
            tags=["celp_light"], symptom_category="Testigo CELP encendido",
            reasoning_short="CELP", parser_source="llm",
        ))
        hybrid_search = MagicMock(return_value=[
            type("C", (), {
                "case_id": "C1", "diagnosis": "Test",
                "vector_score": 0.0, "lexical_score": 0.0, "model_match": 1.0,
                "base_confidence": 0.5, "frequency": 1,
                "source_type": "knowledge_chunk", "source_id": "K1",
            })()
        ])
        faq_match = MagicMock(return_value=FAQMatch(item=SAMPLE_FAQS[0], score=0.85, scope="model"))
        graph = make_graph(parse_free_text=parse, hybrid_search=hybrid_search, faq_match=faq_match)
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="other"),
            "testigo celp",
        )
        assert result.route == "free_text_parser"
        assert result.decision_output["result"] == "faq_fallback"

    def test_model_missing_guardrail(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", entry_point="other"),
            "problema motor",
        )
        assert result.route == "free_text_parser"
        assert result.decision_output["result"] == "model_missing"


# ===================================================================
# Menu Selection node
# ===================================================================


class TestMenuSelection:
    def test_empty_message_with_vin_routes_to_out_of_scope(self):
        """Empty string with VIN but no entry_point → out_of_scope."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "",  # empty message
        )
        assert result.route == "out_of_scope"


# ===================================================================
# Out of Scope node
# ===================================================================


class TestOutOfScope:
    def test_reports_out_of_scope_only_on_empty_message(self):
        """out_of_scope is only reached when msg is empty and entry_point is None."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point=None),
            "",
        )
        assert result.route == "out_of_scope"
        assert "fuera del alcance" in result.assistant_message.lower()


# ===================================================================
# State clearing on node switch (Fase 5 fix)
# ===================================================================


class TestStateClearingOnSwitch:
    def test_stale_tree_state_cleared_when_entering_faq(self):
        """Fase 5.1: current_node/current_symptom must be None when FAQ starts."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(
                vin="AK550-POC-0001", model="AK550",
                current_node="n1", current_symptom="Paradas de motor",
            ),
            "Consultas frecuentes",
        )
        assert result.route == "faq_matcher"
        assert result.state_updates.get("current_node") is None
        assert result.state_updates.get("current_symptom") is None

    def test_stale_tree_state_cleared_when_entering_otros(self):
        """Fase 5.2: current_node/current_symptom must be None when Otros starts."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(
                vin="AK550-POC-0001", model="AK550",
                current_node="n1", current_symptom="Paradas de motor",
            ),
            "Otros",
        )
        assert result.route == "free_text_parser"
        assert result.state_updates.get("current_node") is None
        assert result.state_updates.get("current_symptom") is None


# ===================================================================
# Entry point consistency
# ===================================================================


class TestEntryPoint:
    def test_faq_sets_entry_point_faq(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Consultas frecuentes",
        )
        assert result.entry_point == "faq"

    def test_tree_sets_entry_point_tree(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Sintomas frecuentes",
        )
        assert result.entry_point == "tree"

    def test_otros_sets_entry_point_other(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            "Otros",
        )
        assert result.entry_point == "other"


class TestFinishDiagnosis:
    """'Finalizar diagnostico' command routing and behavior."""

    def test_finish_clears_entry_point(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "Finalizar diagnostico",
        )
        assert result.route == "finish_diagnosis"
        assert result.entry_point is None
        assert "finalizado" in result.assistant_message.lower()

    def test_finish_variants_work(self):
        graph = make_graph()
        for variant in ("finalizar", "terminar"):
            result = graph.run_turn(
                snapshot(vin="AK550-POC-0001", model="AK550", entry_point="other"),
                variant,
            )
            assert result.route == "finish_diagnosis", f"{variant} should route to finish"

    def test_finish_after_tree_clears_nodes(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree",
                     current_symptom="Paradas de motor", current_node="n1"),
            "Finalizar diagnostico",
        )
        assert result.route == "finish_diagnosis"
        # state_updates should clear current_node and current_symptom
        updates = result.state_updates or {}
        assert updates.get("current_node") is None
        assert updates.get("current_symptom") is None

    def test_finish_offers_menu_quick_replies(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "Finalizar diagnostico",
        )
        qr = result.quick_replies or []
        assert "Sintomas frecuentes" in qr
        assert "Consultas frecuentes" in qr
        assert "Otros" in qr


# ===================================================================
# Menu Selection node (expanded)
# ===================================================================


class TestMenuSelectionExpanded:
    """Full field assertions for _node_menu_selection."""

    def test_menu_selection_full_output(self):
        """Verify all state fields when user types 'volver al menu'."""
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point="tree"),
            "volver al menu",
        )
        assert result.route == "menu_selection"
        assert "opcion valida" in result.assistant_message.lower()
        assert result.confidence == 0.6
        qr = result.quick_replies or []
        assert "Sintomas frecuentes" in qr
        assert "Consultas frecuentes" in qr
        assert "Otros" in qr
        assert result.decision_output["route"] == "menu_selection"
        assert result.decision_output["entry_point"] == "tree"

    @pytest.mark.parametrize("variant", [
        "volver al menu",
        "volver",
        "menu",
        "menu principal",
        "atras",
        "regresar",
    ])
    def test_menu_variants_all_route_to_menu_selection(self, variant):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550"),
            variant,
        )
        assert result.route == "menu_selection", f"{variant!r} should route to menu_selection"

    def test_empty_message_no_vin_routes_to_out_of_scope(self):
        """Empty string with no VIN → out_of_scope (not menu_selection)."""
        graph = make_graph()
        result = graph.run_turn(snapshot(), "")
        assert result.route == "vin_lookup"


# ===================================================================
# Accent normalization (CRITICAL for Spanish-language routing)
# ===================================================================


class TestAccentNormalization:
    """Verify accented input routes correctly via _remove_accents."""

    def test_accented_menu_commands(self):
        graph = make_graph()
        cases = [
            ("síntomas", "tree_engine"),
            ("síntomas frecuentes", "tree_engine"),
            ("árbol", "tree_engine"),
            ("menú", "menu_selection"),
            ("pregúntas frecuentes", "faq_matcher"),
            ("consultas frEcuentes", "faq_matcher"),
        ]
        for msg, expected_route in cases:
            result = graph.run_turn(
                snapshot(vin="AK550-POC-0001", model="AK550"),
                msg,
            )
            assert result.route == expected_route, (
                f"accented message {msg!r} should route to {expected_route}, got {result.route}"
            )


# ===================================================================
# Out of Scope — full field assertions
# ===================================================================


class TestOutOfScopeExpanded:
    """Verify all state fields for the out_of_scope node."""

    def test_out_of_scope_full_output(self):
        graph = make_graph()
        result = graph.run_turn(
            snapshot(vin="AK550-POC-0001", model="AK550", entry_point=None),
            "",
        )
        assert result.route == "out_of_scope"
        assert result.confidence == 0.2
        assert "fuera del alcance" in result.assistant_message.lower()
        qr = result.quick_replies or []
        assert "Sintomas frecuentes" in qr
        assert "Consultas frecuentes" in qr
        assert "Otros" in qr
        assert result.decision_output["route"] == "out_of_scope"


# ===================================================================
# _build_diagnostic_output — static method unit tests
# ===================================================================


class TestBuildDiagnosticOutput:
    """Direct tests for _build_diagnostic_output (DDT contract compliance)."""

    def test_all_fields_present(self):
        result = ConversationGraph._build_diagnostic_output(
            primary="Bateria descargada",
            alternatives=["Alternador defectuoso"],
            next_check="Revisar alternador",
            short_explanation="Sintomas compatibles con bateria",
            confidence=0.85,
        )
        assert result["primary_hypothesis"] == "Bateria descargada"
        assert result["alternatives"] == ["Alternador defectuoso"]
        assert result["next_check"] == "Revisar alternador"
        assert result["short_explanation"] == "Sintomas compatibles con bateria"
        assert result["confidence"] == 0.85

    def test_empty_alternatives(self):
        result = ConversationGraph._build_diagnostic_output(
            primary="Solo hipotesis",
            alternatives=[],
            next_check="Ninguna",
            short_explanation="Unica posibilidad",
            confidence=0.5,
        )
        assert result["alternatives"] == []

    def test_confidence_clamped_to_max_1_0(self):
        result = ConversationGraph._build_diagnostic_output(
            primary="X", alternatives=[], next_check="", short_explanation="", confidence=1.5,
        )
        assert result["confidence"] == 1.0

    def test_confidence_clamped_to_min_0_0(self):
        result = ConversationGraph._build_diagnostic_output(
            primary="X", alternatives=[], next_check="", short_explanation="", confidence=-0.5,
        )
        assert result["confidence"] == 0.0

    def test_confidence_mid_range_unchanged(self):
        result = ConversationGraph._build_diagnostic_output(
            primary="X", alternatives=[], next_check="", short_explanation="", confidence=0.75,
        )
        assert result["confidence"] == 0.75


# ===================================================================
# _question_key — static method unit tests
# ===================================================================


class TestQuestionKey:
    """Direct tests for _question_key (asked_questions dedup mechanism)."""

    def test_with_symptom(self):
        assert ConversationGraph._question_key("Paradas de motor", "n1") == "Paradas de motor:n1"

    def test_with_none_symptom(self):
        assert ConversationGraph._question_key(None, "n1") == "n1"

    def test_empty_symptom(self):
        """Empty string symptom should also fall back to just node_id."""
        assert ConversationGraph._question_key("", "n2") == "n2"

    def test_with_special_chars(self):
        assert ConversationGraph._question_key("Testigo CELP", "n3") == "Testigo CELP:n3"
