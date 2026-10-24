$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $projectRoot

$writableDirectories = @(
    "data",
    "airflow/logs",
    "airflow/config",
    "airflow/plugins",
    "data_platform_analytics/logs",
    "data_platform_analytics/target"
)

foreach ($directory in $writableDirectories) {
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

docker compose up --build --wait @args
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose startup failed with exit code $LASTEXITCODE"
}

Write-Host "Data platform is ready: http://localhost:8080"
