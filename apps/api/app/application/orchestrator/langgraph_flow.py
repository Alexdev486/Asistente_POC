from dataclasses import dataclass
from typing import Any, Callable, Literal, TypedDict

from app.modules.faq_matcher.service import FAQItem, FAQMatch
from app.modules.free_text_parser.service import ParsedFreeText
from app.modules.historical_retrieval.service import RetrievalCandidate
from app.modules.hybrid_ranking.service import RankedHypothesis
from app.modules.tree_engine.service import DiagnosticTreeEngine
from app.modules.vin_lookup.service import VehicleInfo


Route = Literal[
    "vin_lookup",
    "menu_selection",
    "faq_matcher",
    "tree_engine",
    "free_text_parser",
    "out_of_scope",
]

EntryPoint = Literal["faq", "tree", "other"]


@dataclass
class ConversationSnapshot:
    vin: str | None
    model: str | None
    entry_point: str | None
    current_symptom: str | None
    current_node: str | None


class ConversationState(TypedDict):
    user_message: str
    normalized_message: str
    vin: str | None
    model: str | None
    entry_point: EntryPoint | None
    current_symptom: str | None
    current_node: str | None
    route: Route
    assistant_message: str
    confidence: float
    decision_output: dict[str, Any]
    state_updates: dict[str, str | None]


@dataclass
class ConversationGraphResult:
    route: Route
    entry_point: EntryPoint | None
    assistant_message: str
    confidence: float
    decision_output: dict[str, Any]
    state_updates: dict[str, str | None]


