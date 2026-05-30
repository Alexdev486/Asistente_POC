"""Tests for FreeTextParserService.

Covers LLM path, rules fallback, rules-only path, taxonomy validation, and edge cases.
"""

import json
from unittest.mock import MagicMock

import httpx
import pytest

from app.modules.free_text_parser.service import FreeTextParserService, ParsedFreeText


SAMPLE_TAXONOMY = {
    "tree_symptoms": ["Paradas de motor", "Testigo CELP encendido"],
    "faq_categories": ["Testigo", "Motor"],
    "case_categories": [],
}


@pytest.fixture
def mock_llm_gateway() -> MagicMock:
    gw = MagicMock()
    gw.complete.return_value = json.dumps({
        "tags": ["hot_engine", "stalling"],
        "symptom_category": "Paradas de motor",
        "reasoning_short": "Sintomas de parada en caliente.",
    })
    return gw


@pytest.fixture
def parser_with_llm(mock_llm_gateway: MagicMock) -> FreeTextParserService:
    p = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
    return p


@pytest.fixture
def parser_without_llm() -> FreeTextParserService:
    return FreeTextParserService(llm_gateway=None, taxonomy=SAMPLE_TAXONOMY)


# ===================================================================
# LLM path
# ===================================================================


class TestLlmPath:
    def test_llm_parses_successfully(self, parser_with_llm: FreeTextParserService):
        result = parser_with_llm.parse("Se me para en caliente cuando acelero")
        assert result.parser_source == "llm"
        assert "hot_engine" in result.tags
        assert result.symptom_category == "Paradas de motor"
        assert result.reasoning_short

    def test_llm_sets_none_category_when_not_in_taxonomy(self, mock_llm_gateway: MagicMock):
        mock_llm_gateway.complete.return_value = json.dumps({
            "tags": ["weird_noise"],
            "symptom_category": "Categoria inexistente",
            "reasoning_short": "Ruido raro.",
        })
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("hace un ruido raro")
        assert result.symptom_category is None  # invalid category rejected

    def test_llm_tags_not_a_list_triggers_fallback(self, mock_llm_gateway: MagicMock):
        """When LLM returns tags as non-list, ValueError is raised and caught → rules fallback."""
        mock_llm_gateway.complete.return_value = json.dumps({
            "tags": "esto no es una lista",
            "symptom_category": None,
            "reasoning_short": "error",
        })
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("tags malformed")
        assert result.parser_source == "rules_fallback"

    def test_llm_returns_empty_tags(self, mock_llm_gateway: MagicMock):
        mock_llm_gateway.complete.return_value = json.dumps({
            "tags": [],
            "symptom_category": None,
            "reasoning_short": "nada",
        })
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("texto sin clasificar")
        assert result.tags == []
        assert result.symptom_category is None

    def test_llm_json_malformed_triggers_fallback(self, mock_llm_gateway: MagicMock):
        mock_llm_gateway.complete.return_value = "not json at all"
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("se calienta mucho")
        assert result.parser_source == "rules_fallback"
        assert "LLM no disponible" in result.reasoning_short

    def test_llm_http_error_triggers_fallback(self, mock_llm_gateway: MagicMock):
        mock_llm_gateway.complete.side_effect = httpx.HTTPError("Network error")
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("error de red")
        assert result.parser_source == "rules_fallback"

    def test_llm_runtime_error_triggers_fallback(self, mock_llm_gateway: MagicMock):
        mock_llm_gateway.complete.side_effect = RuntimeError("API key missing")
        parser = FreeTextParserService(llm_gateway=mock_llm_gateway, taxonomy=SAMPLE_TAXONOMY)
        result = parser.parse("error de API")
        assert result.parser_source == "rules_fallback"


# ===================================================================
# Rules-only path
# ===================================================================


class TestRulesPath:
    def test_rules_detects_celp(self, parser_without_llm: FreeTextParserService):
        result = parser_without_llm.parse("se ha encendido el testigo CELP")
        assert result.parser_source == "rules"
        assert "celp_light" in result.tags
        assert result.symptom_category == "Testigo CELP encendido"

    def test_rules_detects_stalling(self, parser_without_llm: FreeTextParserService):
        result = parser_without_llm.parse("se para en caliente la bomba")
        assert result.parser_source == "rules"
        assert "hot_engine" in result.tags
        assert "fuel_pump" in result.tags
        assert result.symptom_category == "Paradas de motor"

    def test_rules_no_match_returns_none_category(self, parser_without_llm: FreeTextParserService):
        result = parser_without_llm.parse("texto sin ninguna keyword relevante")
        assert result.parser_source == "rules"
        assert result.tags == []
        assert result.symptom_category is None

    def test_rules_with_partial_keywords(self, parser_without_llm: FreeTextParserService):
        result = parser_without_llm.parse("despues de repostar")
        assert "after_refuel" in result.tags
        assert result.symptom_category == "Paradas de motor"

    def test_rules_category_validated_against_taxonomy(self):
        """If rules infer a category not in taxonomy, it should be set to None."""
        empty_taxonomy = {"tree_symptoms": [], "faq_categories": [], "case_categories": []}
        parser = FreeTextParserService(llm_gateway=None, taxonomy=empty_taxonomy)
        result = parser.parse("celp encendido")
        # 'Testigo CELP encendido' is not in empty taxonomy
        assert result.symptom_category is None


# ===================================================================
# Edge cases
# ===================================================================


class TestEdgeCases:
    def test_empty_text(self, parser_with_llm: FreeTextParserService):
        result = parser_with_llm.parse("")
        assert isinstance(result, ParsedFreeText)

    def test_very_long_text(self, parser_with_llm: FreeTextParserService):
        long_text = "a" * 5000
        result = parser_with_llm.parse(long_text)
        assert isinstance(result, ParsedFreeText)

    def test_special_characters(self, parser_with_llm: FreeTextParserService):
        result = parser_with_llm.parse("¿¡Carácteres especiales!? 123")
        assert isinstance(result, ParsedFreeText)

    def test_set_taxonomy_updates_category_validation(self):
        parser = FreeTextParserService(llm_gateway=None, taxonomy={})
        result = parser.parse("celp")
        assert result.symptom_category is None
        # Update taxonomy
        parser.set_taxonomy({"tree_symptoms": ["Testigo CELP encendido"], "faq_categories": [], "case_categories": []})
        result2 = parser.parse("celp")
        assert result2.symptom_category == "Testigo CELP encendido"

    def test_normalize_strips_accents(self):
        result = FreeTextParserService._normalize("SÍ SE CALIENTA")
        assert "si" in result
        assert "calienta" in result
        assert "í" not in result

    def test_normalize_removes_punctuation(self):
        result = FreeTextParserService._normalize("hola, cómo estás?")
        assert "hola" in result
        assert "como" in result
        assert "estas" in result
        assert "," not in result
        assert "?" not in result

    def test_extract_json_with_code_block(self):
        raw = "```json\n{\"tags\": [\"test\"], \"symptom_category\": null, \"reasoning_short\": \"ok\"}\n```"
        result = FreeTextParserService._extract_json(raw)
        assert result["tags"] == ["test"]

    def test_extract_json_plain(self):
        raw = '{"tags": ["a"], "symptom_category": "b", "reasoning_short": "c"}'
        result = FreeTextParserService._extract_json(raw)
        assert result["tags"] == ["a"]
