from app.infrastructure.db.sync_connection import db_connection
from app.infrastructure.db.repositories.knowledge_repository import KnowledgeRepository
from app.infrastructure.retrieval.embeddings import EmbeddingService


def test_repository_reads_seeded_data() -> None:
    repo = KnowledgeRepository()
    vehicle = repo.get_vehicle_by_vin("AK550-POC-0001")

    assert vehicle is not None
    assert vehicle.model == "AK550"

    faqs = repo.list_active_faqs("AK550")
    assert len(faqs) >= 1

    symptoms = repo.list_active_tree_symptoms("AK550")
    assert "Paradas de motor" in symptoms


def test_hybrid_search_returns_candidates() -> None:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM knowledge_chunks WHERE embedding_status = 'ready'")
        ready_count = cur.fetchone()[0]
    assert ready_count > 0

    repo = KnowledgeRepository()
    embedder = EmbeddingService()
    candidates = repo.search_hybrid(
        query_embedding=embedder.embed("paradas en caliente"),
        query_text="paradas en caliente",
        model="AK550",
        symptom="Paradas de motor",
        limit=5,
    )

    assert len(candidates) >= 1
