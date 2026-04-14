CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS vehicles (
    vin VARCHAR(50) PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    family VARCHAR(100),
    displacement_cc INTEGER,
    market VARCHAR(20),
    model_year INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS faqs (
    faq_id BIGSERIAL PRIMARY KEY,
    model VARCHAR(100),
    category VARCHAR(100),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diagnostic_trees (
    tree_id VARCHAR(100) PRIMARY KEY,
    model VARCHAR(100),
    symptom VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    tree_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historical_cases (
    case_id VARCHAR(50) PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    symptom_category VARCHAR(100),
    case_text TEXT NOT NULL,
    final_diagnosis VARCHAR(255) NOT NULL,
    base_confidence NUMERIC(5,4) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin VARCHAR(50),
    model VARCHAR(100),
    entry_point VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_steps INTEGER NOT NULL DEFAULT 0,
    final_result VARCHAR(255),
    success BOOLEAN,
    FOREIGN KEY (vin) REFERENCES vehicles(vin)
);

CREATE TABLE IF NOT EXISTS session_state (
    session_id UUID PRIMARY KEY,
    vin VARCHAR(50),
    model VARCHAR(100),
    current_symptom VARCHAR(100),
    current_node VARCHAR(100),
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (vin) REFERENCES vehicles(vin)
);

CREATE TABLE IF NOT EXISTS messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS decision_logs (
    log_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE,
    useful BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

DROP TRIGGER IF EXISTS trg_faqs_set_updated_at ON faqs;
CREATE TRIGGER trg_faqs_set_updated_at
BEFORE UPDATE ON faqs
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_diagnostic_trees_set_updated_at ON diagnostic_trees;
CREATE TRIGGER trg_diagnostic_trees_set_updated_at
BEFORE UPDATE ON diagnostic_trees
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_session_state_set_updated_at ON session_state;
CREATE TRIGGER trg_session_state_set_updated_at
BEFORE UPDATE ON session_state
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

