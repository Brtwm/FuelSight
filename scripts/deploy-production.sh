#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Usage: $0 <40-character git commit SHA>" >&2
  exit 1
fi

ROOT_DIR="${FUELSIGHT_ROOT:-/opt/fuelsight}"
COMPOSE_FILE="$ROOT_DIR/compose/docker-compose.production.yml"
ENV_FILE="$ROOT_DIR/env/production.env"
RELEASE_FILE="$ROOT_DIR/.release"
IMAGE_TAG="$1"
export IMAGE_TAG

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

previous_tag=""
if [[ -f "$RELEASE_FILE" ]]; then
  previous_tag="$(<"$RELEASE_FILE")"
fi

compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

if "${compose[@]}" ps --status running db | grep -q db; then
  "$ROOT_DIR/scripts/backup-production.sh"
fi

"${compose[@]}" pull
"${compose[@]}" up -d db
"${compose[@]}" run --rm backend-migrate
"${compose[@]}" up -d --remove-orphans

healthy=false
for _ in $(seq 1 120); do
  if curl --fail --silent --show-error \
    http://127.0.0.1:3000/api/v1/health >/dev/null \
    && curl --fail --silent --show-error \
      http://127.0.0.1:8080/api/v2/monitor/health >/dev/null; then
    healthy=true
    break
  fi
  sleep 5
done

if [[ "$healthy" != true ]]; then
  echo "Health check failed for $IMAGE_TAG" >&2
  "${compose[@]}" ps >&2
  if [[ "$previous_tag" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Rolling application images back to $previous_tag" >&2
    IMAGE_TAG="$previous_tag"
    export IMAGE_TAG
    "${compose[@]}" pull
    "${compose[@]}" up -d --remove-orphans
  fi
  exit 1
fi

umask 077
printf '%s\n' "$IMAGE_TAG" > "$RELEASE_FILE"
echo "FuelSight deployed: $IMAGE_TAG"
