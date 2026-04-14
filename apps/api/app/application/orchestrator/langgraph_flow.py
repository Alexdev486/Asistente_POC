from dataclasses import dataclass
from typing import Literal


Route = Literal[
    "vin_lookup",
    "menu_selection",
    "faq_matcher",
    "tree_engine",
    "free_text_parser",
    "out_of_scope",
]


@dataclass
class ConversationSnapshot:
    vin: str | None
    model: str | None
    entry_point: str | None
    current_symptom: str | None


class ConversationRouter:
    def route_turn(self, snapshot: ConversationSnapshot, user_message: str) -> Route:
        msg = user_message.strip().lower()
        if not snapshot.vin:
            return "vin_lookup"

        if msg in {"sintomas frecuentes", "sintoma", "sintomas"}:
            return "tree_engine"
        if msg in {"consultas frecuentes", "faq", "faqs"}:
            return "faq_matcher"
        if msg in {"otros", "otra consulta", "texto libre"}:
            return "free_text_parser"

        if snapshot.entry_point == "faq":
            return "faq_matcher"
        if snapshot.entry_point == "tree":
            return "tree_engine"
        if snapshot.entry_point == "other":
            return "free_text_parser"

        return "menu_selection"

