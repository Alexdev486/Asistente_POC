from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

import httpx

from app.infrastructure.llm.gateway import LLMGateway


@dataclass
class ParsedFreeText:
    normalized_text: str
    tags: list[str]
    symptom_category: str | None
    reasoning_short: str
    parser_source: str


class FreeTextParserService:
    def __init__(self, llm_gateway: LLMGateway | None = None) -> None:
        self._llm_gateway = llm_gateway
        self._system_prompt = self._load_system_prompt()

    def parse(self, text: str) -> ParsedFreeText:
        normalized = self._normalize(text)
        if self._llm_gateway is not None:
            try:
                return self._parse_with_llm(text, normalized)
            except (RuntimeError, httpx.HTTPError, json.JSONDecodeError, ValueError):
                parsed_rules = self._parse_with_rules(normalized)
                return ParsedFreeText(
                    normalized_text=parsed_rules.normalized_text,
                    tags=parsed_rules.tags,
                    symptom_category=parsed_rules.symptom_category,
                    reasoning_short="LLM no disponible o salida invalida; se aplicaron reglas locales.",
                    parser_source="rules_fallback",
                )
        parsed_rules = self._parse_with_rules(normalized)
        return ParsedFreeText(
            normalized_text=parsed_rules.normalized_text,
            tags=parsed_rules.tags,
            symptom_category=parsed_rules.symptom_category,
            reasoning_short="Clasificacion por reglas locales.",
            parser_source="rules",
        )

    def _parse_with_llm(self, raw_text: str, normalized: str) -> ParsedFreeText:
        llm_prompt = (
            "Texto del usuario:\n"
            f"{raw_text}\n\n"
            "Devuelve exclusivamente un JSON con campos:\n"
            "{\n"
            '  "tags": ["tag1","tag2"],\n'
            '  "symptom_category": "Paradas de motor" | "Testigo CELP encendido" | null,\n'
            '  "reasoning_short": "razon breve"\n'
            "}\n"
        )
        raw = self._llm_gateway.complete(prompt=llm_prompt, system_prompt=self._system_prompt)
        data = self._extract_json(raw)
        tags_raw = data.get("tags", [])
        if not isinstance(tags_raw, list):
            raise ValueError("Campo tags no es lista")
        tags = [str(tag).strip() for tag in tags_raw if str(tag).strip()]
        symptom_category = data.get("symptom_category")
        if symptom_category is not None:
            symptom_category = str(symptom_category).strip() or None
        reasoning_short = str(data.get("reasoning_short", "")).strip() or "Clasificacion por LLM."
        return ParsedFreeText(
            normalized_text=normalized,
            tags=tags,
            symptom_category=symptom_category,
            reasoning_short=reasoning_short,
            parser_source="llm",
        )

    def _parse_with_rules(self, normalized: str) -> ParsedFreeText:
        tags = self._infer_tags(normalized)
        symptom_category = self._infer_category(tags)
        return ParsedFreeText(
            normalized_text=normalized,
            tags=tags,
            symptom_category=symptom_category,
            reasoning_short="Clasificacion por reglas locales.",
            parser_source="rules",
        )

    def _infer_tags(self, text: str) -> list[str]:
        keywords = [
            ("caliente", "hot_engine"),
            ("enfr", "cold_restart"),
            ("bomba", "fuel_pump"),
            ("celp", "celp_light"),
            ("baches", "bumps"),
            ("repost", "after_refuel"),
        ]
        tags = [tag for token, tag in keywords if token in text]
        return tags

    def _infer_category(self, tags: list[str]) -> str | None:
        if "celp_light" in tags:
            return "Testigo CELP encendido"
        if {"hot_engine", "fuel_pump", "after_refuel"} & set(tags):
            return "Paradas de motor"
        return None

    @staticmethod
    def _extract_json(raw_content: str) -> dict:
        content = raw_content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if "\n" in content:
                content = content.split("\n", 1)[1]
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No se encontro JSON en salida LLM")
        return json.loads(content[start : end + 1])

    @staticmethod
    def _load_system_prompt() -> str:
        root = Path(__file__).resolve().parents[5]
        prompt_path = root / "data" / "prompts" / "free_text_parser.system.txt"
        return prompt_path.read_text(encoding="utf-8").strip()

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r"[^a-z0-9\\s]", " ", text)
        return " ".join(text.split())
