# validate-session-state.md

# Goal

Validate consistency, persistence and synchronization of session_state across the entire conversational flow.

The session_state is the source of truth.

# Responsibilities

Validate:

* session persistence
* state transitions
* node progression
* symptom progression
* facts persistence
* hypotheses persistence
* asked_questions consistency
* frontend/backend synchronization

# Mandatory Checks

## Session Initialization

Validate:

* session creation
* session_id generation
* VIN persistence
* model persistence
* initial state correctness

## Tree Navigation

Validate:

* current_node updates correctly
* node transitions are deterministic
* answered questions are persisted
* repeated questions are avoided
* diagnosis nodes close correctly

## FAQ Flow

Validate:

* FAQ interactions do not corrupt session state
* entry_point remains consistent
* model context remains fixed

## Free Text / Otros Flow

Validate:

* extracted tags are persisted
* hypotheses are persisted
* ranking results are associated with session
* context survives multiple turns

## Recovery & Continuity

Validate:

* session reload correctness
* state reconstruction
* stale state handling
* interrupted flow recovery

# Detect

You must detect:

* state desynchronization
* orphan states
* missing persistence
* race conditions
* overwritten state
* duplicated state logic
* frontend/backend inconsistencies

# Expected Output

For each issue provide:

## State Area

Affected part of state.

## Failure Scenario

Exact reproduction scenario.

## Root Cause

Technical explanation.

## Risk

Conversation inconsistency impact.

## Minimal Fix

Simplest stable correction.

## Suggested Tests

Unit/integration/E2E validation.

# Constraints

DO NOT:

* move state into LLM memory
* redesign orchestration unnecessarily
* introduce distributed state systems

DO:

* keep state explicit
* keep state deterministic
* preserve LangGraph orchestration
* prefer simple persistence logic
