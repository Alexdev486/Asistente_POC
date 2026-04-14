CREATE INDEX IF NOT EXISTS idx_sessions_vin ON sessions(vin);
CREATE INDEX IF NOT EXISTS idx_sessions_model ON sessions(model);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_decision_logs_session_id ON decision_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_session_state_model ON session_state(model);
CREATE INDEX IF NOT EXISTS idx_historical_cases_model ON historical_cases(model);
CREATE INDEX IF NOT EXISTS idx_historical_cases_symptom_category ON historical_cases(symptom_category);
CREATE INDEX IF NOT EXISTS idx_faqs_model ON faqs(model);
CREATE INDEX IF NOT EXISTS idx_faqs_category ON faqs(category);

