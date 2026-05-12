from uuid import UUID

from app.infrastructure.db.sync_connection import db_connection


class FeedbackRepository:
    def save_feedback(self, session_id: UUID, useful: bool, comment: str | None) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback (session_id, useful, comment)
                VALUES (%s, %s, %s)
                ON CONFLICT (session_id)
                DO UPDATE SET useful = EXCLUDED.useful, comment = EXCLUDED.comment
                """,
                (str(session_id), useful, comment),
            )
