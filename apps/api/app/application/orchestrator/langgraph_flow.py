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
    asked_questions: list[str]


class ConversationState(TypedDict):
    user_message: str
    normalized_message: str
    vin: str | None
    model: str | None
    entry_point: EntryPoint | None
    current_symptom: str | None
    current_node: str | None
    asked_questions: list[str]
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
            "asked_questions": list(snapshot.asked_questions),
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
        elif state["route"] == "out_of_scope":
            self._node_out_of_scope(state)
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
        
        # Normalize menu command
        normalized_cmd = ConversationGraph._normalize_menu_command(msg)
        
        if not state["vin"]:
            return "vin_lookup"

        if normalized_cmd == "tree":
            return "tree_engine"
        if normalized_cmd == "faq":
            return "faq_matcher"
        if normalized_cmd == "other":
            return "free_text_parser"

        if state["entry_point"] == "faq":
            return "faq_matcher"
        if state["entry_point"] == "tree":
            return "tree_engine"
        if state["entry_point"] == "other":
            return "free_text_parser"

        if not state["entry_point"] and msg:
            return "free_text_parser"

        return "out_of_scope"

    @staticmethod
    def _normalize_menu_command(msg: str) -> str | None:
        """Normalize menu commands, handling typos and variations."""
        msg = msg.strip().lower()
        # Tree command variants
        tree_variants = {"sintomas frecuentes", "sintoma", "sintomas", "arbol", "symptom", "symptoms"}
        if msg in tree_variants or "sintom" in msg[:6]:
            return "tree"
        # FAQ command variants
        faq_variants = {"consultas frecuentes", "faq", "faqs", "preguntas", "consulta"}
        if msg in faq_variants or "faq" in msg or "consulta" in msg:
            return "faq"
        # Other command variants
        other_variants = {"otros", "otra consulta", "texto libre", "otro", "libre", "custom"}
        if msg in other_variants or "otro" in msg or "libre" in msg:
            return "other"
        return None

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
        normalized_cmd = self._normalize_menu_command(state["normalized_message"])
        
        if state["current_node"] or state["current_symptom"]:
            if normalized_cmd in ("faq", "other"):
                state["state_updates"]["current_node"] = None
                state["state_updates"]["current_symptom"] = None
        
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
                    "answered_node": state["current_node"],
                    "answer": state["user_message"],
                }
                return

            if step.node_type == "question":
                node_answers = tree_json["nodes"][step.node_id].get("answers", {})
                options = ", ".join(node_answers.keys()) if node_answers else "si/no"
                question_key = self._question_key(state["current_symptom"], step.node_id)
                if question_key in state["asked_questions"] or step.node_id in state["asked_questions"]:
                    state["assistant_message"] = (
                        "Ya hemos cubierto esa pregunta. "
                        "Si quieres, elige otro sintoma o cambia a FAQ/Otros."
                    )
                    state["confidence"] = 0.4
                    state["state_updates"]["current_node"] = None
                    state["state_updates"]["current_symptom"] = None
                    state["decision_output"] = {
                        "route": "tree_engine",
                        "entry_point": "tree",
                        "result": "question_repeated",
                        "current_symptom": state["current_symptom"],
                        "current_node": step.node_id,
                    }
                    return
                state["assistant_message"] = f"{step.question} (Opciones: {options})"
                state["confidence"] = 0.92
                state["state_updates"]["current_node"] = step.node_id
                state["decision_output"] = {
                    "route": "tree_engine",
                    "entry_point": "tree",
                    "result": "question",
                    "current_symptom": state["current_symptom"],
                    "current_node": step.node_id,
                    "answered_node": state["current_node"],
                    "answer": state["user_message"],
                }
                return

            diagnostic_output = self._build_diagnostic_output(
                primary=step.diagnosis,
                alternatives=[],
                next_check=f"Revisar el componente asociado: {step.diagnosis}.",
                short_explanation="Resultado del arbol de diagnostico.",
                confidence=0.97,
            )
            state["assistant_message"] = (
                f"Diagnostico probable (arbol): {step.diagnosis}. "
                "¿Te ha sido util este resultado? Puedes responder desde feedback."
            )
            state["confidence"] = 0.97
            state["state_updates"]["current_node"] = None
            state["state_updates"]["current_symptom"] = None
            state["decision_output"] = {
                "route": "tree_engine",
                "entry_point": "tree",
                "result": "diagnosis",
                "current_symptom": state["current_symptom"],
                "diagnosis": step.diagnosis,
                "diagnostic_output": diagnostic_output,
                "answered_node": state["current_node"],
                "answer": state["user_message"],
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
            question_key = self._question_key(selected_symptom, step.node_id)
            if question_key in state["asked_questions"] or step.node_id in state["asked_questions"]:
                state["assistant_message"] = (
                    "Ya hemos cubierto esa pregunta. "
                    "Elige otro sintoma o cambia a FAQ/Otros."
                )
                state["confidence"] = 0.4
                state["state_updates"]["current_node"] = None
                state["state_updates"]["current_symptom"] = None
                state["decision_output"] = {
                    "route": "tree_engine",
                    "entry_point": "tree",
                    "result": "question_repeated",
                    "current_symptom": selected_symptom,
                    "current_node": step.node_id,
                }
                return
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

        diagnostic_output = self._build_diagnostic_output(
            primary=step.diagnosis,
            alternatives=[],
            next_check=f"Revisar el componente asociado: {step.diagnosis}.",
            short_explanation="Resultado del arbol de diagnostico.",
            confidence=0.97,
        )
        state["assistant_message"] = (
            f"Diagnostico probable (arbol): {step.diagnosis}. "
            "¿Te ha sido util este resultado? Puedes responder desde feedback."
        )
        state["confidence"] = 0.97
        state["state_updates"]["current_node"] = None
        state["state_updates"]["current_symptom"] = None
        state["decision_output"] = {
            "route": "tree_engine",
            "entry_point": "tree",
            "result": "diagnosis",
            "current_symptom": selected_symptom,
            "diagnosis": step.diagnosis,
            "diagnostic_output": diagnostic_output,
        }

    def _node_faq_matcher(self, state: ConversationState) -> None:
        state["entry_point"] = "faq"
        normalized_cmd = self._normalize_menu_command(state["normalized_message"])
        
        if state["current_node"] or state["current_symptom"]:
            if normalized_cmd in ("tree", "other"):
                state["state_updates"]["current_node"] = None
                state["state_updates"]["current_symptom"] = None
        
        faqs = self._list_active_faqs(state["model"])
        if state["normalized_message"] in {"consultas frecuentes", "faq", "faqs"}:
            suggested_list = [item.question for item in faqs[:3]]
            suggested = ", ".join(suggested_list) if suggested_list else "sin FAQs activas"
            state["assistant_message"] = (
                "Vamos por Consultas frecuentes. "
                f"Puedes escribir una pregunta como: {suggested}."
            )
            state["confidence"] = 0.6
            state["decision_output"] = {
                "route": "faq_matcher",
                "entry_point": "faq",
                "result": "faq_suggestions",
                "suggestions": suggested_list,
            }
            return
        match = self._faq_match(state["model"] or "", state["user_message"], faqs)

        if match:
            diagnostic_output = self._build_diagnostic_output(
                primary=match.item.answer,
                alternatives=[],
                next_check="Aplicar la recomendacion de la FAQ y validar el resultado.",
                short_explanation=f"FAQ: {match.item.question}",
                confidence=max(0.25, min(match.score, 1.0)),
            )
            state["assistant_message"] = (
                f"FAQ encontrada: {match.item.answer} "
                "¿Te ha sido util este resultado? Puedes responder desde feedback."
            )
            state["confidence"] = max(0.25, min(match.score, 1.0))
            state["decision_output"] = {
                "route": "faq_matcher",
                "entry_point": "faq",
                "faq_id": match.item.faq_id,
                "score": match.score,
                "scope": match.scope,
                "diagnostic_output": diagnostic_output,
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
        normalized_cmd = self._normalize_menu_command(state["normalized_message"])
        
        if state["current_node"] or state["current_symptom"]:
            if normalized_cmd in ("tree", "faq"):
                state["state_updates"]["current_node"] = None
                state["state_updates"]["current_symptom"] = None
        
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
        # Guardrails: filter out weak candidates (vector similarity too low)
        min_score_threshold = 0.25
        filtered_candidates = [
            c for c in candidates
            if c.vector_score >= min_score_threshold or c.lexical_score >= min_score_threshold
        ]
        
        preferred = [candidate for candidate in filtered_candidates if candidate.source_type == "historical_case"]
        if not preferred:
            faqs = self._list_active_faqs(state["model"])
            match = self._faq_match(state["model"] or "", state["user_message"], faqs)
            if match:
                diagnostic_output = self._build_diagnostic_output(
                    primary=match.item.answer,
                    alternatives=[],
                    next_check="Aplicar la recomendacion de la FAQ y validar el resultado.",
                    short_explanation=f"FAQ: {match.item.question}",
                    confidence=max(0.25, min(match.score, 1.0)),
                )
                state["assistant_message"] = (
                    f"FAQ encontrada: {match.item.answer} "
                    "¿Te ha sido util este resultado? Puedes responder desde feedback."
                )
                state["confidence"] = max(0.25, min(match.score, 1.0))
                state["decision_output"] = {
                    "route": "free_text_parser",
                    "entry_point": "other",
                    "result": "faq_fallback",
                    "faq_id": match.item.faq_id,
                    "score": match.score,
                    "scope": match.scope,
                    "tags": parsed.tags,
                    "symptom_category": parsed.symptom_category,
                    "reasoning_short": parsed.reasoning_short,
                    "parser_source": parsed.parser_source,
                    "diagnostic_output": diagnostic_output,
                }
                return
        ranked = self._rank_hypotheses(preferred or filtered_candidates, 3)

        # Guardrails: require minimum confidence and sufficient evidence
        min_confidence_threshold = 0.35
        if ranked and ranked[0].score >= min_confidence_threshold:
            primary = ranked[0].diagnosis
            alternatives = ", ".join(h.diagnosis for h in ranked[1:]) or "sin alternativas"
            sources = [
                {"source_type": c.source_type, "source_id": c.source_id}
                for c in (preferred or filtered_candidates)[:3]
            ]
            diagnostic_output = self._build_diagnostic_output(
                primary=primary,
                alternatives=[h.diagnosis for h in ranked[1:]],
                next_check=f"Verificar hipotesis principal: {primary}.",
                short_explanation=parsed.reasoning_short,
                confidence=max(0.0, min(ranked[0].score, 1.0)),
            )
            state["assistant_message"] = (
                f"Hipotesis principal: {primary}. Alternativas: {alternatives}. "
                "¿Te ha sido util este resultado? Puedes responder desde feedback."
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
                "diagnostic_output": diagnostic_output,
            }
            return

        # Guardrail: insufficient confidence
        has_candidates = len(candidates) > 0
        has_category = parsed.symptom_category is not None
        
        if has_candidates and has_category and ranked:
            # Weak match but has category
            reason = f"Confianza baja ({ranked[0].score:.2f}) para la categoria '{parsed.symptom_category}'."
        elif has_candidates and not has_category:
            # Candidates but no clear category
            reason = "No pude clasificar el sintoma en un arbol conocido."
        else:
            reason = "No hay casos similares en la base de datos para este sintoma."

        state["assistant_message"] = (
            f"No tengo suficientes casos para darte una hipotesis fiable. {reason} "
            "Prueba a dar mas detalles o vuelve al menu para usar FAQ/Arbol."
        )
        state["confidence"] = 0.2
        state["decision_output"] = {
            "route": "free_text_parser",
            "entry_point": "other",
            "result": "weak_evidence",
            "tags": parsed.tags,
            "symptom_category": parsed.symptom_category,
            "reasoning_short": parsed.reasoning_short,
            "parser_source": parsed.parser_source,
            "threshold": min_confidence_threshold,
            "top_score": ranked[0].score if ranked else 0.0,
            "reason": reason,
        }

    @staticmethod
    def _node_menu_selection(state: ConversationState) -> None:
        state["assistant_message"] = "Selecciona una opcion valida: Sintomas frecuentes, Consultas frecuentes u Otros."
        state["confidence"] = 0.6
        state["decision_output"] = {"route": "menu_selection", "entry_point": state["entry_point"]}

    @staticmethod
    def _node_out_of_scope(state: ConversationState) -> None:
        state["assistant_message"] = (
            "Esa consulta esta fuera del alcance de la POC. "
            "Selecciona: Sintomas frecuentes, Consultas frecuentes u Otros."
        )
        state["confidence"] = 0.2
        state["decision_output"] = {"route": "out_of_scope", "entry_point": state["entry_point"]}

    @staticmethod
    def _build_diagnostic_output(
        *,
        primary: str,
        alternatives: list[str],
        next_check: str,
        short_explanation: str,
        confidence: float,
    ) -> dict[str, Any]:
        return {
            "primary_hypothesis": primary,
            "alternatives": alternatives,
            "next_check": next_check,
            "short_explanation": short_explanation,
            "confidence": max(0.0, min(confidence, 1.0)),
        }

    @staticmethod
    def _question_key(symptom: str | None, node_id: str) -> str:
        if symptom:
            return f"{symptom}:{node_id}"
        return node_id
