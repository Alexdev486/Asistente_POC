#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

make db-up
make db-migrate
make db-seed
make db-ingest-chunks
docker exec -i asistente-poc-postgres psql -U postgres -d asistente_poc -c "UPDATE embedding_jobs SET status='pending' WHERE chunk_id IN (SELECT chunk_id FROM knowledge_chunks WHERE embedding_status='pending');"
make embeddings-worker

PYTHONPATH=apps/api pytest apps/api/tests

PYTHONPATH=apps/api uvicorn app.main:app --host 127.0.0.1 --port 18000 >/tmp/asistente_api.log 2>&1 &
API_PID=$!
trap 'kill "$API_PID" >/dev/null 2>&1 || true' EXIT
sleep 4

curl -sf http://127.0.0.1:18000/api/v1/health >/tmp/health.json
START_JSON=$(curl -sf -X POST http://127.0.0.1:18000/api/v1/session/start -H 'Content-Type: application/json' -d '{"metadata":{"source":"qa"}}')
SESSION_ID=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["session_id"])' "$START_JSON")
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/message -H 'Content-Type: application/json' -d '{"session_id":"'"$SESSION_ID"'","message":"AK550-POC-0001"}' >/tmp/msg1.json
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/message -H 'Content-Type: application/json' -d '{"session_id":"'"$SESSION_ID"'","message":"consultas frecuentes"}' >/tmp/msg2.json
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/message -H 'Content-Type: application/json' -d '{"session_id":"'"$SESSION_ID"'","message":"Que significa que no se escuche la bomba de gasolina al dar contacto?"}' >/tmp/msg3.json
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/message -H 'Content-Type: application/json' -d '{"session_id":"'"$SESSION_ID"'","message":"otros"}' >/tmp/msg4.json
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/message -H 'Content-Type: application/json' -d '{"session_id":"'"$SESSION_ID"'","message":"La moto se para en caliente y luego arranca en frio"}' >/tmp/msg5.json
curl -sf http://127.0.0.1:18000/api/v1/session/$SESSION_ID >/tmp/session.json
curl -sf -X POST http://127.0.0.1:18000/api/v1/session/$SESSION_ID/feedback -H 'Content-Type: application/json' -d '{"useful":true,"comment":"QA"}' >/tmp/feedback.json
curl -sf http://127.0.0.1:18000/api/v1/metrics/summary >/tmp/metrics.json

echo "QA_OK session_id=$SESSION_ID"
