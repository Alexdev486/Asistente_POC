import logging
from contextlib import contextmanager
from urllib.parse import urlparse

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import connection as PGConnection

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_pool: ThreadedConnectionPool | None = None
_POOL_MIN = 1
_POOL_MAX = 10


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


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = ThreadedConnectionPool(_POOL_MIN, _POOL_MAX, get_sync_database_url())
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


@contextmanager
def db_connection() -> PGConnection:
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.error("Database error, transaction rolled back", exc_info=True)
        raise
    finally:
        pool.putconn(conn)