class ConversationGraph:
    def __init__(
        self,
        *,
        resolve_vin: Callable[[str], VehicleInfo | None],
        list_active_faqs: Callable[[str | None], list[FAQItem]],
        list_active_tree_symptoms: Callable[[str | None], list[str]],
        get_active_tree_by_symptom: Callable[[str | None, str], dict | None],
        parse_free_text: Callable[[str], ParsedFreeText],
        faq_match: Callable[[str, str, list[FAQItem]], FAQMatch | None],
        embed_text: Callable[[str], list[float]],
        hybrid_search: Callable[[list[float], str, str | None, str | None, int], list[RetrievalCandidate]],
        rank_hypotheses: Callable[[list[RetrievalCandidate], int], list[RankedHypothesis]],
        tree_engine: DiagnosticTreeEngine,
    ) -> None:
        self._resolve_vin = resolve_vin
        self._list_active_faqs = list_active_faqs
        self._list_active_tree_symptoms = list_active_tree_symptoms
        self._get_active_tree_by_symptom = get_active_tree_by_symptom
        self._parse_free_text = parse_free_text
        self._faq_match = faq_match
        self._embed_text = embed_text
        self._hybrid_search = hybrid_search
        self._rank_hypotheses = rank_hypotheses
        self._tree_engine = tree_engine

    def run_turn(self, snapshot: ConversationSnapshot, user_message: str) -> ConversationGraphResult:
        state: ConversationState = {
            "user_message": user_message.strip(),
            "normalized_message": user_message.strip().lower(),
            "vin": snapshot.vin,
            "model": snapshot.model,
            "entry_point": snapshot.entry_point if snapshot.entry_point in {"faq", "tree", "other"} else None,
            "current_symptom": snapshot.current_symptom,
            "current_node": snapshot.current_node,
            "route": "menu_selection",
            "assistant_message": "",
            "confidence": 0.6,
            "decision_output": {},
            "state_updates": {},
        }
        state["route"] = self._route_turn(state)

        if state["route"] == "vin_lookup":
            self._node_vin_lookup(state)
        elif state["route"] == "tree_engine":
            self._node_tree_engine(state)
        elif state["route"] == "faq_matcher":
            self._node_faq_matcher(state)
        elif state["route"] == "free_text_parser":
            self._node_free_text_parser(state)
        else:
            self._node_menu_selection(state)

        return ConversationGraphResult(
            route=state["route"],
            entry_point=state["entry_point"],
            assistant_message=state["assistant_message"],
            confidence=state["confidence"],
            decision_output=state["decision_output"],
            state_updates=state["state_updates"],
        )

    @staticmethod
    def _route_turn(state: ConversationState) -> Route:
        msg = state["normalized_message"]
        if not state["vin"]:
            return "vin_lookup"

        if msg in {"sintomas frecuentes", "sintoma", "sintomas"}:
            return "tree_engine"
        if msg in {"consultas frecuentes", "faq", "faqs"}:
            return "faq_matcher"
        if msg in {"otros", "otra consulta", "texto libre"}:
            return "free_text_parser"

        if state["entry_point"] == "faq":
            return "faq_matcher"
        if state["entry_point"] == "tree":
            return "tree_engine"
        if state["entry_point"] == "other":
            return "free_text_parser"

        return "menu_selection"

    def _node_vin_lookup(self, state: ConversationState) -> None:
        vehicle = self._resolve_vin(state["user_message"])
        if not vehicle:
            state["assistant_message"] = "No he podido identificar ese bastidor. Intenta de nuevo."
            state["confidence"] = 0.0
            state["decision_output"] = {"result": "vin_not_found"}
            return

        state["assistant_message"] = (
            f"He identificado el vehiculo como {vehicle.model} ({vehicle.model_year}). "
            "Selecciona una opcion: Sintomas frecuentes, Consultas frecuentes u Otros."
        )
        state["confidence"] = 1.0
        state["decision_output"] = {"result": "vin_identified", "vin": vehicle.vin, "model": vehicle.model}
        state["state_updates"]["vin"] = vehicle.vin
        state["state_updates"]["model"] = vehicle.model

    def _node_tree_engine(self, state: ConversationState) -> None:
        state["entry_point"] = "tree"
        symptoms = self._list_active_tree_symptoms(state["model"])
        normalized_symptoms = {s.lower(): s for s in symptoms}

        # Si estamos en medio de un arbol, interpretar el mensaje como respuesta al nodo actual
        if state["current_node"] and state["current_symptom"]:
            tree_json = self._get_active_tree_by_symptom(state["model"], state["current_symptom"])
            if tree_json is None:
                state["assistant_message"] = "No encuentro el arbol activo para ese sintoma. Vuelve a seleccionarlo."
                state["confidence"] = 0.2
                state["state_updates"]["current_node"] = None
                state["state_updates"]["current_symptom"] = None
                state["decision_output"] = {"route": "tree_engine", "entry_point": "tree", "result": "tree_not_found"}
                return

            try:
                step = self._tree_engine.advance(tree_json, state["current_node"], state["user_message"])
            except ValueError:
                node_answers = tree_json["nodes"][state["current_node"]].get("answers", {})
                options = ", ".join(node_answers.keys()) if node_answers else "si/no"
                state["assistant_message"] = f"Respuesta no valida para este paso. Opciones: {options}."
                state["confidence"] = 0.3
                state["decision_output"] = {
                    "route": "tree_engine",
                    "entry_point": "tree",
                    "result": "invalid_answer",
                    "current_node": state["current_node"],
                }
                return

            if step.node_type == "question":
                node_answers = tree_json["nodes"][step.node_id].get("answers", {})
                options = ", ".join(node_answers.keys()) if node_answers else "si/no"
                state["assistant_message"] = f"{step.question} (Opciones: {options})"
                state["confidence"] = 0.92
                state["state_updates"]["current_node"] = step.node_id
                state["decision_output"] = {
                    "route": "tree_engine",
                    "entry_point": "tree",
                    "result": "question",
                    "current_symptom": state["current_symptom"],
                    "current_node": step.node_id,
                }
                return

            state["assistant_message"] = (
                f"Diagnostico probable (arbol): {step.diagnosis}. "
                "Si quieres seguimos con otra rama o validamos por FAQ/Otros."
            )
            state["confidence"] = 0.97
            state["state_updates"]["current_node"] = None
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "diagnosis",
                "current_symptom": state["current_symptom"],
                "diagnosis": step.diagnosis,
            }
            return

        # Entrada inicial a arbol: mostrar sintomas disponibles
        if state["normalized_message"] in {"sintomas frecuentes", "sintoma", "sintomas"}:
            options = ", ".join(symptoms) if symptoms else "sin arboles activos"
            state["assistant_message"] = f"Vamos por Sintomas frecuentes. Selecciona: {options}."
            state["confidence"] = 0.95
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "symptom_selection",
                "symptoms": symptoms,
            }
            return

        selected_symptom = normalized_symptoms.get(state["normalized_message"])
        if selected_symptom is None:
            options = ", ".join(symptoms) if symptoms else "sin arboles activos"
            state["assistant_message"] = (
                "No reconozco ese sintoma para arbol. "
                f"Selecciona uno de estos: {options}."
            )
            state["confidence"] = 0.4
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "invalid_symptom",
                "symptoms": symptoms,
            }
            return

        tree_json = self._get_active_tree_by_symptom(state["model"], selected_symptom)
        if tree_json is None:
            state["assistant_message"] = "No hay arbol activo para ese sintoma en este modelo."
            state["confidence"] = 0.2
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "tree_not_found",
                "selected_symptom": selected_symptom,
            }
            return

        step = self._tree_engine.start(tree_json)
        state["state_updates"]["current_symptom"] = selected_symptom
        if step.node_type == "question":
            node_answers = tree_json["nodes"][step.node_id].get("answers", {})
            options = ", ".join(node_answers.keys()) if node_answers else "si/no"
            state["assistant_message"] = f"{step.question} (Opciones: {options})"
            state["confidence"] = 0.93
            state["state_updates"]["current_node"] = step.node_id
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "question",
                "current_symptom": selected_symptom,
                "current_node": step.node_id,
            }
            return

        state["assistant_message"] = (
            f"Diagnostico probable (arbol): {step.diagnosis}. "
            "Si quieres seguimos con otra rama o validamos por FAQ/Otros."
        )
        state["confidence"] = 0.97
        state["state_updates"]["current_node"] = None
        state["decision_output"] = {
            "route": "tree_engine",
            "entry_point": "tree",
            "result": "diagnosis",
            "current_symptom": selected_symptom,
            "diagnosis": step.diagnosis,
        }

    def _node_faq_matcher(self, state: ConversationState) -> None:
        state["entry_point"] = "faq"
        faqs = self._list_active_faqs(state["model"])
        match = self._faq_match(state["model"] or "", state["user_message"], faqs)

        if match:
            state["assistant_message"] = f"FAQ encontrada: {match.item.answer}"
            state["confidence"] = max(0.25, min(match.score, 1.0))
            state["decision_output"] = {
                "route": "faq_matcher",
                "entry_point": "faq",
                "faq_id": match.item.faq_id,
                "score": match.score,
                "scope": match.scope,
            }
            return

        suggested = ", ".join(item.question for item in faqs[:2]) if faqs else "sin FAQs activas"
        state["assistant_message"] = (
            "No encuentro una FAQ exacta con ese texto. "
            f"Prueba con una pregunta mas concreta. Ejemplos: {suggested}."
        )
        state["confidence"] = 0.3
        state["decision_output"] = {
            "route": "faq_matcher",
            "entry_point": "faq",
            "faq_id": None,
            "score": 0.0,
            "scope": "none",
        }

    def _node_free_text_parser(self, state: ConversationState) -> None:
        state["entry_point"] = "other"
        if state["normalized_message"] in {"otros", "otra consulta", "texto libre"}:
            state["assistant_message"] = "Describe el problema con tus palabras para analizarlo en la via Otros."
            state["confidence"] = 0.2
            state["decision_output"] = {
                "route": "free_text_parser",
                "entry_point": "other",
                "result": "awaiting_free_text",
            }
            return

        parsed = self._parse_free_text(state["user_message"])
        if parsed.symptom_category:
            state["state_updates"]["current_symptom"] = parsed.symptom_category

        if not state["model"]:
            state["assistant_message"] = "Describe el problema con mas detalle para analizarlo en la via Otros."
            state["confidence"] = 0.2
            state["decision_output"] = {
                "route": "free_text_parser",
                "entry_point": "other",
                "result": "model_missing",
                "tags": parsed.tags,
                "symptom_category": parsed.symptom_category,
                "reasoning_short": parsed.reasoning_short,
                "parser_source": parsed.parser_source,
            }
            return

        query_text = state["user_message"]
        query_embedding = self._embed_text(parsed.normalized_text or query_text)
        candidates = self._hybrid_search(
            query_embedding=query_embedding,
            query_text=query_text,
            model=state["model"],
            symptom=parsed.symptom_category,
            limit=12,
        )
        preferred = [candidate for candidate in candidates if candidate.source_type == "historical_case"]
        ranked = self._rank_hypotheses(preferred or candidates, 3)

        if ranked:
            primary = ranked[0].diagnosis
            alternatives = ", ".join(h.diagnosis for h in ranked[1:]) or "sin alternativas"
            sources = [
                {"source_type": c.source_type, "source_id": c.source_id}
                for c in (preferred or candidates)[:3]
            ]
            state["assistant_message"] = (
                f"Hipotesis principal: {primary}. Alternativas: {alternatives}. "
                "Si quieres, te guio por comprobaciones paso a paso."
            )
            state["confidence"] = max(0.0, min(ranked[0].score, 1.0))
            state["decision_output"] = {
                "route": "free_text_parser",
                "entry_point": "other",
                "top_hypotheses": [h.diagnosis for h in ranked],
                "top_score": ranked[0].score,
                "tags": parsed.tags,
                "symptom_category": parsed.symptom_category,
                "reasoning_short": parsed.reasoning_short,
                "parser_source": parsed.parser_source,
                "sources": sources,
            }
            return

        state["assistant_message"] = "Describe el problema con mas detalle para analizarlo en la via Otros."
        state["confidence"] = 0.2
        state["decision_output"] = {
            "route": "free_text_parser",
            "entry_point": "other",
            "result": "no_candidates",
            "tags": parsed.tags,
            "symptom_category": parsed.symptom_category,
            "reasoning_short": parsed.reasoning_short,
            "parser_source": parsed.parser_source,
        }

    @staticmethod
    def _node_menu_selection(state: ConversationState) -> None:
        state["assistant_message"] = "Selecciona una opcion valida: Sintomas frecuentes, Consultas frecuentes u Otros."
        state["confidence"] = 0.6
        state["decision_output"] = {"route": "menu_selection", "entry_point": state["entry_point"]}
