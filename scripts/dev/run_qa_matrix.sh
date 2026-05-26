#!/usr/bin/env bash
set -euo pipefail

# QA Matrix - End-to-End Test Cases for Asistente POC
# This script validates consistent behavior across all conversation paths

API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api}"
VERBOSE="${VERBOSE:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed_tests=0
failed_tests=0

log_test() {
  if [[ "$VERBOSE" == "true" ]]; then
    echo -e "${YELLOW}[TEST]${NC} $1"
  fi
}

pass_test() {
  ((passed_tests++))
  echo -e "${GREEN}✓ PASS${NC} $1"
}

fail_test() {
  ((failed_tests++))
  echo -e "${RED}✗ FAIL${NC} $1"
}

# Test case helper: sends a message and checks response
test_flow() {
  local test_name=$1
  local session_id=$2
  local user_message=$3
  local expected_in_response=$4
  
  log_test "Sending: '$user_message'"
  
  response=$(curl -s -X POST "${API_BASE_URL}/sessions/${session_id}/messages" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$user_message\"}")
  
  if echo "$response" | grep -q "$expected_in_response"; then
    pass_test "$test_name"
  else
    fail_test "$test_name - Response: $response"
  fi
}

echo "========================================="
echo "QA Matrix - E2E Test Suite"
echo "========================================="

# Test 1: VIN Lookup (positive case)
echo ""
echo "=== Group 1: VIN Lookup ==="
SESSION_ID=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')
echo "Created session: $SESSION_ID"

test_flow "VIN lookup - Valid AK550" "$SESSION_ID" "AK550-POC-0001" "He identificado"

# Test 2: Menu selection - Tree path (positive)
echo ""
echo "=== Group 2: Tree Engine (Sintomas Frecuentes) ==="
test_flow "Menu - Tree selection" "$SESSION_ID" "Sintomas frecuentes" "Vamos por Sintomas"

test_flow "Tree - Select symptom (Paradas de motor)" "$SESSION_ID" "Paradas de motor" "Cuando se para"

test_flow "Tree - Answer question (si)" "$SESSION_ID" "si" "Mal contacto"

# Test 3: New session for FAQ path
echo ""
echo "=== Group 3: FAQ Matcher (Consultas Frecuentes) ==="
SESSION_ID2=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup for FAQ session" "$SESSION_ID2" "XCITING-POC-0001" "Xciting 400"

test_flow "Menu - FAQ selection" "$SESSION_ID2" "Consultas frecuentes" "Vamos por Consultas"

test_flow "FAQ - Known question (CELP)" "$SESSION_ID2" "Que significa el testigo CELP encendido?" "testigo CELP"

# Test 4: New session for Otros (free text) path - NEGATIVE CASE
echo ""
echo "=== Group 4: Otros - Free Text (Negative Cases) ==="
SESSION_ID3=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup for Others session" "$SESSION_ID3" "AK550-POC-0001" "He identificado"

test_flow "Menu - Otros selection" "$SESSION_ID3" "Otros" "Describe el problema"

# These should return "weak_evidence" or "no_candidates" responses (guardrails)
test_flow "Otros - Unrelated symptom (aceite)" "$SESSION_ID3" "sale aceite del motor" "No tengo suficientes|No pude clasificar"

test_flow "Otros - Unrelated symptom (frena)" "$SESSION_ID3" "frena sola la moto" "No tengo suficientes|No pude clasificar"

test_flow "Otros - Unrelated symptom (ruido lata)" "$SESSION_ID3" "suena a lata el escape" "No tengo suficientes|No pude clasificar"

# Test 5: New session for Otros (free text) path - POSITIVE CASE
echo ""
echo "=== Group 5: Otros - Free Text (Positive Cases) ==="
SESSION_ID4=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup for Otros positive" "$SESSION_ID4" "AK550-POC-0002" "He identificado"

test_flow "Menu - Otros" "$SESSION_ID4" "Otros" "Describe el problema"

# These are known symptoms that should return hypotheses
test_flow "Otros - Known symptom (frio)" "$SESSION_ID4" "Se apaga al arrancar en frio" "Hipotesis principal"

# Test 6: Xciting specific cases
echo ""
echo "=== Group 6: Xciting-specific Cases ==="
SESSION_ID5=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup Xciting" "$SESSION_ID5" "XCITING-POC-0001" "Xciting"

test_flow "Menu - Otros" "$SESSION_ID5" "Otros" "Describe"

test_flow "Xciting - Specific case (humo negro)" "$SESSION_ID5" "sale humo negro del escape" "Hipotesis|No tengo"

# Test 7: Menu command normalization (typos and variations)
echo ""
echo "=== Group 7: Menu Command Normalization ==="
SESSION_ID6=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup" "$SESSION_ID6" "AK550-POC-0001" "He identificado"

# Test various menu command variations
test_flow "Menu - Typo (sintomas)" "$SESSION_ID6" "sintomas" "Vamos"

test_flow "Back to menu - Otros" "$SESSION_ID6" "otros" "Describe"

# Test 8: Entry point reset when switching paths
echo ""
echo "=== Group 8: Entry Point Reset ==="
SESSION_ID7=$(curl -s -X POST "${API_BASE_URL}/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.session_id')

test_flow "VIN lookup" "$SESSION_ID7" "XCITING-POC-0001" "Xciting"

test_flow "Start Tree" "$SESSION_ID7" "Sintomas" "Vamos por Sintomas"

test_flow "Switch to FAQ mid-tree" "$SESSION_ID7" "Consultas frecuentes" "Vamos por Consultas"

# Summary
echo ""
echo "========================================="
echo "Test Results:"
echo -e "  ${GREEN}Passed: $passed_tests${NC}"
echo -e "  ${RED}Failed: $failed_tests${NC}"
echo "========================================="

if [[ $failed_tests -gt 0 ]]; then
  exit 1
fi
