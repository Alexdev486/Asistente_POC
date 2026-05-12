from psycopg2.extras import RealDictCursor

from app.infrastructure.db.sync_connection import db_connection
from app.modules.faq_matcher.service import FAQItem
from app.modules.historical_retrieval.service import HistoricalCase
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
