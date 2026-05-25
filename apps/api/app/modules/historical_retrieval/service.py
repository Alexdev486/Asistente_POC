from dataclasses import dataclass
from typing import Iterable


@dataclass
class HistoricalCase:
    case_id: str
    model: str
    case_text: str
    final_diagnosis: str
    base_confidence: float
    frequency: int = 1


@dataclass
class RetrievalCandidate:
    case_id: str
    diagnosis: str
    vector_score: float
    lexical_score: float
    model_match: float
    base_confidence: float
    frequency: int
    source_type: str | None = None
    source_id: str | None = None
    text_chunk: str | None = None


class HistoricalRetrievalService:
    def retrieve(
        self,
        model: str,
        normalized_query: str,
        cases: Iterable[HistoricalCase],
    ) -> list[RetrievalCandidate]:
        tokens = set(normalized_query.split())
        candidates: list[RetrievalCandidate] = []
        for case in cases:
            if case.model != model:
                continue
            lexical = self._lexical_similarity(tokens, set(case.case_text.lower().split()))
            # Placeholder de similitud vectorial hasta conectar embeddings/pgvector.
            vector = lexical
            candidates.append(
                RetrievalCandidate(
                    case_id=case.case_id,
                    diagnosis=case.final_diagnosis,
                    vector_score=vector,
                    lexical_score=lexical,
                    model_match=1.0,
                    base_confidence=case.base_confidence,
                    frequency=case.frequency,
                    source_type="historical_case",
                    source_id=case.case_id,
                    text_chunk=case.case_text,
                )
            )
        return candidates

    @staticmethod
    def _lexical_similarity(query_tokens: set[str], case_tokens: set[str]) -> float:
        if not query_tokens:
            return 0.0
        return len(query_tokens.intersection(case_tokens)) / len(query_tokens)
