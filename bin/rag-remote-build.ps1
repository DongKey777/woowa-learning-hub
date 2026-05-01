# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\rag-remote-build.ps1 --r-phase r1 [--dry-run] [runpod args...]
# bash equivalent: bin/rag-remote-build ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$PY = Join-Path $ROOT ".venv\Scripts\python.exe"
if (-not (Test-Path $PY)) {
    $PY = "python"
}
Push-Location $ROOT
try {
    & $PY -m scripts.remote.runpod_rag_full_build @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
