from uuid import UUID

from app.infrastructure.db.sync_connection import db_connection


class MessageRepository:
    def save_message(self, session_id: UUID, role: str, content: str) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages (session_id, role, content)
                VALUES (%s, %s, %s)
                """,
                (str(session_id), role, content),
            )
