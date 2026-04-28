# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\orchestrator.ps1 [args...]
# bash equivalent: bin/orchestrator ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" orchestrator @args
exit $LASTEXITCODE
