CREATE OR REPLACE VIEW v_metrics_summary AS
WITH session_stats AS (
    SELECT
        COUNT(*)::INT AS total_sessions,
        COUNT(*) FILTER (WHERE status = 'completed' OR ended_at IS NOT NULL)::INT AS completed_sessions,
        ROUND(COALESCE(AVG(total_steps), 0), 2)::NUMERIC AS avg_steps_per_session
    FROM sessions
),
module_usage AS (
    SELECT
        COUNT(*) FILTER (WHERE module_name = 'faq_matcher')::INT AS faq_usage,
        COUNT(*) FILTER (WHERE module_name = 'tree_engine')::INT AS tree_usage,
        COUNT(*) FILTER (
            WHERE module_name IN ('free_text_parser', 'historical_retrieval', 'hybrid_ranking')
        )::INT AS other_usage
    FROM decision_logs
),
feedback_stats AS (
    SELECT
        COUNT(*) FILTER (WHERE useful IS TRUE)::INT AS positive_feedback,
        COUNT(*) FILTER (WHERE useful IS FALSE)::INT AS negative_feedback
    FROM feedback
),
result_stats AS (
    SELECT final_result
    FROM sessions
    WHERE final_result IS NOT NULL
    GROUP BY final_result
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
SELECT
    ss.total_sessions,
    ss.completed_sessions,
    ss.avg_steps_per_session,
    mu.faq_usage,
    mu.tree_usage,
    mu.other_usage,
    fs.positive_feedback,
    fs.negative_feedback,
    (SELECT final_result FROM result_stats) AS most_frequent_final_result
FROM session_stats ss
CROSS JOIN module_usage mu
CROSS JOIN feedback_stats fs;

