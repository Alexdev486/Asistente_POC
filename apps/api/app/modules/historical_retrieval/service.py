"""
Shared data types for retrieval and ranking.

HistoricalCase — represents a historical diagnosis case from the database.
RetrievalCandidate — represents a candidate retrieved for ranking.
"""
from dataclasses import dataclass


@dataclass
class HistoricalCase:
    case_id: str
    model: str
    case_text: str
    final_diagnosis: str
    base_confidence: float
    frequency: int = 1


@dataclass
class RetrievalCandidate:
    case_id: str
    diagnosis: str
    vector_score: float
    lexical_score: float
    model_match: float
    base_confidence: float
    frequency: int
    source_type: str | None = None
    source_id: str | None = None
    text_chunk: str | None = None
