from fastapi import APIRouter

from app.infrastructure.db.repositories import MetricsRepository
from app.schemas.responses import MetricsSummaryResponse

router = APIRouter()
metrics_repository = MetricsRepository()


@router.get("/metrics/summary", response_model=MetricsSummaryResponse)
def metrics_summary() -> MetricsSummaryResponse:
    return metrics_repository.get_summary()
