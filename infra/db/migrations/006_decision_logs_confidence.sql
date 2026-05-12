ALTER TABLE decision_logs
ADD COLUMN IF NOT EXISTS confidence NUMERIC(5,4);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_decision_logs_confidence_range'
    ) THEN
        ALTER TABLE decision_logs
        ADD CONSTRAINT ck_decision_logs_confidence_range
        CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1));
    END IF;
END $$;

UPDATE decision_logs
SET confidence = (output_data->>'confidence')::NUMERIC(5,4)
WHERE confidence IS NULL
  AND output_data ? 'confidence'
  AND jsonb_typeof(output_data->'confidence') = 'number'
  AND (output_data->>'confidence')::NUMERIC(10,6) BETWEEN 0 AND 1;
