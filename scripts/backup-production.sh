#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${FUELSIGHT_ROOT:-/opt/fuelsight}"
BACKUP_DIR="${FUELSIGHT_BACKUP_DIR:-$ROOT_DIR/backups}"
COMPOSE_FILE="$ROOT_DIR/compose/docker-compose.production.yml"
ENV_FILE="$ROOT_DIR/env/production.env"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

if [[ -z "${IMAGE_TAG:-}" ]]; then
  if [[ -f "$ROOT_DIR/.release" ]]; then
    IMAGE_TAG="$(<"$ROOT_DIR/.release")"
    export IMAGE_TAG
  else
    echo "Set IMAGE_TAG or create $ROOT_DIR/.release" >&2
    exit 1
  fi
fi

mkdir -p "$BACKUP_DIR"
umask 077

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="$BACKUP_DIR/fuelsight-$timestamp.sql.gz"

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T db \
  sh -c 'pg_dump --clean --if-exists --no-owner -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip -9 > "$backup_path"

test -s "$backup_path"
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'fuelsight-*.sql.gz' \
  -mtime "+$RETENTION_DAYS" -delete

echo "Backup written: $backup_path"
