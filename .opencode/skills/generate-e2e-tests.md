# generate-e2e-tests.md

# Goal

Generate robust end-to-end tests for the conversational diagnostic system.

Tests must validate:

* DDT compliance
* conversation stability
* state consistency
* traceability
* user experience continuity

# Responsibilities

Generate:

* pytest E2E backend tests
* Playwright conversational frontend tests
* fixtures
* mocks
* regression scenarios

# Mandatory Flows

## VIN Identification Flow

Validate:

* valid VIN
* invalid VIN
* missing VIN
* malformed VIN
* blocked progression without VIN

## Main Menu Flow

Validate:

* symptom menu
* FAQ menu
* Otros menu
* invalid selection handling

## Diagnostic Tree Flow

Validate:

* complete Paradas de motor flow
* CELP flow
* deterministic transitions
* final diagnosis contract

## FAQ Flow

Validate:

* FAQ matching
* model-aware FAQs
* fallback behavior
* no-match behavior

## Otros Flow

Validate:

* free text parsing
* historical retrieval
* ranking generation
* top-3 hypotheses
* uncertainty handling

## Error Handling

Validate:

* LLM temporary failures
* invalid answers
* interrupted sessions
* unsupported branches
* malformed payloads

# Required Assertions

Always validate:

* session_state consistency
* messages persistence
* decision_logs creation
* response contract correctness
* no duplicated questions
* stable conversation continuity

# Test Quality Rules

Tests must:

* be deterministic
* avoid brittle selectors
* avoid implementation coupling
* prioritize business behavior
* maximize regression detection

# Output Format

For every generated test include:

* scenario description
* setup
* execution
* assertions
* cleanup if needed

# Constraints

DO NOT:

* generate flaky tests
* depend on timing hacks
* hardcode unstable UI assumptions

DO:

* prioritize reliability
* maximize DDT coverage
* reuse fixtures
* isolate scenarios
