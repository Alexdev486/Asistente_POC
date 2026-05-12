from typing import Any
from uuid import UUID

from app.infrastructure.db.sync_connection import db_connection


class DecisionLogRepository:
    def save_log(
        self,
        *,
        session_id: UUID,
        module_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        confidence: float | None,
    ) -> None:
        with db_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO decision_logs (session_id, module_name, input_data, output_data, confidence)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s)
                """,
                (
                    str(session_id),
                    module_name,
                    self._dumps_json(input_data),
                    self._dumps_json(output_data),
                    confidence,
                ),
            )

    @staticmethod
    def _dumps_json(data: dict[str, Any]) -> str:
        import json

        return json.dumps(data, ensure_ascii=True)
