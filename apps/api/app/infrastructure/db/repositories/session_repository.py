from dataclasses import dataclass
from typing import Any
from uuid import UUID

from psycopg2.extras import RealDictCursor

from app.infrastructure.db.sync_connection import db_connection
from app.schemas.responses import SessionStateResponse


@dataclass
class PersistedSession:
    session_id: UUID
    status: str
    entry_point: str | None
    steps: int
    state: SessionStateResponse
    state_json: dict[str, Any]


class SessionRepository:
    def create_session(self, session_id: UUID, state_json: dict[str, Any]) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (session_id, status, total_steps)
                VALUES (%s, 'active', 0)
                """,
                (str(session_id),),
            )
            cur.execute(
                """
                INSERT INTO session_state (session_id, state_json)
                VALUES (%s, %s::jsonb)
                """,
                (str(session_id), self._dumps_json(state_json)),
            )

    def get_session(self, session_id: UUID) -> PersistedSession | None:
        with db_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    s.session_id,
                    s.status,
                    s.entry_point,
                    s.total_steps,
                    ss.vin,
                    ss.model,
                    ss.current_symptom,
                    ss.current_node,
                    ss.state_json
                FROM sessions s
                JOIN session_state ss ON ss.session_id = s.session_id
                WHERE s.session_id = %s
                """,
                (str(session_id),),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return PersistedSession(
            session_id=row["session_id"],
            status=row["status"],
            entry_point=row["entry_point"],
            steps=row["total_steps"],
            state=SessionStateResponse(
                vin=row["vin"],
                model=row["model"],
                current_symptom=row["current_symptom"],
                current_node=row["current_node"],
            ),
            state_json=row["state_json"] or {},
        )

    def save_turn(
        self,
        session_id: UUID,
        *,
        steps: int,
        entry_point: str | None,
        state: SessionStateResponse,
        state_json: dict[str, Any],
    ) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET total_steps = %s,
                    entry_point = %s,
                    vin = %s,
                    model = %s
                WHERE session_id = %s
                """,
                (steps, entry_point, state.vin, state.model, str(session_id)),
            )
            cur.execute(
                """
                UPDATE session_state
                SET vin = %s,
                    model = %s,
                    current_symptom = %s,
                    current_node = %s,
                    state_json = %s::jsonb
                WHERE session_id = %s
                """,
                (
                    state.vin,
                    state.model,
                    state.current_symptom,
                    state.current_node,
                    self._dumps_json(state_json),
                    str(session_id),
                ),
            )

    def complete_session(self, session_id: UUID) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET status = 'completed',
                    ended_at = NOW()
                WHERE session_id = %s
                """,
                (str(session_id),),
            )
            if cur.rowcount == 0:
                raise KeyError(f"Sesion no encontrada: {session_id}")

    def set_final_result(self, session_id: UUID, final_result: str) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET final_result = %s
                WHERE session_id = %s
                """,
                (final_result, str(session_id)),
            )

    @staticmethod
    def _dumps_json(data: dict[str, Any]) -> str:
        import json

        return json.dumps(data, ensure_ascii=True)
