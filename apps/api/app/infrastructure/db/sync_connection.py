from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2.extensions import connection as PGConnection

from app.core.config import get_settings


def _to_sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if database_url.startswith("postgres+asyncpg://"):
        return database_url.replace("postgres+asyncpg://", "postgresql://", 1)
    return database_url


def get_sync_database_url() -> str:
    settings = get_settings()
    sync_url = _to_sync_database_url(settings.database_url)
    parsed = urlparse(sync_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError("DATABASE_URL debe usar esquema postgresql/postgres")
    return sync_url


@contextmanager
def db_connection() -> PGConnection:
    conn = psycopg2.connect(get_sync_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
