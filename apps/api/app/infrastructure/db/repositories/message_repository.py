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

    def get_session_messages(self, session_id: UUID) -> list[dict]:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_id, role, content, created_at
                FROM messages
                WHERE session_id = %s
                ORDER BY message_id ASC
                """,
                (str(session_id),),
            )
            return [
                {
                    "message_id": row[0],
                    "role": row[1],
                    "content": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                }
                for row in cur.fetchall()
            ]
