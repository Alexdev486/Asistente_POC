#!/usr/bin/env bash
# stop_web.sh — Detiene el frontend Next.js (puerto 3000 por defecto).
set -euo pipefail

PORT="${1:-3000}"

PIDS=$(ss -tlnpH "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u || true)

if [ -n "$PIDS" ]; then
  for PID in $PIDS; do
    echo "Deteniendo frontend en puerto $PORT (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
  done
  for i in $(seq 1 5); do
    REMAINING=""
    for PID in $PIDS; do
      if kill -0 "$PID" 2>/dev/null; then
        REMAINING="$REMAINING $PID"
      fi
    done
    if [ -z "$REMAINING" ]; then
      echo "Frontend detenido."
      exit 0
    fi
    sleep 1
  done
  for PID in $PIDS; do
    if kill -0 "$PID" 2>/dev/null; then
      echo "Forzando cierre del frontend (PID: $PID)..."
      kill -9 "$PID" 2>/dev/null || true
    fi
  done
  echo "Frontend detenido (forzado)."
else
  echo "No se encontro proceso en el puerto $PORT."
fi
