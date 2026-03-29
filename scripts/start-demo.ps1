param(
  [switch]$WithAirflow
)

$ErrorActionPreference = 'Stop'
$composeFile = 'compose/docker-compose.yml'

Write-Host 'Starting FuelSight core stack (db, backend, frontend)...'
docker compose -f $composeFile --profile core up -d

if ($WithAirflow) {
  Write-Host 'Starting Airflow profile...'
  docker compose -f $composeFile --profile airflow up -d
}

Write-Host 'Done. Use `docker compose -f compose/docker-compose.yml ps` to inspect status.'
