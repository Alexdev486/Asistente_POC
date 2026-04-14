from dataclasses import dataclass
from typing import Any


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
        normalized_answer = answer.strip().lower()
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

