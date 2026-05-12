#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL no esta definida"
  exit 1
fi

echo "Ingestando knowledge_chunks..."
if command -v psql >/dev/null 2>&1 && psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "infra/db/seeds/002_ingest_knowledge_chunks.sql"; then
  :
else
  if ! command -v docker >/dev/null 2>&1; then
    echo "No hay psql ni docker disponible para ejecutar la ingesta."
    exit 1
  fi
  if ! docker ps --format '{{.Names}}' | grep -q '^asistente-poc-postgres$'; then
    echo "No se encontro el contenedor asistente-poc-postgres en ejecucion."
    exit 1
  fi
  docker exec -i asistente-poc-postgres psql -U postgres -d asistente_poc -v ON_ERROR_STOP=1 -f - < "infra/db/seeds/002_ingest_knowledge_chunks.sql"
fi
echo "Ingestion completada."
