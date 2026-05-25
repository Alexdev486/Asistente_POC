from psycopg2.extras import RealDictCursor

from app.infrastructure.db.sync_connection import db_connection
from app.schemas.responses import MetricsSummaryResponse


class MetricsRepository:
    def get_summary(self) -> MetricsSummaryResponse:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    total_sessions,
                    completed_sessions,
                    avg_steps_per_session,
                    avg_session_seconds,
                    faq_usage,
                    tree_usage,
                    other_usage,
                    positive_feedback,
                    negative_feedback,
                    most_frequent_final_result
                FROM v_metrics_summary
                """
            )
            row = cur.fetchone()
        if row is None:
            return MetricsSummaryResponse(
                total_sessions=0,
                completed_sessions=0,
                avg_steps_per_session=0.0,
                avg_session_seconds=0.0,
                faq_usage=0,
                tree_usage=0,
                other_usage=0,
                positive_feedback=0,
                negative_feedback=0,
                most_frequent_final_result=None,
            )
        return MetricsSummaryResponse(
            total_sessions=row["total_sessions"],
            completed_sessions=row["completed_sessions"],
            avg_steps_per_session=float(row["avg_steps_per_session"]),
            avg_session_seconds=float(row["avg_session_seconds"]),
            faq_usage=row["faq_usage"],
            tree_usage=row["tree_usage"],
            other_usage=row["other_usage"],
            positive_feedback=row["positive_feedback"],
            negative_feedback=row["negative_feedback"],
            most_frequent_final_result=row["most_frequent_final_result"],
        )
