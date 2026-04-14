from dataclasses import dataclass

from app.modules.historical_retrieval.service import RetrievalCandidate


@dataclass
class RankedHypothesis:
    diagnosis: str
    score: float
    source_case_id: str


class HybridRankingService:
    """
    Formula base en la POC:
    0.55 * vector_sim + 0.20 * lexical_sim + 0.15 * model_match + 0.10 * base_confidence
    """

    def rank(self, candidates: list[RetrievalCandidate], top_k: int = 3) -> list[RankedHypothesis]:
        ranked = [
            RankedHypothesis(
                diagnosis=c.diagnosis,
                source_case_id=c.case_id,
                score=(
                    0.55 * c.vector_score
                    + 0.20 * c.lexical_score
                    + 0.15 * c.model_match
                    + 0.10 * c.base_confidence
                ),
            )
            for c in candidates
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

