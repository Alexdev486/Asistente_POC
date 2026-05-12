#!/usr/bin/env python3
from __future__ import annotations

from app.infrastructure.db.sync_connection import db_connection
from app.infrastructure.retrieval.embeddings import EmbeddingService


def _to_vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in values) + "]"


def enqueue_pending_jobs() -> int:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO embedding_jobs (chunk_id, provider, model, status)
            SELECT
                kc.chunk_id,
                kc.embedding_provider,
                kc.embedding_model,
                'pending'
            FROM knowledge_chunks kc
            WHERE kc.embedding_status IN ('pending', 'failed')
            ON CONFLICT (chunk_id, provider, model) DO NOTHING
            """
        )
        return cur.rowcount


def claim_next_job() -> dict | None:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH next_job AS (
                SELECT ej.job_id
                FROM embedding_jobs ej
                WHERE ej.status = 'pending'
                ORDER BY ej.created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE embedding_jobs ej
            SET status = 'in_progress',
                attempts = attempts + 1
            FROM next_job
            WHERE ej.job_id = next_job.job_id
            RETURNING ej.job_id, ej.chunk_id, ej.provider, ej.model
            """
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "job_id": row[0],
            "chunk_id": row[1],
            "provider": row[2],
            "model": row[3],
        }


def get_chunk_text(chunk_id: int) -> str:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT text_chunk FROM knowledge_chunks WHERE chunk_id = %s",
            (chunk_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Chunk no encontrado: {chunk_id}")
        return row[0]


def mark_done(job_id: int, chunk_id: int, provider: str, model: str, embedding: list[float]) -> None:
    vector_literal = _to_vector_literal(embedding)
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE knowledge_chunks
            SET embedding = %s::vector,
                embedding_status = 'ready',
                embedding_provider = %s,
                embedding_model = %s
            WHERE chunk_id = %s
            """,
            (vector_literal, provider, model, chunk_id),
        )
        cur.execute(
            """
            UPDATE embedding_jobs
            SET status = 'done',
                last_error = NULL
            WHERE job_id = %s
            """,
            (job_id,),
        )


def mark_failed(job_id: int, chunk_id: int, error: Exception) -> None:
    with db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE embedding_jobs
            SET status = 'failed',
                last_error = %s
            WHERE job_id = %s
            """,
            (str(error), job_id),
        )
        cur.execute(
            """
            UPDATE knowledge_chunks
            SET embedding_status = 'failed'
            WHERE chunk_id = %s
            """,
            (chunk_id,),
        )


def run_worker_once() -> None:
    enqueued = enqueue_pending_jobs()
    service = EmbeddingService()
    processed = 0
    failed = 0

    while True:
        job = claim_next_job()
        if job is None:
            break
        try:
            text_chunk = get_chunk_text(job["chunk_id"])
            embedding = service.embed(text_chunk)
            mark_done(
                job_id=job["job_id"],
                chunk_id=job["chunk_id"],
                provider=job["provider"],
                model=job["model"],
                embedding=embedding,
            )
            processed += 1
        except Exception as exc:
            mark_failed(job_id=job["job_id"], chunk_id=job["chunk_id"], error=exc)
            failed += 1

    print(f"embedding_jobs_enqueued={enqueued}")
    print(f"embedding_jobs_processed={processed}")
    print(f"embedding_jobs_failed={failed}")


if __name__ == "__main__":
    run_worker_once()
