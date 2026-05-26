#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL no esta definida"
  exit 1
fi

echo "Cargando seed mock..."
if command -v psql >/dev/null 2>&1; then
  psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "infra/db/seeds/001_seed_mock.sql"
  if [[ -f "infra/db/seeds/003_expand_seed_data.sql" ]]; then
    echo "Cargando seed expandido..."
    psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "infra/db/seeds/003_expand_seed_data.sql"
  fi
else
  if ! command -v docker >/dev/null 2>&1; then
    echo "No hay psql ni docker disponible para ejecutar seed."
    exit 1
  fi
  if ! docker ps --format '{{.Names}}' | grep -q '^asistente-poc-postgres$'; then
    echo "No se encontro el contenedor asistente-poc-postgres en ejecucion."
    exit 1
  fi
  docker exec -i asistente-poc-postgres psql -U postgres -d asistente_poc -v ON_ERROR_STOP=1 -f - < "infra/db/seeds/001_seed_mock.sql"
  if [[ -f "infra/db/seeds/003_expand_seed_data.sql" ]]; then
    echo "Cargando seed expandido..."
    docker exec -i asistente-poc-postgres psql -U postgres -d asistente_poc -v ON_ERROR_STOP=1 -f - < "infra/db/seeds/003_expand_seed_data.sql"
  fi
fi
echo "Seed completado."
