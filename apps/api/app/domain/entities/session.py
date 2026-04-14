from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class SessionEntity:
    session_id: UUID
    status: str = "active"
    entry_point: str | None = None
    steps: int = 0
    state: dict[str, Any] = field(default_factory=dict)
    state_json: dict[str, Any] = field(default_factory=dict)

