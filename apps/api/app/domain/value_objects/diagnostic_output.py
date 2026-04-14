from dataclasses import dataclass


@dataclass
class DiagnosticOutput:
    primary_hypothesis: str
    alternatives: list[str]
    next_check: str
    short_explanation: str
    confidence: float

