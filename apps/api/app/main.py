import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import health, metrics, session
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.infrastructure.db.sync_connection import close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="POC Asistente Conversacional de Diagnostico por Bastidor",
        lifespan=lifespan,
    )
    allowed_origins = [origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(session.router, prefix=settings.api_prefix, tags=["session"])
    app.include_router(metrics.router, prefix=settings.api_prefix, tags=["metrics"])

    # ── Vehicle photos (static files) ──────────────────────────
    photos_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "vehicle_photos")
    photos_dir = os.path.normpath(photos_dir)
    if os.path.isdir(photos_dir):
        app.mount(f"{settings.api_prefix}/photos", StaticFiles(directory=photos_dir), name="vehicle_photos")

    return app


app = create_app()
