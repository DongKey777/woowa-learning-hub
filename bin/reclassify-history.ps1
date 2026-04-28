# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\reclassify-history.ps1 [--dry-run]
# bash equivalent: bin/reclassify-history ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" reclassify-history @args
exit $LASTEXITCODE
