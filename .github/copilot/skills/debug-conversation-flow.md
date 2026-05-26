# debug-conversation-flow.md

# Goal

Debug conversational inconsistencies, broken flows and unstable dialogue behavior across the hybrid diagnostic system.

The system is NOT a generic chatbot.
The flow must remain deterministic and controlled.

# Responsibilities

Analyze:

* orchestration flow
* LangGraph transitions
* menu routing
* tree progression
* FAQ routing
* Otros routing
* fallback handling
* response continuity

# Mandatory Checks

## Conversation Routing

Validate:

* correct routing after VIN identification
* symptom flow prioritization
* FAQ prioritization
* free text routing correctness

## Tree Engine

Validate:

* node transitions
* invalid answer handling
* repeated question prevention
* final diagnosis stability

## Free Text Flow

Validate:

* normalization
* tag extraction
* historical retrieval
* ranking coherence
* reconduction to structured flows

## Context Continuity

Validate:

* conversation memory coherence
* no forgotten facts
* no contradictory assistant responses
* no context resets

## Failure Modes

Validate:

* LLM failure fallback
* malformed responses
* unsupported intents
* ambiguous answers
* out-of-scope branches

# Detect

You must detect:

* dead branches
* unreachable states
* infinite loops
* contradictory responses
* duplicated routing logic
* unstable transitions
* hidden assumptions
* state corruption

# Expected Output

For every detected issue provide:

## Flow Area

Affected conversation area.

## Reproduction Steps

Exact conversation to reproduce.

## Root Cause

Technical explanation.

## Risk

Impact on UX or diagnosis stability.

## Minimal Fix

Simplest reliable correction.

## Regression Risk

What could break after fix.

## Suggested Tests

How to validate correction.

# Constraints

DO NOT:

* transform system into open chatbot
* bypass structured flows
* introduce non-deterministic routing
* replace explicit orchestration with pure prompting

DO:

* preserve guided diagnosis
* preserve deterministic flows
* preserve state-driven orchestration
* prefer explicit logic over hidden LLM behavior
