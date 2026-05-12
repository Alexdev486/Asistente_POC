from dataclasses import dataclass
from typing import Iterable
import re
import unicodedata


@dataclass
class FAQItem:
    faq_id: int
    model: str | None
    category: str
    question: str
    answer: str
    usage_count: int = 0


@dataclass
class FAQMatch:
    item: FAQItem
    score: float
    scope: str


class FAQMatcherService:
    def match(self, model: str, query: str, faqs: Iterable[FAQItem]) -> FAQMatch | None:
        all_faqs = list(faqs)
        model_faqs = [faq for faq in all_faqs if faq.model == model]
        global_faqs = [faq for faq in all_faqs if faq.model is None]

        best_model = self._best_match(query, model_faqs, scope="model")
        if best_model and best_model.score >= 0.25:
            return best_model

        best_global = self._best_match(query, global_faqs, scope="global")
        if best_global and best_global.score >= 0.28:
            return best_global

        return None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = FAQMatcherService._normalize(text)
        stopwords = {
            "que",
            "el",
            "la",
            "los",
            "las",
            "de",
            "del",
            "en",
            "al",
            "por",
            "con",
            "y",
            "o",
            "un",
            "una",
            "unos",
            "unas",
            "se",
            "es",
            "son",
            "puede",
            "pueden",
            "significa",
            "ser",
        }
        return [token for token in normalized.split() if token and len(token) > 2 and token not in stopwords]

    @staticmethod
    def _overlap_score(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a.intersection(b)) / max(min(len(a), len(b)), 1)

    def _best_match(self, query: str, faqs: list[FAQItem], scope: str) -> FAQMatch | None:
        query_tokens = set(self._tokenize(query))
        query_norm = self._normalize(query)
        best: FAQMatch | None = None
        for faq in faqs:
            question_norm = self._normalize(faq.question)
            score = self._overlap_score(query_tokens, set(self._tokenize(faq.question)))

            if query_norm and (query_norm in question_norm or question_norm in query_norm):
                score += 0.15
            score += min(faq.usage_count / 20, 1) * 0.05

            if best is None or score > best.score:
                best = FAQMatch(item=faq, score=score, scope=scope)
        return best

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
