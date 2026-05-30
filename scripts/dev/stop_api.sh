#!/usr/bin/env bash
# stop_api.sh — Detiene el backend FastAPI (puerto 8000).
set -euo pipefail

PORT="${1:-8000}"

PIDS=$(ss -tlnpH "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u || true)

if [ -n "$PIDS" ]; then
  for PID in $PIDS; do
    echo "Deteniendo backend en puerto $PORT (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
  done
  # Esperar hasta 5 segundos a que terminen
  for i in $(seq 1 5); do
    REMAINING=""
    for PID in $PIDS; do
      if kill -0 "$PID" 2>/dev/null; then
        REMAINING="$REMAINING $PID"
      fi
    done
    if [ -z "$REMAINING" ]; then
      echo "Backend detenido."
      exit 0
    fi
    sleep 1
  done
  # Forzar los que queden
  for PID in $PIDS; do
    if kill -0 "$PID" 2>/dev/null; then
      echo "Forzando cierre del backend (PID: $PID)..."
      kill -9 "$PID" 2>/dev/null || true
    fi
  done
  echo "Backend detenido (forzado)."
else
  echo "No se encontro proceso en el puerto $PORT."
fi
