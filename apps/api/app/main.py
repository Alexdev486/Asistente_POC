from fastapi import FastAPI

from app.api.v1.endpoints import health, metrics, session
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="POC Asistente Conversacional de Diagnostico por Bastidor",
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(session.router, prefix=settings.api_prefix, tags=["session"])
    app.include_router(metrics.router, prefix=settings.api_prefix, tags=["metrics"])
    return app


app = create_app()

