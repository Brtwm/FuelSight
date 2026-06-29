param(
    [string]$SourceEnv = ".env",
    [string]$Template = "compose/env/production.env.example",
    [string]$Output = "env/production.env"
)

$ErrorActionPreference = "Stop"

function New-HexSecret([int]$Bytes) {
    return [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes($Bytes)).ToLowerInvariant()
}

function New-FernetKey {
    $base64 = [Convert]::ToBase64String(
        [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
    )
    return $base64.Replace("+", "-").Replace("/", "_")
}

function Read-DotEnv([string]$Path) {
    $result = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
            $result[$Matches[1]] = $Matches[2]
        }
    }
    return $result
}

if (-not (Test-Path -LiteralPath $SourceEnv)) {
    throw "Source env not found: $SourceEnv"
}
if (-not (Test-Path -LiteralPath $Template)) {
    throw "Production template not found: $Template"
}

$localValues = Read-DotEnv $SourceEnv
foreach ($requiredKey in @("LLM_API_KEY", "LLM_OPENAI_COMPAT_BASE_URL")) {
    if ([string]::IsNullOrWhiteSpace($localValues[$requiredKey])) {
        throw "$requiredKey is missing in $SourceEnv"
    }
}

$databasePassword = New-HexSecret 24
$productionValues = @{
    "POSTGRES_PASSWORD" = $databasePassword
    "DATABASE_URL" = "postgresql+psycopg://fuelsight:${databasePassword}@db:5432/fuelsight"
    "JWT_SECRET_KEY" = New-HexSecret 32
    "AIRFLOW__CORE__FERNET_KEY" = New-FernetKey
    "AIRFLOW__CORE__AUTH_MANAGER" = "airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"
    "AIRFLOW__CORE__EXECUTION_API_SERVER_URL" = "http://airflow-webserver:8080/execution/"
    "AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK" = "True"
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" = "postgresql+psycopg2://fuelsight:${databasePassword}@db:5432/airflow"
    "AIRFLOW__API_AUTH__JWT_SECRET" = New-HexSecret 32
    "AIRFLOW__API__SECRET_KEY" = New-HexSecret 32
    "AIRFLOW__API__PORT" = "8080"
    "_AIRFLOW_WWW_USER_PASSWORD" = New-HexSecret 16
}

$copyWithoutChanges = @(
    "LLM_OPENAI_COMPAT_BASE_URL",
    "LLM_API_KEY",
    "LLM_CHAT_MODEL",
    "LLM_EMBEDDING_MODEL",
    "LLM_RERANKER_MODEL",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_EVIDENCE_CHARS",
    "LLM_EMBEDDING_DIMENSIONS",
    "GIGACHAT_AUTH_KEY",
    "GIGACHAT_SCOPE",
    "GIGACHAT_BASE_URL",
    "GIGACHAT_AUTH_URL",
    "GIGACHAT_CHAT_MODEL",
    "GIGACHAT_EMBEDDING_MODEL",
    "NEWS_PROVIDER"
)
foreach ($key in $copyWithoutChanges) {
    if ($localValues.ContainsKey($key)) {
        $productionValues[$key] = $localValues[$key]
    }
}

$outputLines = foreach ($line in Get-Content -LiteralPath $Template) {
    if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$' -and $productionValues.ContainsKey($Matches[1])) {
        "$($Matches[1])=$($productionValues[$Matches[1]])"
    } else {
        $line
    }
}

$outputDirectory = Split-Path -Parent $Output
if ($outputDirectory) {
    New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}
$outputLines | Set-Content -LiteralPath $Output -Encoding utf8NoBOM

Write-Host "Created $Output without modifying $SourceEnv."
Write-Host "Do not commit or print the generated file. Copy it directly to the VPS."
