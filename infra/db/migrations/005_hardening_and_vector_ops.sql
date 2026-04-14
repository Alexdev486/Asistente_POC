-- Core hardening constraints (idempotent via pg_constraint checks)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_faqs_usage_count_non_negative'
    ) THEN
        ALTER TABLE faqs
        ADD CONSTRAINT ck_faqs_usage_count_non_negative
        CHECK (usage_count >= 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_historical_cases_base_confidence_range'
    ) THEN
        ALTER TABLE historical_cases
        ADD CONSTRAINT ck_historical_cases_base_confidence_range
        CHECK (base_confidence >= 0 AND base_confidence <= 1);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_sessions_total_steps_non_negative'
    ) THEN
        ALTER TABLE sessions
        ADD CONSTRAINT ck_sessions_total_steps_non_negative
        CHECK (total_steps >= 0);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_sessions_status'
    ) THEN
        ALTER TABLE sessions
        ADD CONSTRAINT ck_sessions_status
        CHECK (status IN ('active', 'completed', 'abandoned', 'error'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_sessions_entry_point'
    ) THEN
        ALTER TABLE sessions
        ADD CONSTRAINT ck_sessions_entry_point
        CHECK (entry_point IS NULL OR entry_point IN ('faq', 'tree', 'other'));
    END IF;
END $$;

-- Operational indexes for read-heavy traces
CREATE INDEX IF NOT EXISTS idx_sessions_status_started_at ON sessions(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_session_created_at ON messages(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decision_logs_session_created_at ON decision_logs(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_state_vin ON session_state(vin);
CREATE INDEX IF NOT EXISTS idx_faqs_model_active ON faqs(model, active);
CREATE INDEX IF NOT EXISTS idx_diagnostic_trees_model_symptom_active ON diagnostic_trees(model, symptom, active);
CREATE INDEX IF NOT EXISTS idx_decision_logs_module_created_at ON decision_logs(module_name, created_at DESC);

-- Vector layer: async-friendly ingestion + richer metadata
ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS chunk_index INTEGER NOT NULL DEFAULT 0;

ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS embedding_provider VARCHAR(30) NOT NULL DEFAULT 'openrouter';

ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(120) NOT NULL DEFAULT 'bge-m3';

ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS embedding_status VARCHAR(20) NOT NULL DEFAULT 'pending';

ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NOT NULL DEFAULT NOW();

ALTER TABLE knowledge_chunks
ALTER COLUMN embedding DROP NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_knowledge_chunks_embedding_status'
    ) THEN
        ALTER TABLE knowledge_chunks
        ADD CONSTRAINT ck_knowledge_chunks_embedding_status
        CHECK (embedding_status IN ('pending', 'ready', 'failed'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_knowledge_chunks_base_confidence_range'
    ) THEN
        ALTER TABLE knowledge_chunks
        ADD CONSTRAINT ck_knowledge_chunks_base_confidence_range
        CHECK (
            base_confidence IS NULL
            OR (base_confidence >= 0 AND base_confidence <= 1)
        );
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_chunks_source_chunk_model
ON knowledge_chunks(source_type, source_id, chunk_index, embedding_model);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_ref
ON knowledge_chunks(source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_status
ON knowledge_chunks(embedding_status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_provider_model
ON knowledge_chunks(embedding_provider, embedding_model);

DROP INDEX IF EXISTS idx_kc_embedding_hnsw;
CREATE INDEX IF NOT EXISTS idx_kc_embedding_hnsw
ON knowledge_chunks
USING hnsw (embedding vector_cosine_ops)
WHERE embedding_status = 'ready' AND embedding IS NOT NULL;

DROP TRIGGER IF EXISTS trg_knowledge_chunks_set_updated_at ON knowledge_chunks;
CREATE TRIGGER trg_knowledge_chunks_set_updated_at
BEFORE UPDATE ON knowledge_chunks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Embedding job queue for scalable backfill/retries
CREATE TABLE IF NOT EXISTS embedding_jobs (
    job_id BIGSERIAL PRIMARY KEY,
    chunk_id BIGINT NOT NULL,
    provider VARCHAR(30) NOT NULL,
    model VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (chunk_id) REFERENCES knowledge_chunks(chunk_id) ON DELETE CASCADE,
    CONSTRAINT ck_embedding_jobs_status CHECK (status IN ('pending', 'in_progress', 'done', 'failed')),
    CONSTRAINT ck_embedding_jobs_attempts_non_negative CHECK (attempts >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_embedding_jobs_chunk_provider_model
ON embedding_jobs(chunk_id, provider, model);

CREATE INDEX IF NOT EXISTS idx_embedding_jobs_status_created_at
ON embedding_jobs(status, created_at ASC);

DROP TRIGGER IF EXISTS trg_embedding_jobs_set_updated_at ON embedding_jobs;
CREATE TRIGGER trg_embedding_jobs_set_updated_at
BEFORE UPDATE ON embedding_jobs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Weighted hybrid retrieval (model-aware with fallback to global rows)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1024),
    query_text TEXT,
    target_model VARCHAR(100),
    target_symptom VARCHAR(100),
    limit_count INTEGER DEFAULT 10,
    weight_vector DOUBLE PRECISION DEFAULT 0.75,
    weight_lexical DOUBLE PRECISION DEFAULT 0.25
)
RETURNS TABLE (
    chunk_id BIGINT,
    source_type VARCHAR(30),
    source_id VARCHAR(100),
    model VARCHAR(100),
    symptom_category VARCHAR(100),
    text_chunk TEXT,
    vector_score DOUBLE PRECISION,
    lexical_score DOUBLE PRECISION,
    hybrid_score DOUBLE PRECISION
)
LANGUAGE SQL
STABLE
AS $$
    WITH params AS (
        SELECT
            GREATEST(weight_vector, 0) AS wv,
            GREATEST(weight_lexical, 0) AS wl
    ),
    scored AS (
        SELECT
            kc.chunk_id,
            kc.source_type,
            kc.source_id,
            kc.model,
            kc.symptom_category,
            kc.text_chunk,
            (1 - (kc.embedding <=> query_embedding)) AS vector_score,
            CASE
                WHEN COALESCE(BTRIM(query_text), '') = '' THEN 0::double precision
                ELSE ts_rank_cd(kc.lexical, websearch_to_tsquery('spanish', query_text))
            END AS lexical_score
        FROM knowledge_chunks kc
        WHERE kc.embedding_status = 'ready'
          AND kc.embedding IS NOT NULL
          AND (target_model IS NULL OR kc.model = target_model OR kc.model IS NULL)
          AND (target_symptom IS NULL OR kc.symptom_category = target_symptom OR kc.symptom_category IS NULL)
    )
    SELECT
        s.chunk_id,
        s.source_type,
        s.source_id,
        s.model,
        s.symptom_category,
        s.text_chunk,
        s.vector_score,
        s.lexical_score,
        CASE
            WHEN (p.wv + p.wl) = 0 THEN 0
            ELSE ((p.wv * s.vector_score) + (p.wl * s.lexical_score)) / (p.wv + p.wl)
        END AS hybrid_score
    FROM scored s
    CROSS JOIN params p
    ORDER BY hybrid_score DESC
    LIMIT GREATEST(limit_count, 1);
$$;

