#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="compose/docker-compose.yml"

echo "Stopping FuelSight core and airflow profiles..."
docker compose -f "$COMPOSE_FILE" --profile core --profile airflow down
echo "Done."
