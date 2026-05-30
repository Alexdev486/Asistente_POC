import pytest

from app.modules.tree_engine.service import DiagnosticTreeEngine, _normalize_tree_answer


def test_tree_engine_advances_to_diagnosis() -> None:
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "n2", "no": "n3"}},
            "n2": {"type": "diagnosis", "result": "Bateria descargada"},
            "n3": {"type": "diagnosis", "result": "Motor de arranque"},
        },
    }

    engine = DiagnosticTreeEngine()
    first = engine.start(tree)
    assert first.node_type == "question"
    assert first.question == "Arranca?"

    second = engine.advance(tree, first.node_id, "si")
    assert second.node_type == "diagnosis"
    assert second.diagnosis == "Bateria descargada"


# ---------------------------------------------------------------------------
# _normalize_tree_answer — synonym expansion (CRITICAL for robustness)
# ---------------------------------------------------------------------------


class TestNormalizeTreeAnswer:
    """Verify all synonym variants resolve to the correct canonical answer.

    This is critical because users may answer with synonyms like "sí", "yes",
    "vale", "nope", etc. If the synonym map breaks, tree navigation fails
    with a ValueError.
    """

    @pytest.mark.parametrize("answer,expected", [
        # Canonical forms
        ("si", "si"),
        ("no", "no"),
        # Si synonyms
        ("sí", "si"),
        ("s", "si"),
        ("yes", "si"),
        ("vale", "si"),
        ("ok", "si"),
        ("okay", "si"),
        ("claro", "si"),
        ("correcto", "si"),
        ("afirmativo", "si"),
        # No synonyms
        ("n", "no"),
        ("nope", "no"),
        ("nunca", "no"),
        ("tampoco", "no"),
        ("negativo", "no"),
        ("nada", "no"),
        # Whitespace is stripped
        ("  si  ", "si"),
        ("  no  ", "no"),
        # Case insensitivity
        ("SI", "si"),
        ("NO", "no"),
        ("Sí", "si"),
        ("VALE", "si"),
        # Unknown values pass through unchanged
        ("unknown", "unknown"),
        ("", ""),
        ("quizas", "quizas"),
    ])
    def test_all_synonyms(self, answer: str, expected: str) -> None:
        assert _normalize_tree_answer(answer) == expected

    def test_tree_engine_advances_with_synonyms(self) -> None:
        """Integration check: tree engine advance works with all si/no synonyms."""
        tree = {
            "start_node": "n1",
            "nodes": {
                "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "n2", "no": "n3"}},
                "n2": {"type": "diagnosis", "result": "Bateria descargada"},
                "n3": {"type": "diagnosis", "result": "Motor de arranque"},
            },
        }
        engine = DiagnosticTreeEngine()
        first = engine.start(tree)

        # Try every si synonym — all should advance to n2
        for synonym in ["si", "sí", "s", "yes", "vale", "ok", "okay", "claro", "correcto", "afirmativo"]:
            step = engine.advance(tree, first.node_id, synonym)
            assert step.node_type == "diagnosis", f"synonym {synonym!r} should advance to diagnosis"
            assert step.diagnosis == "Bateria descargada"

        # Try every no synonym — all should advance to n3
        for synonym in ["no", "n", "nope", "nunca", "tampoco", "negativo", "nada"]:
            step = engine.advance(tree, first.node_id, synonym)
            assert step.node_type == "diagnosis", f"synonym {synonym!r} should advance to diagnosis"
            assert step.diagnosis == "Motor de arranque"

    def test_invalid_answer_raises_value_error(self) -> None:
        """Unknown answers still raise ValueError as expected."""
        tree = {
            "start_node": "n1",
            "nodes": {
                "n1": {"type": "question", "text": "Arranca?", "answers": {"si": "n2", "no": "n3"}},
            },
        }
        engine = DiagnosticTreeEngine()
        first = engine.start(tree)
        with pytest.raises(ValueError, match="Respuesta no valida"):
            engine.advance(tree, first.node_id, "quizas")
