CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id BIGSERIAL PRIMARY KEY,
    source_type VARCHAR(30) NOT NULL CHECK (source_type IN ('faq', 'historical_case', 'tree_node')),
    source_id VARCHAR(100) NOT NULL,
    model VARCHAR(100),
    symptom_category VARCHAR(100),
    text_chunk TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    lexical tsvector GENERATED ALWAYS AS (
        to_tsvector('spanish', COALESCE(text_chunk, ''))
    ) STORED,
    base_confidence NUMERIC(5,4),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kc_model_symptom ON knowledge_chunks(model, symptom_category);
CREATE INDEX IF NOT EXISTS idx_kc_lexical ON knowledge_chunks USING GIN(lexical);
CREATE INDEX IF NOT EXISTS idx_kc_embedding_hnsw ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding vector(1024),
    query_text TEXT,
    target_model VARCHAR(100),
    target_symptom VARCHAR(100),
    limit_count INTEGER DEFAULT 10
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
    WITH scored AS (
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
        WHERE (target_model IS NULL OR kc.model = target_model)
          AND (target_symptom IS NULL OR kc.symptom_category = target_symptom)
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
        (0.75 * s.vector_score + 0.25 * s.lexical_score) AS hybrid_score
    FROM scored s
    ORDER BY hybrid_score DESC
    LIMIT GREATEST(limit_count, 1);
$$;

