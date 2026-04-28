# PowerShell wrapper — native Windows 사용자용
# Usage: .\bin\next-action.ps1 [args...]
# bash equivalent: bin/next-action ...
$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
& python "$ROOT\scripts\workbench\cli.py" next-action @args
exit $LASTEXITCODE
