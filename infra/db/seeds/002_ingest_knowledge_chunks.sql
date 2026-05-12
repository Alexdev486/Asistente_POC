WITH faq_chunks AS (
    INSERT INTO knowledge_chunks (
        source_type,
        source_id,
        model,
        symptom_category,
        text_chunk,
        base_confidence,
        chunk_index,
        metadata,
        embedding_status
    )
    SELECT
        'faq' AS source_type,
        f.faq_id::text AS source_id,
        f.model,
        f.category AS symptom_category,
        CONCAT('FAQ: ', f.question, E'\nRespuesta: ', f.answer) AS text_chunk,
        NULL::NUMERIC(5,4) AS base_confidence,
        0 AS chunk_index,
        jsonb_build_object(
            'faq_id', f.faq_id,
            'category', f.category,
            'kind', 'faq'
        ) AS metadata,
        'pending' AS embedding_status
    FROM faqs f
    WHERE f.active IS TRUE
    ON CONFLICT (source_type, source_id, chunk_index, embedding_model)
    DO UPDATE SET
        model = EXCLUDED.model,
        symptom_category = EXCLUDED.symptom_category,
        text_chunk = EXCLUDED.text_chunk,
        base_confidence = EXCLUDED.base_confidence,
        metadata = EXCLUDED.metadata,
        embedding_status = 'pending',
        embedding = NULL
    RETURNING chunk_id
),
historical_case_chunks AS (
    INSERT INTO knowledge_chunks (
        source_type,
        source_id,
        model,
        symptom_category,
        text_chunk,
        base_confidence,
        chunk_index,
        metadata,
        embedding_status
    )
    SELECT
        'historical_case' AS source_type,
        hc.case_id AS source_id,
        hc.model,
        hc.symptom_category,
        CONCAT('Caso: ', hc.case_text, E'\nDiagnostico final: ', hc.final_diagnosis) AS text_chunk,
        hc.base_confidence,
        0 AS chunk_index,
        jsonb_build_object(
            'case_id', hc.case_id,
            'kind', 'historical_case'
        ) AS metadata,
        'pending' AS embedding_status
    FROM historical_cases hc
    ON CONFLICT (source_type, source_id, chunk_index, embedding_model)
    DO UPDATE SET
        model = EXCLUDED.model,
        symptom_category = EXCLUDED.symptom_category,
        text_chunk = EXCLUDED.text_chunk,
        base_confidence = EXCLUDED.base_confidence,
        metadata = EXCLUDED.metadata,
        embedding_status = 'pending',
        embedding = NULL
    RETURNING chunk_id
),
tree_nodes AS (
    SELECT
        dt.tree_id,
        dt.model,
        dt.symptom,
        node.key AS node_id,
        node.value AS node_json,
        ROW_NUMBER() OVER (PARTITION BY dt.tree_id ORDER BY node.key) - 1 AS chunk_index
    FROM diagnostic_trees dt
    CROSS JOIN LATERAL jsonb_each(dt.tree_json -> 'nodes') AS node(key, value)
    WHERE dt.active IS TRUE
),
tree_chunks AS (
    INSERT INTO knowledge_chunks (
        source_type,
        source_id,
        model,
        symptom_category,
        text_chunk,
        base_confidence,
        chunk_index,
        metadata,
        embedding_status
    )
    SELECT
        'tree_node' AS source_type,
        tn.tree_id AS source_id,
        tn.model,
        tn.symptom AS symptom_category,
        CASE
            WHEN tn.node_json ->> 'type' = 'question'
                THEN CONCAT('Arbol ', tn.tree_id, ' [', tn.node_id, ']: ', COALESCE(tn.node_json ->> 'text', ''))
            ELSE CONCAT('Arbol ', tn.tree_id, ' [', tn.node_id, ']: ', COALESCE(tn.node_json ->> 'result', ''))
        END AS text_chunk,
        NULL::NUMERIC(5,4) AS base_confidence,
        tn.chunk_index,
        jsonb_build_object(
            'tree_id', tn.tree_id,
            'node_id', tn.node_id,
            'node_type', tn.node_json ->> 'type',
            'kind', 'tree_node'
        ) AS metadata,
        'pending' AS embedding_status
    FROM tree_nodes tn
    ON CONFLICT (source_type, source_id, chunk_index, embedding_model)
    DO UPDATE SET
        model = EXCLUDED.model,
        symptom_category = EXCLUDED.symptom_category,
        text_chunk = EXCLUDED.text_chunk,
        base_confidence = EXCLUDED.base_confidence,
        metadata = EXCLUDED.metadata,
        embedding_status = 'pending',
        embedding = NULL
    RETURNING chunk_id
)
SELECT
    (SELECT COUNT(*) FROM faq_chunks) AS faq_chunks_upserted,
    (SELECT COUNT(*) FROM historical_case_chunks) AS historical_case_chunks_upserted,
    (SELECT COUNT(*) FROM tree_chunks) AS tree_chunks_upserted;
