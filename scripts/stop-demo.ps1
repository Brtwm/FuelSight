$ErrorActionPreference = 'Stop'
$composeFile = 'compose/docker-compose.yml'

Write-Host 'Stopping FuelSight core and airflow profiles...'
docker compose -f $composeFile --profile core --profile airflow down
Write-Host 'Done.'
