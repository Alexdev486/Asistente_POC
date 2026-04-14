from fastapi import APIRouter

from app.schemas.responses import MetricsSummaryResponse

router = APIRouter()


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def metrics_summary() -> MetricsSummaryResponse:
    return MetricsSummaryResponse(
        total_sessions=0,
        completed_sessions=0,
        avg_steps_per_session=0.0,
        faq_usage=0,
        tree_usage=0,
        other_usage=0,
        positive_feedback=0,
        negative_feedback=0,
    )

