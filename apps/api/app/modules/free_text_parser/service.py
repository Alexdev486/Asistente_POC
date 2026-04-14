from dataclasses import dataclass


@dataclass
class ParsedFreeText:
    normalized_text: str
    tags: list[str]
    symptom_category: str | None


class FreeTextParserService:
    def parse(self, text: str) -> ParsedFreeText:
        normalized = " ".join(text.lower().replace(",", " ").replace(".", " ").split())
        tags = self._infer_tags(normalized)
        symptom_category = self._infer_category(tags)
        return ParsedFreeText(
            normalized_text=normalized,
            tags=tags,
            symptom_category=symptom_category,
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

