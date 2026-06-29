#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="${FUELSIGHT_ROOT:-/opt/fuelsight}"
COMPOSE_FILE="$ROOT_DIR/compose/docker-compose.production.yml"
ENV_FILE="$ROOT_DIR/env/production.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

if [[ -z "${IMAGE_TAG:-}" ]]; then
  if [[ -f "$ROOT_DIR/.release" ]]; then
    IMAGE_TAG="$(<"$ROOT_DIR/.release")"
    export IMAGE_TAG
  else
    echo "Set IMAGE_TAG to a deployed commit SHA" >&2
    exit 1
  fi
fi

compose=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

"${compose[@]}" run --rm backend-migrate
"${compose[@]}" run --rm backend fuelsight-seed-core
"${compose[@]}" run --rm backend \
  fuelsight-pipeline generate-demo-data --replace-existing
"${compose[@]}" run --rm backend \
  fuelsight-pipeline ingest-external-indicators-daily --provider live --lookback-days 365
"${compose[@]}" run --rm backend \
  fuelsight-pipeline build-feature-store-daily
"${compose[@]}" run --rm backend \
  fuelsight-pipeline train-models-weekly --window-type rolling
"${compose[@]}" run --rm backend \
  fuelsight-pipeline refresh-news-daily --provider live --lookback-days 30
"${compose[@]}" run --rm backend \
  fuelsight-pipeline refresh-rag-index-daily

echo "Production data, model, news, and RAG bootstrap completed."
echo "Create analyst and director reviewers with fuelsight-create-reviewer as documented."
