# validate-traceability.md

# Goal

Validate that all critical decisions, transitions and module executions are fully traceable end-to-end.

Every important system decision must be reconstructable.

# Responsibilities

Validate traceability for:

* VIN lookup
* FAQ matching
* tree execution
* free text parsing
* historical retrieval
* hybrid ranking
* response generation
* feedback
* metrics

# Mandatory Checks

## decision_logs Coverage

Validate every critical module generates:

* session_id
* module_name
* input_data
* output_data
* timestamps

Detect:

* missing logs
* partial logs
* inconsistent schemas
* silent failures

## Message Tracking

Validate:

* all user messages persist
* all assistant responses persist
* ordering correctness
* session association correctness

## State Transition Tracking

Validate:

* node changes are logged
* diagnosis selection is logged
* ranking decisions are logged
* FAQ resolution is logged

## Error Traceability

Validate:

* LLM failures are logged
* fallback activation is logged
* invalid inputs are logged
* out-of-scope branches are logged

# Detect

You must detect:

* hidden decisions
* non-traceable flows
* logging gaps
* inconsistent payloads
* duplicated logging logic
* missing context correlation

# Expected Output

For every issue provide:

## Traceability Gap

What is missing.

## Impact

Why debugging or auditing becomes impossible.

## Minimal Fix

Smallest logging improvement possible.

## Suggested Schema

If payload structure needs normalization.

## Suggested Tests

Validation strategy.

# Constraints

DO NOT:

* introduce complex observability platforms
* add unnecessary telemetry systems
* redesign logging architecture

DO:

* keep logs structured
* keep logs deterministic
* prioritize debuggability
* preserve POC simplicity
