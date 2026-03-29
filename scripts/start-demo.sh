#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="compose/docker-compose.yml"

echo "Starting FuelSight core stack (db, backend, frontend)..."
docker compose -f "$COMPOSE_FILE" --profile core up -d

if [[ "${1:-}" == "--with-airflow" ]]; then
  echo "Starting Airflow profile..."
  docker compose -f "$COMPOSE_FILE" --profile airflow up -d
fi

echo "Done. Use 'docker compose -f compose/docker-compose.yml ps' to inspect status."
