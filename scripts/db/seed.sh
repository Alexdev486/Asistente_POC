#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL no esta definida"
  exit 1
fi

execute_sql() {
  local file="$1"
  if command -v psql >/dev/null 2>&1 && psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${file}"; then
    return 0
  fi
  if ! command -v docker >/dev/null 2>&1; then
    echo "No hay psql ni docker disponible para ejecutar seed."
    return 1
  fi
  if ! docker ps --format '{{.Names}}' | grep -q '^asistente-poc-postgres$'; then
    echo "No se encontro el contenedor asistente-poc-postgres en ejecucion."
    return 1
  fi
  docker exec -i asistente-poc-postgres psql -U postgres -d asistente_poc -v ON_ERROR_STOP=1 -f - < "${file}"
}

echo "Cargando seed mock..."
execute_sql "infra/db/seeds/001_seed_mock.sql"

if [[ -f "infra/db/seeds/003_expand_seed_data.sql" ]]; then
  echo "Cargando seed expandido..."
  execute_sql "infra/db/seeds/003_expand_seed_data.sql"
fi

if [[ -f "infra/db/seeds/004_seed_more_data.sql" ]]; then
  echo "Cargando seed adicional..."
  execute_sql "infra/db/seeds/004_seed_more_data.sql"
fi

echo "Seed completado."
