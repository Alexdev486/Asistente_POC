#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL no esta definida"
  exit 1
fi

for file in infra/db/migrations/*.sql; do
  echo "Aplicando migration: ${file}"
  psql "${DATABASE_URL}" -v ON_ERROR_STOP=1 -f "${file}"
done

echo "Migraciones aplicadas correctamente."

