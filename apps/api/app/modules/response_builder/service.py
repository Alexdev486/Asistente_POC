from app.domain.value_objects.diagnostic_output import DiagnosticOutput


class ResponseBuilderService:
    def build_standard_output(
        self,
        primary_hypothesis: str,
        alternatives: list[str],
        next_check: str,
        short_explanation: str,
        confidence: float,
    ) -> DiagnosticOutput:
        return DiagnosticOutput(
            primary_hypothesis=primary_hypothesis,
            alternatives=alternatives[:2],
            next_check=next_check,
            short_explanation=short_explanation,
            confidence=max(0.0, min(confidence, 1.0)),
        )

