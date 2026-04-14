#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL no esta definida"
  exit 1
fi

echo "Cargando seed mock..."
psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "infra/db/seeds/001_seed_mock.sql"
echo "Seed completado."

