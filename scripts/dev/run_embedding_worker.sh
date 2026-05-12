#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=apps/api python3 scripts/dev/run_embedding_worker_once.py
