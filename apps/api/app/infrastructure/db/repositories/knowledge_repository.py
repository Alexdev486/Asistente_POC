import re

from psycopg2.extras import RealDictCursor

from app.infrastructure.db.sync_connection import db_connection
from app.modules.faq_matcher.service import FAQItem
from app.modules.historical_retrieval.service import HistoricalCase, RetrievalCandidate
from app.modules.vin_lookup.service import VehicleInfo


class KnowledgeRepository:
    def get_vehicle_by_vin(self, vin: str) -> VehicleInfo | None:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT vin, model, family, model_year, market
                FROM vehicles
                WHERE vin = %s
                """,
                (vin,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return VehicleInfo(
            vin=row["vin"],
            model=row["model"],
            family=row["family"] or "",
            model_year=row["model_year"] or 0,
            market=row["market"] or "",
        )

    def list_active_faqs(self, model: str | None) -> list[FAQItem]:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT faq_id, model, category, question, answer, usage_count
                FROM faqs
                WHERE active IS TRUE
                  AND (%s IS NULL OR model = %s OR model IS NULL)
                ORDER BY usage_count DESC, faq_id ASC
                """,
                (model, model),
            )
            rows = cur.fetchall()
        return [
            FAQItem(
                faq_id=row["faq_id"],
                model=row["model"],
                category=row["category"] or "General",
                question=row["question"],
                answer=row["answer"],
                usage_count=row["usage_count"] or 0,
            )
            for row in rows
        ]

    def list_active_tree_symptoms(self, model: str | None) -> list[str]:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT symptom
                FROM diagnostic_trees
                WHERE active IS TRUE
                  AND (%s IS NULL OR model = %s OR model IS NULL)
                ORDER BY symptom ASC
                """,
                (model, model),
            )
            rows = cur.fetchall()
        return [row[0] for row in rows]

    def list_historical_cases(self, model: str) -> list[HistoricalCase]:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT case_id, model, case_text, final_diagnosis, base_confidence
                FROM historical_cases
                WHERE model = %s
                ORDER BY case_id ASC
                """,
                (model,),
            )
            rows = cur.fetchall()
        return [
            HistoricalCase(
                case_id=row["case_id"],
                model=row["model"],
                case_text=row["case_text"],
                final_diagnosis=row["final_diagnosis"],
                base_confidence=float(row["base_confidence"]),
                frequency=1,
            )
            for row in rows
        ]

    def get_active_tree_by_symptom(self, model: str | None, symptom: str) -> dict | None:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT tree_json
                FROM diagnostic_trees
                WHERE active IS TRUE
                  AND LOWER(symptom) = LOWER(%s)
                  AND (%s IS NULL OR model = %s OR model IS NULL)
                ORDER BY CASE WHEN model = %s THEN 0 ELSE 1 END, version DESC
                LIMIT 1
                """,
                (symptom, model, model, model),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return row["tree_json"]

    def search_hybrid(
        self,
        *,
        query_embedding: list[float],
        query_text: str,
        model: str | None,
        symptom: str | None,
        limit: int = 10,
    ) -> list[RetrievalCandidate]:
        vector_literal = self._to_vector_literal(query_embedding)
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    hs.chunk_id,
                    hs.source_type,
                    hs.source_id,
                    hs.model,
                    hs.symptom_category,
                    hs.text_chunk,
                    hs.vector_score,
                    hs.lexical_score,
                    hs.hybrid_score,
                    kc.base_confidence
                FROM hybrid_search(%s::vector, %s, %s, %s, %s) AS hs
                JOIN knowledge_chunks kc ON kc.chunk_id = hs.chunk_id
                """,
                (vector_literal, query_text, model, symptom, limit),
            )
            rows = cur.fetchall()

        candidates: list[RetrievalCandidate] = []
        for row in rows:
            diagnosis = self._extract_diagnosis(row["source_type"], row["text_chunk"])
            base_confidence = float(row["base_confidence"]) if row["base_confidence"] is not None else 0.5
            if model is None or row["model"] is None or row["model"] == model:
                model_match = 1.0
            else:
                model_match = 0.8
            candidates.append(
                RetrievalCandidate(
                    case_id=str(row["chunk_id"]),
                    diagnosis=diagnosis,
                    vector_score=float(row["vector_score"] or 0.0),
                    lexical_score=float(row["lexical_score"] or 0.0),
                    model_match=model_match,
                    base_confidence=base_confidence,
                    frequency=1,
                    source_type=row["source_type"],
                    source_id=row["source_id"],
                    text_chunk=row["text_chunk"],
                )
            )
        return candidates

    @staticmethod
    def _to_vector_literal(values: list[float]) -> str:
        return "[" + ",".join(f"{value:.6f}" for value in values) + "]"

    @staticmethod
    def _extract_diagnosis(source_type: str | None, text_chunk: str) -> str:
        if source_type == "historical_case":
            match = re.search(r"Diagnostico final:\s*(.+)", text_chunk, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        if source_type == "tree_node":
            match = re.search(r"\]:\s*(.+)", text_chunk)
            if match:
                return match.group(1).strip()
        if source_type == "faq":
            match = re.search(r"FAQ:\s*(.+)", text_chunk, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return text_chunk.strip()[:160]
