# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\sync-prs.ps1 [args...]
# bash equivalent: bin/sync-prs ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" sync-prs @args
exit $LASTEXITCODE
