# Install dependencies on Windows (pip cache on H: drive, not C:)
$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:PIP_CACHE_DIR = Join-Path $ProjectRoot ".pip-cache"
$env:TEMP = Join-Path $ProjectRoot "temp"
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR, $env:TEMP | Out-Null

Write-Host "=== Purge pip cache on C: ===" -ForegroundColor Yellow
python -m pip cache purge

if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "=== Create venv ===" -ForegroundColor Cyan
    python -m venv venv
}

$py = ".\venv\Scripts\python.exe"
$pip = ".\venv\Scripts\pip.exe"

Write-Host "=== Upgrade pip ===" -ForegroundColor Cyan
& $py -m pip install --upgrade pip --no-cache-dir

Write-Host "=== Install core packages ===" -ForegroundColor Cyan
& $pip install -r requirements-core.txt --no-cache-dir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "=== Install llama-cpp-python (prebuilt wheel) ===" -ForegroundColor Cyan
& $pip install llama-cpp-python --prefer-binary --no-cache-dir
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Run: .\venv\Scripts\python.exe main.py" -ForegroundColor Green
Write-Host "HF token: `$env:HF_TOKEN = 'hf_YOUR_TOKEN'" -ForegroundColor Yellow
Write-Host "Download models: .\venv\Scripts\python.exe scripts\download_models.py --whisper --model medium" -ForegroundColor Yellow
