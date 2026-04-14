from dataclasses import dataclass
from typing import Iterable


@dataclass
class FAQItem:
    faq_id: int
    model: str | None
    category: str
    question: str
    answer: str


@dataclass
class FAQMatch:
    item: FAQItem
    score: float


class FAQMatcherService:
    def match(self, model: str, query: str, faqs: Iterable[FAQItem]) -> FAQMatch | None:
        tokens = set(self._tokenize(query))
        best: FAQMatch | None = None
        for faq in faqs:
            if faq.model and faq.model != model:
                continue
            score = self._overlap_score(tokens, set(self._tokenize(faq.question)))
            if best is None or score > best.score:
                best = FAQMatch(item=faq, score=score)
        if best and best.score >= 0.25:
            return best
        return None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token for token in text.lower().replace("?", " ").split() if token]

    @staticmethod
    def _overlap_score(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a.intersection(b)) / max(len(a), 1)

