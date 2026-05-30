# audit-ddt-compliance.md

# Goal

Audit the current implementation against the DDT requirements and detect:

* missing requirements
* partial implementations
* inconsistent behavior
* architecture deviations
* broken acceptance criteria

The DDT is the source of truth.

# Responsibilities

You must validate compliance for:

* Functional requirements (RF)
* Non-functional requirements (RNF)
* Business rules
* Session state rules
* Traceability rules
* API contracts
* Acceptance criteria
* Error handling
* POC architectural constraints

# Mandatory Checks

## Functional Requirements

Validate:

* RF-001 through RF-020

For each requirement:

* identify implementation status
* identify affected files
* identify gaps
* identify hidden edge cases

## Non Functional Requirements

Validate:

* modularity
* maintainability
* state persistence
* resilience
* reasonable response time
* traceability
* controlled failures

## Acceptance Criteria

Validate:

* CA-001 through CA-010

Check if criteria are:

* fully implemented
* partially implemented
* untested
* broken

## Architectural Constraints

Validate:

* monolith modular architecture
* session_state as source of truth
* LLM not used as memory
* mandatory VIN flow
* model persistence during session
* controlled out-of-scope handling

# Expected Output

For every issue provide:

## Requirement

Reference to RF/RNF/CA/RN-NEG.

## Current Status

Implemented / Partial / Missing / Broken.

## Problem

Precise explanation.

## Risk

Impact on POC stability or DDT compliance.

## Minimal Fix

Smallest safe correction possible.

## Affected Files

List impacted modules/files.

# Constraints

DO NOT:

* redesign architecture
* introduce unnecessary abstractions
* suggest enterprise patterns
* rewrite working modules

DO:

* prioritize incremental fixes
* preserve current architecture
* preserve current business logic
* optimize for POC stability
