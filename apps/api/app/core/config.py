from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Asistente Diagnostico POC API"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/asistente_poc"
    pgvector_dim: int = 1024

    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    request_timeout_seconds: int = Field(default=20, ge=1, le=120)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

