from dataclasses import dataclass
from typing import Any

# Synonym map for tree navigation answers.
_ANSWER_SYNONYMS: dict[str, list[str]] = {
    "si": ["si", "sí", "s", "yes", "vale", "ok", "okay", "claro", "correcto", "afirmativo"],
    "no": ["no", "n", "nope", "nunca", "tampoco", "negativo", "nada"],
}


def _normalize_tree_answer(raw: str) -> str:
    """Normalize a user answer for tree navigation with fuzzy matching."""
    cleaned = raw.strip().lower()
    for canonical, variants in _ANSWER_SYNONYMS.items():
        if cleaned in variants:
            return canonical
    return cleaned


@dataclass
class TreeStepResult:
    node_id: str
    node_type: str
    question: str | None = None
    diagnosis: str | None = None


class DiagnosticTreeEngine:
    def start(self, tree_json: dict[str, Any]) -> TreeStepResult:
        start_node = tree_json["start_node"]
        return self._build_step(tree_json, start_node)

    def advance(self, tree_json: dict[str, Any], current_node: str, answer: str) -> TreeStepResult:
        node = tree_json["nodes"][current_node]
        normalized_answer = _normalize_tree_answer(answer)
        next_node = node["answers"].get(normalized_answer)
        if not next_node:
            raise ValueError("Respuesta no valida para este nodo.")
        return self._build_step(tree_json, next_node)

    def _build_step(self, tree_json: dict[str, Any], node_id: str) -> TreeStepResult:
        node = tree_json["nodes"][node_id]
        node_type = node["type"]
        if node_type == "question":
            return TreeStepResult(node_id=node_id, node_type=node_type, question=node["text"])
        return TreeStepResult(node_id=node_id, node_type=node_type, diagnosis=node["result"])

