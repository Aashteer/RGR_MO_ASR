# Сборка exe (PyInstaller) — Windows
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:PIP_CACHE_DIR = Join-Path $ProjectRoot ".pip-cache"
$env:TEMP = Join-Path $ProjectRoot "temp"
$env:TMP = $env:TEMP

$py = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Создайте venv: python -m venv venv" -ForegroundColor Red
    exit 1
}

Write-Host "=== Установка PyInstaller ===" -ForegroundColor Cyan
& $py -m pip install pyinstaller --quiet

Write-Host "=== Сборка exe (5-15 мин, ~2 ГБ) ===" -ForegroundColor Cyan
& $py -m PyInstaller transcribe.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$dist = Join-Path $ProjectRoot "dist\Transcription"
$modelsSrc = Join-Path $ProjectRoot "models"
$modelsDst = Join-Path $dist "models"

if (Test-Path $modelsSrc) {
    Write-Host "=== Копирование models/ рядом с exe ===" -ForegroundColor Cyan
    if (Test-Path $modelsDst) { Remove-Item $modelsDst -Recurse -Force }
    Copy-Item $modelsSrc $modelsDst -Recurse
}

Write-Host ""
Write-Host "Готово!" -ForegroundColor Green
Write-Host "  Запуск: $dist\Transcription.exe"
Write-Host "  Папка:  $dist"
Write-Host ""
Write-Host "Первый запуск может быть медленным. Модели Whisper/Qwen — в dist\Transcription\models\"
