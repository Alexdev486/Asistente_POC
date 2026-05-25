from app.modules.historical_retrieval.service import RetrievalCandidate
from app.modules.hybrid_ranking.service import HybridRankingService


def test_hybrid_ranking_orders_by_score() -> None:
    service = HybridRankingService()
    candidates = [
        RetrievalCandidate(
            case_id="C1",
            diagnosis="Caso 1",
            vector_score=0.1,
            lexical_score=0.1,
            model_match=1.0,
            base_confidence=0.5,
            frequency=1,
        ),
        RetrievalCandidate(
            case_id="C2",
            diagnosis="Caso 2",
            vector_score=0.9,
            lexical_score=0.2,
            model_match=1.0,
            base_confidence=0.7,
            frequency=1,
        ),
    ]

    ranked = service.rank(candidates, top_k=2)

    assert ranked[0].source_case_id == "C2"
    assert ranked[0].score > ranked[1].score
