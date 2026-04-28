# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\coach.ps1 [args...]
# bash equivalent: bin/coach ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" coach @args
exit $LASTEXITCODE
